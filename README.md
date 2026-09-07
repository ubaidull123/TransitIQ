# TransitIQ

TransitIQ is a Python shipment-exception analysis agent. It reads saved shipment issues from PostgreSQL and uses LangChain with OpenRouter to:

1. Classify the exception.
2. Determine its severity.
3. Identify missing information.
4. Recommend operational actions.
5. Stream a final report to the terminal.

## Requirements

- Python 3.13+
- PostgreSQL
- An OpenRouter API key
- `uv` for dependency management

## Setup

Install the project dependencies:

```powershell
uv sync
```

Create a `.env` file containing:

```dotenv
OPENROUTER_API_KEY=your_key
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password
```

The `.env` file contains secrets and should not be committed to version control.

## Run

Process the shipment issues currently stored in the database:

```powershell
uv run python -m transitiq_v2.main
```

If the virtual environment is already activated:

```powershell
python -m transitiq_v2.main
```

The current version is a CLI batch workflow. Each valid shipment is processed through all agent stages and its final analysis is printed in the terminal.
