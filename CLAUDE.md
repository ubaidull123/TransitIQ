# CLAUDE.md — TransitIQ

This file scopes what Claude should (and should not) do when working in this repo. Read this before making changes.

## What This Project Is

TransitIQ is a supply-chain exception management API. An agent analyzes shipment exceptions (delays, customs holds, etc.) and — eventually — takes real-world actions on them, with human approval for high-risk cases.

**Framework layer, by phase:** V1–V3 use LangChain's `create_agent` + middleware (a single agent with tools; runs on the LangGraph engine underneath, so checkpointing/durability is free). V4+ steps down to a hand-written LangGraph `StateGraph`, once multi-agent routing (Supervisor pattern) is actually needed. **Deep Agents is not used on this project** — its virtual filesystem / subagent-spawning / auto-compression features solve problems this project doesn't have. Don't reach for it.

Full roadmap: see `PROJECT_ROADMAP.md`. **That file describes 5 future versions. It is a map of where the project is headed, not a spec for what to build right now.**

## Current Phase

> ⬇️ **Update this line as the project progresses — it's the single most important line in this file.**

**We are on: V1 — The Stable Foundation**

Only build what V1 needs:
- `POST /exceptions` endpoint, Pydantic-validated
- `GET /exceptions` read endpoint (newest first, limited)
- A React intake console in `frontend/` — record an exception, and see the ledger
- Save issues to a Postgres `issues` table
- A single agent built with `create_agent`, with a few plain tools (`analyze_case`, `add_context`, `update_action`) — no hand-written `StateGraph`
- A CLI to test the agent loop locally

Nothing else. If it's not in the current phase's feature list in `PROJECT_ROADMAP.md`, it does not exist yet.

## Hard Rules — Do Not Do These Unless the Current Phase Says So

- ❌ No hand-written LangGraph `StateGraph`. Use `create_agent` + middleware until V4 — that's the whole point of the framework step-down described in the roadmap. Don't hand-roll graph nodes/edges "for control" before V4 actually requires it.
- ❌ No Deep Agents, ever, unless explicitly re-scoped. Virtual filesystem, subagent-spawning, and auto context-compression are not problems this project has.
- ❌ No multi-agent / Supervisor / router pattern. That's V4. Right now there is **one** agent.
- ❌ No RAG, no pgvector, no document parsing. That's V4.
- ❌ No real external API calls (Resend, EasyPost, carrier APIs). That's V3. Stub or mock instead.
- ❌ No HITL middleware/approval flow. That's V3.
- ❌ No Redis, ARQ, Celery, background workers, or webhooks. That's V5.
- ❌ No Prometheus, Grafana, or metrics endpoints. That's V5.
- ❌ No CI/CD pipelines, load testing, or Docker multi-stage optimization. That's V5.
- ❌ No LangSmith tracing setup. That's V2.
- ❌ No speculative abstraction — no plugin systems, no "in case we need it later" interfaces, no config for features that don't exist yet.

If a task seems to call for one of these, **stop and ask** rather than building it. The roadmap existing is not permission to pull features forward.

## Default Engineering Posture

- **Simplest thing that works, for the phase we're in.** Don't add a layer of indirection to "future-proof" something — YAGNI applies hard here.
- **Boring code over clever code.** Plain functions and straightforward SQL over frameworks-on-frameworks.
- **One agent via `create_agent`, few tools, no hand-written graph** until the roadmap explicitly says otherwise (V4).
- **No new dependencies without asking**, especially anything from a later phase's tech stack (see the Tech Stack Evolution table in the roadmap).
- **Prefer editing over adding files.** Don't scaffold a new module/service/package for something that fits in an existing file.
- If you (Claude) find yourself designing something that spans multiple files, multiple abstractions, or "sets things up for V4," that's a signal to stop and do the smaller thing instead.

## Current Tech Stack (do not add to this without asking)

- Python 3.13, `uv` for dependency management
- FastAPI + Uvicorn
- SQLAlchemy (async, `psycopg 3` driver) — use the existing models/session setup, don't introduce a second data-access pattern alongside it
- `langchain` (`create_agent`) — runs on the LangGraph engine, `AsyncPostgresSaver` for checkpointing (`thread_id = shipment:{id}`), but write zero hand-rolled graph code at this phase
- React 19 + Vite + TypeScript in `frontend/`, managed with `npm` — served by FastAPI's StaticFiles in production, proxied to it in dev. No UI or component libraries; plain CSS.
- Standard `logging` — not LangSmith yet

## When In Doubt

Ask: *"Does V1's Definition of Done in `PROJECT_ROADMAP.md` require this?"*
If no — don't build it. Flag it as a "later phase" idea instead of implementing it.