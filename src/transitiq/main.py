"""TransitIQ — Interactive CLI for shipment exception management."""

import asyncio
import sys

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from transitiq.database.db import get_database_uri, initialize_ticket_schema
from transitiq.database.repositories import ticket_repository
from transitiq.models import TicketCreate
from transitiq.services.ticket_service import TicketService
from transitiq.workflow.agent import create_transit_agent
from transitiq.workflow.config import shipment_thread_config

if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception:
        pass


# ── Helpers ──────────────────────────────────────────────────────────

def print_banner():
    print("\n" + "=" * 44)
    print("            TransitIQ CLI")
    print("=" * 44)
    print("  1)  Add new issue")
    print("  2)  Run agent on an issue")
    print("  3)  View / update current issues")
    print("  4)  Exit")
    print("=" * 44)


def print_report(state: dict) -> None:
    """Pretty-print a case report from agent state."""
    sid = state.get("shipment_id", "?")
    print(f"\n{'=' * 50}")
    print(f"  REPORT - Shipment {sid}")
    print(f"{'=' * 50}")
    print(f"  Status        : {state.get('status', 'new')}")
    print(f"  Classification: {state.get('exception_type', 'Unclassified')}")
    print(f"  Severity      : {state.get('severity', 'Unknown')}")

    missing = state.get("missing_information", [])
    if missing:
        print(f"  Missing info  : {', '.join(missing)}")

    actions = state.get("actions", [])
    if actions:
        print("  Actions:")
        for a in actions:
            print(f"    [{a.get('status', 'pending')}] {a.get('id', '')}: {a.get('description', '')}")
    else:
        for rec in state.get("recommended_actions", []):
            print(f"    [pending] {rec}")
    print("-" * 50)


# ── Option 1: Add new issue ─────────────────────────────────────────

async def add_new_issue(ticket_service: TicketService):
    """Prompt user for issue details and insert into the database."""
    print("\n-- Add New Issue --")
    origin = input("  Origin      : ").strip()
    destination = input("  Destination : ").strip()
    carrier = input("  Carrier     : ").strip()
    description = input("  Description : ").strip()

    if not all([origin, destination, carrier, description]):
        print("  [!] All fields are required.")
        return

    ticket = await ticket_service.create_ticket(
        TicketCreate(
            origin=origin,
            destination=destination,
            carrier=carrier,
            issue_description=description,
        )
    )
    print(f"\n  [OK] Issue created - Shipment ID: {ticket['shipment_id']}")


# ── Option 2: Run agent on an issue ─────────────────────────────────

async def run_agent_on_issue(agent):
    """List issues, let user pick one, and run the agent to analyze it."""
    ids = await ticket_repository.list_ids()
    if not ids:
        print("\n  No issues in the database. Add one first.")
        return

    print("\n-- Existing Issues --")
    for sid in ids:
        ticket = await ticket_repository.get(sid)
        desc = (ticket["issue_description"][:60] + "...") if len(ticket["issue_description"]) > 60 else ticket["issue_description"]
        print(f"  [{sid}] {ticket['origin']} -> {ticket['destination']} | {desc}")

    try:
        choice = int(input("\n  Enter shipment ID to analyze: "))
    except ValueError:
        print("  [!] Invalid ID.")
        return

    ticket = await ticket_repository.get(choice)
    if not ticket:
        print(f"  [!] Shipment {choice} not found.")
        return

    config = shipment_thread_config(choice)
    print(f"\n  Running agent on shipment {choice}...")

    try:
        await agent.ainvoke(
            {
                "shipment_id": choice,
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Shipment exception reported for shipment {choice}: {ticket['issue_description']}. "
                            f"Origin: {ticket['origin']}, Destination: {ticket['destination']}, "
                            f"Carrier: {ticket['carrier']}. Analyze this case."
                        ),
                    }
                ],
            },
            config=config,
        )
        snapshot = await agent.aget_state(config)
        print_report(snapshot.values)
    except Exception as e:
        print(f"  [!] Agent error: {e}")


# ── Option 3: View / update current issues ───────────────────────────

async def view_update_issues(agent):
    """List issues with agent state, let user interact (update action, add context, chat)."""
    ids = await ticket_repository.list_ids()
    if not ids:
        print("\n  No issues in the database.")
        return

    # Show all issues with their current status
    print("\n-- Current Issues --")
    for sid in ids:
        config = shipment_thread_config(sid)
        ticket = await ticket_repository.get(sid)
        status = "new"
        try:
            snapshot = await agent.aget_state(config)
            if snapshot and snapshot.values:
                status = snapshot.values.get("status", "new")
        except Exception:
            pass
        desc = (ticket["issue_description"][:50] + "...") if len(ticket["issue_description"]) > 50 else ticket["issue_description"]
        print(f"  [{sid}] {status:<18} | {desc}")

    try:
        choice = int(input("\n  Enter shipment ID to interact with: "))
    except ValueError:
        print("  [!] Invalid ID.")
        return

    ticket = await ticket_repository.get(choice)
    if not ticket:
        print(f"  [!] Shipment {choice} not found.")
        return

    config = shipment_thread_config(choice)

    # Show current state
    try:
        snapshot = await agent.aget_state(config)
        if snapshot and snapshot.values:
            print_report(snapshot.values)
        else:
            print(f"\n  Shipment {choice} has not been analyzed yet. Run agent first (option 2).")
            return
    except Exception:
        print(f"\n  No agent state found for shipment {choice}. Run agent first (option 2).")
        return

    # Sub-menu for this issue
    print("\n  What would you like to do?")
    print("    a) Mark an action as completed")
    print("    b) Add context / notes")
    print("    c) Chat with agent about this issue")
    print("    d) Go back")

    sub = input("  Choose [a/b/c/d]: ").strip().lower()

    if sub == "a":
        actions = snapshot.values.get("actions", [])
        pending = [a for a in actions if a.get("status") != "completed"]
        if not pending:
            print("  No pending actions.")
            return
        print("\n  Pending actions:")
        for a in pending:
            print(f"    {a['id']}: {a.get('description', '')}")
        action_id = input("  Enter action ID to complete (e.g. ACT-1): ").strip()
        if not action_id:
            return
        await agent.ainvoke(
            {"messages": [{"role": "user", "content": f"Mark action {action_id} as completed."}]},
            config=config,
        )
        snap = await agent.aget_state(config)
        print_report(snap.values)

    elif sub == "b":
        source = input("  Source (e.g. operator, carrier, warehouse): ").strip()
        content = input("  Context / note: ").strip()
        if not source or not content:
            print("  [!] Both source and content are required.")
            return
        await agent.ainvoke(
            {"messages": [{"role": "user", "content": f"Add context from '{source}': {content}"}]},
            config=config,
        )
        print("  [OK] Context added.")

    elif sub == "c":
        message = input("  Your message to the agent: ").strip()
        if not message:
            return
        await agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
        )
        snap = await agent.aget_state(config)
        # Print the last assistant message
        messages = snap.values.get("messages", [])
        for msg in reversed(messages):
            if hasattr(msg, "content") and getattr(msg, "type", None) == "ai" and msg.content:
                print(f"\n  Agent: {msg.content}")
                break
        else:
            print_report(snap.values)

    elif sub == "d":
        return
    else:
        print("  [!] Invalid choice.")


# ── Main loop ────────────────────────────────────────────────────────

async def run_cli() -> None:
    await initialize_ticket_schema()
    uri = get_database_uri()

    async with AsyncPostgresSaver.from_conn_string(uri) as checkpointer:
        await checkpointer.setup()
        agent = create_transit_agent(checkpointer=checkpointer)
        ticket_service = TicketService(ticket_repository, agent)

        while True:
            print_banner()
            choice = input("  Choose [1-4]: ").strip()

            if choice == "1":
                await add_new_issue(ticket_service)
            elif choice == "2":
                await run_agent_on_issue(agent)
            elif choice == "3":
                await view_update_issues(agent)
            elif choice == "4":
                print("\n  Goodbye!\n")
                break
            else:
                print("  [!] Please enter 1, 2, 3, or 4.")


def main() -> None:
    asyncio.run(run_cli())


if __name__ == "__main__":
    main()
