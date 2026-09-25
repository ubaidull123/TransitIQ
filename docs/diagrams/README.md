# TransitIQ — Architecture Diagrams

A hand-maintained map of how TransitIQ actually works right now.

**"Functional" is a rule, not a vibe.** Every box and arrow on these pages
corresponds to code that exists in `src/`. If a feature is only planned in
`roadmap.md`, it does not appear here. Where something is built but never
executed, it is drawn and explicitly labelled as not-invoked.

## How to read these pages

Every page has the same five parts:

1. **The question it answers** — so you know why the page exists.
2. **The diagram** — kept small on purpose. A diagram you have to squint at
   teaches nothing.
3. **How to read it** — the story the arrows are telling.
4. **Follow it in the code** — `file:line` pointers to the real thing. Reading
   the diagram then the code is how the two stick together.
5. **Gotchas** — the parts that surprised me, which will probably surprise you.

Read them in order. 01 sets the board, 02 walks a request across it, 03 opens up
the agent, 04 lands on the database.

## The views

| # | Page | The question it answers |
|---|------|-------------------------|
| 01 | [System context](01-system-context.md) | What are the moving parts, and what does the process talk to? |
| 02 | [Request flow](02-request-flow.md) | What happens, in order, when an exception is recorded? |
| 03 | [Agent loop](03-agent-loop.md) | How is the agent assembled, and what runs when it's invoked? |
| 04 | [Data model](04-data-model.md) | What tables exist, and how are they connected? |

## Update contract

These pages go stale the moment they are forgotten. When you change something,
change the page that owns it:

| If you change... | Files that changed | Update page |
|---|---|---|
| An endpoint, status code, or the error envelope | `api/routers/`, `api/schemas/` | 02 |
| The request/response shape | `api/schemas/exception_schema.py` | 02 |
| Agent config, middleware, tools, or state | `workflow/agent.py`, `workflow/middleware.py`, `workflow/tools/`, `workflow/state.py` | 03 |
| The system prompt | `workflow/prompts/system.py` | 03 |
| A table, column, or index | `database/models/`, `database/db.py` | 04 (and re-sync the drawdb canvas) |
| Which model is used, or the LLM provider | `llm/openrouter_service.py` | 01 |
| A dependency, or a new external service | `pyproject.toml` | 01 |
| Anything that makes an agent call actually run | `api/routers/`, or a new CLI | 02 **and** 03 |

Rule of thumb: if a change makes one of these diagrams wrong, fixing the diagram
is part of that change, not a follow-up task.

## Verified gaps

Both of these were confirmed by running code, not by reading it. They are listed
here so the diagrams never imply more working software than exists.

**1. The agent is never invoked.** `POST /exceptions` calls `agent.aupdate_state(...)`
to seed the checkpoint, then returns. There is no `ainvoke`, no `astream`, no
agent endpoint, and no CLI anywhere in the codebase. All eight tools in
`workflow/tools/` are therefore unreachable at runtime. The agent is assembled at
startup and sits fully wired but unused. See page 02.

**2. The `transitiq` CLI does not exist.** `pyproject.toml` line 31 declares:

```toml
transitiq = "transitiq.main:main"
```

but `src/transitiq/main.py` is not in the repo. Running `transitiq` fails with
`ModuleNotFoundError: No module named 'transitiq.main'`. `roadmap.md` lists "a CLI
to test the agent loop locally" as part of V1 — it is declared but not built.

## Keeping the drawdb canvas in sync

Page 04 is the committed, diffable source of truth for the schema. The interactive
drawdb canvas is a separate, richer view of the same five tables. If you change
`database/models/`, update page 04 first, then mirror it in drawdb — the canvas is
not version-controlled, so page 04 is the one that survives.