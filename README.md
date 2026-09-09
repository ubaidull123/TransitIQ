# TransitIQ

TransitIQ is a shipment-exception management service built with FastAPI, LangChain, LangGraph, and PostgreSQL. It accepts an original shipment ticket, assigns the case a durable LangGraph thread, and lets an AI-assisted workflow manage analysis, context, actions, status, and history.

The current release provides a stable V3 foundation for later document and tracking intelligence work. It does not perform external operational actions automatically.

## Core capabilities

- Validate and accept shipment exception tickets through FastAPI.
- Store original ticket data in a dedicated PostgreSQL `issues` table.
- Give every shipment a stable `shipment:{shipment_id}` LangGraph thread.
- Persist complete operational state with `AsyncPostgresSaver`.
- Load the original ticket into agent state on first use.
- Analyze and re-analyze exceptions through structured agent tools.
- Maintain chronological context, analysis history, action items, and case status.
- Operate cases through an interactive command-line interface.

## Architecture

```text
POST /exceptions
       |
       v
TicketService ---------------------> PostgreSQL issues
       |                              original ticket only
       v
shipment:{id} checkpoint
       |
       v
TransitIQ Agent <------------------- CLI / future interfaces
       |
       +--> load_ticket middleware
       +--> operational tools
       |
       v
TransitState
       |
       v
AsyncPostgresSaver ----------------> PostgreSQL checkpoints
                                      state and history
```

### Responsibility boundaries

| Component | Responsibility |
|---|---|
| FastAPI | Validate new ticket requests and manage the application lifespan. |
| `TicketService` | Save the ticket and initialize its LangGraph checkpoint. |
| `TicketRepository` | Create and read immutable ticket records. |
| `load_ticket` middleware | Hydrate ticket fields into `TransitState` on first agent use. |
| TransitIQ agent | Select the appropriate operational tool for each case interaction. |
| `TransitState` | Represent the current status, analysis, context, actions, and messages. |
| `AsyncPostgresSaver` | Persist state snapshots and complete checkpoint history. |

## Technology

- Python 3.13+
- FastAPI and Uvicorn
- LangChain and LangGraph
- PostgreSQL with asynchronous psycopg 3
- LangGraph PostgreSQL checkpointer
- OpenRouter through `langchain-openrouter`
- `uv` for dependency and environment management

## Getting started

### Prerequisites

- Python 3.13 or newer
- PostgreSQL
- [`uv`](https://docs.astral.sh/uv/)
- An OpenRouter API key

### Installation

```powershell
git clone https://github.com/ubaidull123/TransitIQ.git
cd TransitIQ
uv sync
```

Create a `.env` file in the project root:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=TransitIQ_DB
DB_USER=postgres
DB_PASSWORD=your_database_password
OPENROUTER_API_KEY=your_openrouter_api_key

# Optional API overrides
API_HOST=127.0.0.1
API_PORT=8765
```

Do not commit `.env` or expose production credentials.

The application creates the `issues` table and LangGraph checkpoint tables during startup when they do not already exist.

## Running the API

```powershell
uv run transitiq-api
```

Default address: `http://127.0.0.1:8765`

Interactive API documentation is available at:

- Swagger UI: `http://127.0.0.1:8765/docs`
- ReDoc: `http://127.0.0.1:8765/redoc`

### Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Confirm that the API process is available. |
| `POST` | `/exceptions` | Validate a ticket, store it, and initialize its agent thread. |

Example request:

```powershell
$body = @{
    origin = "Karachi"
    destination = "Dubai"
    carrier = "Example Carrier"
    issue_description = "Shipment is delayed during customs clearance"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8765/exceptions" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

Successful requests return HTTP `201 Created` with the stored ticket:

```json
{
  "origin": "Karachi",
  "destination": "Dubai",
  "carrier": "Example Carrier",
  "issue_description": "Shipment is delayed during customs clearance",
  "shipment_id": 42,
  "created_at": "2026-09-09T12:00:00"
}
```

## Running the CLI

```powershell
uv run transitiq
```

The CLI supports:

1. Creating a new shipment issue.
2. Running the agent on an existing issue.
3. Viewing case state and updating actions or context.
4. Continuing a case conversation through its existing checkpoint thread.

API and CLI ticket creation both use `TicketService`, so they follow the same persistence path.

## Operational tools

| Tool | Purpose |
|---|---|
| `analyze_case` | Create the initial structured analysis and action items. |
| `reanalyze_case` | Append a new analysis after facts or context change without duplicating actions. |
| `add_context` | Append a timestamped operational update and its source. |
| `get_case` | Read the current shipment case. |
| `get_analysis_history` | Read accumulated structured analyses. |
| `get_actions` | Read current operational actions. |
| `update_action` | Change the status of one or more actions. |
| `update_case_status` | Change the overall case lifecycle status. |

State-changing interactions are intentionally kept sequential: the agent is instructed to execute at most one state-changing tool per response.

## Case persistence

Each shipment uses one configuration:

```python
{
    "configurable": {
        "thread_id": f"shipment:{shipment_id}"
    }
}
```

The `issues` table remains the source of the original user submission. Once the agent loads that ticket, operational data is maintained in `TransitState` and persisted through PostgreSQL checkpoints.

Typical state includes:

- Shipment identity and route information
- Case status and current workflow step
- Exception classification and severity
- Missing information and recommendations
- Operational context
- Action items
- Latest analysis and analysis history
- Conversation messages

## Testing

The test suite focuses on stable contracts rather than exhaustive prompt variations:

```powershell
uv run pytest
```

Current tests cover:

- Ticket persistence and checkpoint initialization
- The `POST /exceptions` API boundary
- Re-analysis without action duplication
- Reopening a closed case

Run coverage when needed:

```powershell
uv run pytest --cov=transitiq --cov-report=term-missing
```

Tests use deterministic fakes and do not require live OpenRouter calls.

## Project structure

```text
TransitIQ/
|-- src/transitiq/
|   |-- api/
|   |   |-- app.py                  # FastAPI routes and lifespan
|   |   `-- run.py                  # Windows-compatible Uvicorn launcher
|   |-- database/
|   |   |-- db.py                   # Connection lifecycle and schema setup
|   |   `-- repositories.py         # Immutable ticket repository
|   |-- llm/
|   |   `-- openrouter_service.py   # OpenRouter client configuration
|   |-- services/
|   |   `-- ticket_service.py       # Ticket and checkpoint orchestration
|   |-- workflow/
|   |   |-- Tools/
|   |   |   `-- operational_tools.py
|   |   |-- agent.py                # Agent factory and case-aware prompt
|   |   |-- config.py               # Shipment thread configuration
|   |   |-- middleware.py           # First-use ticket hydration
|   |   `-- state.py                # TransitState and reducers
|   |-- main.py                     # Interactive CLI
|   `-- models.py                   # Ticket request and response models
|-- tests/
|   `-- test_stable_contract.py
|-- pyproject.toml
`-- uv.lock
```

## Current scope

TransitIQ currently manages human-submitted shipment exceptions. Document extraction, tracking-provider integrations, automatic exception detection, and autonomous external actions are intentionally outside this stable foundation and can be added as isolated future capabilities.
