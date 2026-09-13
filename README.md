# Database Copilot

Database Copilot is an authenticated AI assistant that translates plain-English
business questions into PostgreSQL, executes the SQL through a read-only
connection, and returns both an explanation and the underlying result table.

## What it does

- Inspects configured PostgreSQL schemas at query time.
- Combines live schema metadata with human-written business definitions.
- Generates PostgreSQL using a tool-calling OpenAI agent.
- Runs one statement inside a database-enforced `READ ONLY` transaction.
- Applies a statement timeout and maximum returned-row limit.
- Shows the generated SQL and query results in the chat interface.
- Stores each user's conversation history in Supabase.

## Architecture

The Vite React SPA authenticates users with Supabase Auth and streams chat
requests to FastAPI. The backend owns schema inspection, SQL generation,
read-only execution, result validation, and chat persistence.

Two database connections are intentionally separate:

- `DATABASE_URL`: the product Supabase database for users, chats, and migrations.
- `TARGET_DATABASE_URL`: the PostgreSQL database that the copilot may query.

See [docs/architecture.md](docs/architecture.md) for the full request flow and
safety model.

## Stack

- Backend: Python 3.12, FastAPI, PydanticAI, SQLAlchemy, psycopg
- Frontend: Vite, React, TypeScript, Tailwind CSS, shadcn/ui
- Product persistence and authentication: Supabase
- Target data source: PostgreSQL or Supabase Postgres
- LLM: OpenAI

## Project structure

```text
document-copilot/
├── backend/
│   ├── app/
│   │   ├── assistant/       # Agent, tools, output contract
│   │   ├── chat/            # Turn orchestration and streaming
│   │   └── database/        # Product and target database access
│   ├── database_description.md
│   └── tests/
├── frontend/
│   └── src/
│       ├── components/chat/
│       ├── hooks/
│       └── pages/
└── docs/
```

## Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)
- Node.js 20+
- [pnpm](https://pnpm.io/)
- A Supabase project
- An OpenAI API key
- A PostgreSQL database and dedicated read-only user

## Configuration

Create backend and frontend environment files:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

Required backend values:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://product-user:password@host:5432/product-db

TARGET_DATABASE_URL=postgresql://copilot-reader:password@host:5432/analytics
TARGET_DATABASE_SCHEMAS=public
DATABASE_DESCRIPTION_PATH=database_description.md
QUERY_MAX_ROWS=200
QUERY_TIMEOUT_MS=15000

OPENAI_API_KEY=sk-...
OPENAI_CHAT_MODEL=gpt-4.1
ALLOWED_ORIGINS=http://localhost:5173
```

Required frontend values:

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-anon-key
```

Add metric definitions, required filters, join guidance, timezone conventions,
and data-quality notes to `backend/database_description.md`. Do not place
credentials in that file.

## Target database permissions

Use a dedicated PostgreSQL role with only:

- `CONNECT` on the target database
- `USAGE` on approved schemas
- `SELECT` on approved tables or views

The application also restricts statement types, starts a `READ ONLY`
transaction, enforces a timeout, limits returned rows, and always rolls the
transaction back. Database permissions remain the primary security boundary.

## Run locally

Install dependencies and apply product-database migrations:

```bash
cd backend
uv sync
uv run alembic upgrade head

cd ../frontend
pnpm install
```

Start the backend:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Start the frontend in another terminal:

```bash
cd frontend
pnpm dev
```

Open `http://localhost:5173`.

## Example

Question:

> Which products generated the most non-cancelled revenue this quarter?

Database Copilot inspects the available schema and business description,
generates an appropriate aggregate query, executes it with the read-only target
connection, and displays:

- a concise explanation
- the exact SQL
- the returned columns and rows
- execution time and truncation status

## Verification

```bash
cd backend
uv run ruff check app tests
uv run pytest -m "not integration" --ignore=tests/ingest

cd ../frontend
pnpm tsc --noEmit
pnpm lint
```

The ingestion and retrieval directories are retained from the original Document
Copilot baseline but are no longer used by the live chat path.
