from transitiq_v2.input import serve_issues
from transitiq_v2.workflow.agent import agent


def main():
    for issue in serve_issues():
        description = issue.get("description", "").strip()

        if len(description) < 10 or len(description.split()) < 2:
            print(
                f"[SKIPPED] Shipment {issue.get('issue_id', 'unknown')}: "
                "Issue description is too short or unclear."
            )
            continue

        initial_state = {
            **issue,
            "description": description,
            "current_step":"classification",
            "messages": [
                {
                    "role": "user",
                    "content" :(
                        f"Analyze shipment {issue['issue_id']}. "
                        f"Origin: {issue['origin']}. "
                        f"Destination: {issue['destination']}. "
                        f"Carrier: {issue['carrier']}. "
                        f"Problem: {issue['description']}"  

                        )
                }
            ]
        }
        # result = agent.stream_events(initial_state)
        final_answer = ""

        for update in agent.stream(initial_state, stream_mode="updates"):
            tool_update = update.get("tools", {})

            if "Issue_type" in tool_update:
                print(f"\n Classification: {tool_update['Issue_type']}")

            if "severity" in tool_update:
                print(f"\n Severity: {tool_update['severity']}")

            if "missing_info" in tool_update:
                print("\n Missing information identified")

            if "recommendations" in tool_update:
                print("\n Recommendations prepared")

            model_update = update.get("model")
            if model_update:
                message = model_update["messages"][-1]
                if message.content:
                    final_answer = message.content

                    print("\n" + "=" * 60)
                    print(f"TRANSITIQ REPORT — SHIPMENT {issue['issue_id']}")
                    print("=" * 60)
                    print(final_answer)

if __name__ == "__main__":
    main()
