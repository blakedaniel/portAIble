# portAIble

Interactive prompt-building experience for AI-driven code porting.

A user uploads or links source code; the system uses an LLM to draft a structured **source code profile** (languages, frameworks, packages, important info) which the user reviews and edits. The same is repeated for a **destination code profile**, then the user answers LLM-generated **design decisions**. The backend assembles a final prompt — combining both profiles + matching markdown from a bundled `prompt-bank/` (language docs, framework docs, src→dst transition guides) + the answered decisions — and ships it with the source ZIP to the [`local-chat-agent`](../local-chat-agent) AI Pipeline for code generation.

## Architecture

- **Frontend**: Nuxt 4 + Nuxt UI (`frontend/`)
- **Backend**: FastAPI, Python 3.14 (`backend/`), use-case-driven clean architecture (`domain → ports ← infrastructure`, `usecases` orchestrate ports, `api` wires adapters via `Depends`)
- **Persistence**: SQLite via SQLAlchemy 2.0 async (sessions + jobs tables) + Alembic; binary artifacts on the filesystem under `WORKSPACE_DIR`
- **AI calls**: DSPy with structured (Pydantic-typed) outputs against Ollama
- **AI Pipeline**: HTTP-calls `local-chat-agent`'s `POST /chat` (multipart `file` + `instructions`)

## Running locally

```bash
# Backend (port 8001)
uv sync
cp .env.example .env
uv run uvicorn portaible.app:app --port 8001 --reload

# Frontend (port 3000)
cd frontend && pnpm install && pnpm dev

# AI Pipeline must be running separately on port 8000:
cd ../local-chat-agent && uv run local-chat-agent
```

## Repo layout

See [`api-design.md`](./api-design.md) for the original Mermaid sketch and `/home/blake/.claude/plans/i-want-to-go-sparkling-flame.md` for the implementation plan.
