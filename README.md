# TransitIQ

TransitIQ is a **shipment-exception analysis agent** for logistics operations. It takes a shipment problem (delay, customs hold, missing documents, damaged cargo, etc.), runs a structured LLM analysis pipeline, and produces a classification, a severity rating, a list of missing information, and recommended operational actions.

It exposes two interfaces on top of the same agent:

- **CLI batch workflow** — reads every stored shipment issue from PostgreSQL and streams a report per shipment to the terminal.
- **FastAPI REST API** — persistent exception cases with on-demand analysis and a saved analysis history per case.

Built with LangChain / LangGraph over OpenRouter and PostgreSQL.

---

## Features

- **Structured agent pipeline** — a single LangGraph agent that walks through five steps: `classification → severity → missing_info → recommendation → done`. Each step swaps in its own system prompt and tool via a middleware hook, and each tool advances the state machine by returning a `Command` that updates the graph state.
- **CLI batch workflow** — pulls all issues from the database and streams a `TRANSITIQ REPORT` per shipment, skipping issues whose description is too short to analyze.
- **Persistent exception cases** — issues are stored in PostgreSQL with a lifecycle `status` (`new`, `analyzed`, …) and timestamps.
- **Saved analysis history** — every analysis run is stored in `analysis_runs`; re-analyzing a case creates a new record instead of overwriting the previous one.
- **Idempotent schema setup** — the `issues` and `analysis_runs` tables are created on demand with `CREATE TABLE IF NOT EXISTS` plus `ALTER TABLE … ADD COLUMN IF NOT EXISTS` migration statements, so no manual migration step is required.

---

## Tech stack

| Layer | Technology |
|---|---|
| Language | Python ≥ 3.13 |
| Agent framework | LangChain (`create_agent`), LangGraph |
| LLM access | OpenRouter (`ChatOpenRouter`) |
| API layer | FastAPI, Pydantic v2, uvicorn |
| Database | PostgreSQL (psycopg2) |
| Tooling | `uv` (project + environment management) |

---

## Requirements

- Python 3.13+
- PostgreSQL
- An [OpenRouter](https://openrouter.ai) API key
- [uv](https://docs.astral.sh/uv/)

---

## Setup

```bash
uv sync
```

Create a `.env` file in the project root with your database credentials and API key:

```dotenv
DB_HOST=localhost
DB_PORT=5432
DB_NAME=transitiq
DB_USER=postgres
DB_PASSWORD=your_password
OPENROUTER_API_KEY=your_openrouter_key
```

> The database must already exist; TransitIQ creates its tables on first use but not the database itself.

---

## Running the CLI batch workflow

```bash
uv run python -m transitiq_v2.main
```

or, using the package entry point:

```bash
uv run transitiq
```

The CLI iterates over all issues in the `issues` table and streams a report for each one. Issues whose description is shorter than 10 characters or contains fewer than 2 words are skipped.

---

## Running the API server

```bash
uv run uvicorn transitiq_v2.api.api:app --reload
```

Interactive API docs are available at <http://127.0.0.1:8000/docs>.

### Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/exceptions` | Create a new exception case from `origin`, `destination`, `carrier`, `issue_description`; returns the new `shipment_id`. |
| `GET` | `/exceptions` | List all exception cases (raw database rows). |
| `GET` | `/exceptions/{id}` | Fetch a single case by `shipment_id` (raw database row). |
| `PATCH` | `/exceptions/{id}` | Update a case's `issue_description`. |
| `PATCH` | `/exceptions/{id}/status` | Update a case's lifecycle `status`. |
| `POST` | `/exceptions/{exception_id}/analyze` | Run the TransitIQ agent on a case and persist the result as a new analysis. Returns 422 if the issue description is too short or unclear, 502 if the agent fails or returns an incomplete analysis. Marks the case `analyzed`. |
| `GET` | `/exceptions/{exception_id}/analyses` | Analysis history for a case, oldest first. |
| `GET` | `/analyses/{analysis_id}` | Fetch a single saved analysis. |

An analysis record contains: `id`, `exception_id`, `exception_type`, `severity`, `missing_information`, `recommended_actions`, `model_name`, and `created_at`.

---

## Database schema

Both tables are created automatically on first use.

**`issues`** — one row per exception case:

| Column | Type | Notes |
|---|---|---|
| `shipment_id` | `SERIAL PRIMARY KEY` | Internal case id |
| `origin` | `VARCHAR(255) NOT NULL` | |
| `destination` | `VARCHAR(255) NOT NULL` | |
| `carrier` | `VARCHAR(255) NOT NULL` | |
| `issue_description` | `TEXT NOT NULL` | |
| `status` | `VARCHAR(255) NOT NULL DEFAULT 'new'` | Case lifecycle (e.g. `new`, `analyzed`) |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | |
| `updated_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | |

**`analysis_runs`** — one row per agent run, linked to a case:

| Column | Type | Notes |
|---|---|---|
| `id` | `SERIAL PRIMARY KEY` | |
| `exception_id` | `INTEGER NOT NULL REFERENCES issues(shipment_id)` | |
| `exception_type` | `VARCHAR(255) NOT NULL` | |
| `severity` | `VARCHAR(255) NOT NULL` | |
| `missing_information` | `TEXT NOT NULL` | |
| `recommended_actions` | `TEXT NOT NULL` | JSON-encoded list |
| `model_name` | `VARCHAR(255) NOT NULL` | Model used for the run |
| `created_at` | `TIMESTAMP DEFAULT CURRENT_TIMESTAMP` | |

---

## How the agent works

A single LangGraph agent (`transitiq_v2.workflow.agent`) is built with `create_agent` using the `TransitState` schema and a `@wrap_model_call` middleware (`apply_transit_step`). The middleware inspects `state["current_step"]`, looks up the matching entry in `STEP_CONFIG`, and swaps in that step's system prompt and available tool before each model call.

The state machine (`current_step`) progresses:

```
classification  →  severity  →  missing_info  →  recommendation  →  done
```

Each step is driven by one tool. Tools return a `langgraph.types.Command` that writes the result into state **and** advances `current_step`:

| Step | Tool | Writes |
|---|---|---|
| `classification` | `classify_exception_type` | `exception_type` |
| `severity` | `record_severity` | `severity` |
| `missing_info` | `record_missing_information` | `missing_info`, `actions` |
| `recommendation` | `record_recommendations` | `recommendations` |
| `done` | — (no tools) | Final summary |

The final step instructs the model to return a summary in English only, not to invent shipment facts, and to state clearly if the supplied data is meaningless or insufficient to analyze.

**Exception types:** Delayed shipment, Missing documents, Customs hold, Incorrect address, Damaged cargo, Carrier cancellation, Payment/document mismatch, Insufficient information.

**Severity levels:** Low, Medium, High, Critical.

The model is configured in `transitiq_v2/llm/openrouter_service.py` (`OPENROUTER_MODEL`).

---

## Project layout

```
src/transitiq_v2/
├── main.py                        # CLI batch workflow entry point
├── input.py                       # Loads issues from the database
├── output.py                      # Agent output model
├── api/
│   ├── api.py                     # FastAPI app
│   ├── exception_routes.py        # Exception CRUD endpoints
│   ├── analysis_routes.py         # Analysis endpoints
│   └── models.py                  # Pydantic request/response models
├── database/
│   └── db.py                      # Connection + idempotent table creation
├── llm/
│   └── openrouter_service.py      # OpenRouter client and model config
└── workflow/
    ├── agent.py                   # LangGraph agent construction
    ├── state.py                   # Typed agent state + taxonomies
    ├── middlewere.py              # apply_transit_step middleware
    └── Tools/                     # Per-step tools + STEP_CONFIG prompts
```
