# TransitIQ

Autonomous logistics exception management powered by LangChain, LangGraph, and PostgreSQL.

## Architecture

```text
POST /exceptions -> TicketService -> PostgreSQL issues
                         |
                         +-> shipment:{id} checkpoint
                                      |
CLI / future interfaces -> TransitIQ Agent
                                      |
                              Operational tools
                                      |
                                 TransitState
                                      |
                            AsyncPostgresSaver
```

### Responsibility Split

- **FastAPI**: Validates new tickets through `POST /exceptions` and owns the shared checkpointer through application lifespan.
- **`TicketService`**: Saves the immutable ticket and initializes its `shipment:{shipment_id}` checkpoint.
- **`issues` table**: Stores original user-submitted tickets (`shipment_id`, `origin`, `destination`, `carrier`, `issue_description`, `created_at`).
- **`load_ticket` middleware**: Automatically hydates ticket information from PostgreSQL into `TransitState` on first thread invocation, skipping subsequent database queries once present.
- **`TransitState`**: Active, bounded operational representation of the case containing classification, severity, action items, operational context, and analysis history.
- **`AsyncPostgresSaver`**: Persists durable agent workflow checkpoints and full state history in PostgreSQL (`thread_id = shipment:{shipment_id}`).

---

## Quick Start

### Prerequisites

- Python 3.13+
- PostgreSQL
- [uv](https://docs.astral.sh/uv/) package manager
- OpenRouter API key

### Setup

```bash
# Clone repository
git clone https://github.com/ubaidull123/TransitIQ.git
cd TransitIQ

# Install dependencies
uv sync

# Configure environment
cp .env.example .env
# Fill in: DB_HOST, DB_NAME, DB_USER, DB_PASSWORD, DB_PORT, OPENROUTER_API_KEY
```

### Running the CLI

```bash
uv run transitiq
# or
uv run python -m transitiq.main
```

### Running the API

```bash
uv run transitiq-api
```

Set `API_HOST` or `API_PORT` when the defaults (`127.0.0.1:8765`) are unavailable.

Create a ticket:

```http
POST /exceptions
Content-Type: application/json

{
  "origin": "Karachi",
  "destination": "Dubai",
  "carrier": "Example Carrier",
  "issue_description": "Shipment is delayed at customs"
}
```

Interactive menu:

```text
============================================
            TransitIQ CLI
============================================
  1)  Add new issue
  2)  Run agent on an issue
  3)  View / update current issues
  4)  Exit
============================================
  Choose [1-4]:
```

---

## Project Structure

```text
src/transitiq/
├── api/
│   └── app.py                       # POST /exceptions, health, API lifespan
├── services/
│   └── ticket_service.py            # Ticket intake and thread initialization
├── models.py                        # Typed ticket request/response models
├── main.py                          # Interactive CLI menu & entry point
├── database/
│   ├── db.py                        # Async psycopg connection & issues DDL
│   └── repositories.py             # TicketRepository (intake CRUD)
├── workflow/
│   ├── agent.py                     # Agent factory with LangGraph & checkpointer
│   ├── middleware.py                # load_ticket before_model hydration & validation
│   ├── state.py                     # Bounded TransitState schema
│   └── Tools/
│       └── operational_tools.py     # 8 operational tools modifying state via Command
└── llm/
    └── openrouter_service.py        # OpenRouter ChatOpenRouter client
```

---

## Operational Agent Tools

All tools operate strictly through `ToolRuntime` and `TransitState` using `Command(update=...)`, without directly touching checkpointer tables or issuing duplicate database queries:

| Tool | Type | Purpose |
|---|---|---|
| `analyze_case` | Write | Classify exception, evaluate severity, identify missing info, generate actions, append analysis |
| `reanalyze_case` | Write | Re-evaluate shipment when new operational context is received, appending to history |
| `add_context` | Write | Record chronological operational notes/updates from operators, carriers, or brokers |
| `update_action` | Write | Update action status (`pending`, `in_progress`, `completed`, `cancelled`), updating case status |
| `update_case_status` | Write | Transition lifecycle status (`new`, `analyzed`, `action_required`, `in_progress`, `resolved`, `closed`) |
| `get_case` | Read | Read complete current operational case state directly from state |
| `get_actions` | Read | Read action items directly from state |
| `get_analysis_history` | Read | Read chronological analysis history directly from state |

---

## Testing & Coverage

TransitIQ uses a small deterministic contract suite for its API, service, and state boundaries:

### Run All Tests

```bash
uv run pytest
```

### Run Coverage Report

```bash
uv run pytest --cov=transitiq --cov-report=term-missing
```

---

## Tech Stack

- **Python 3.13** + `uv`
- **FastAPI** + Uvicorn
- **LangChain** + `create_agent`
- **LangGraph** + `AsyncPostgresSaver`
- **PostgreSQL** + `psycopg` v3 (async)
- **OpenRouter** (DeepSeek v4 Flash)

## License

MIT
