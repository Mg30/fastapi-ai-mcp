# fastapi-ai-mcp

A Python/FastAPI starter kit for AI assistants with streaming responses,
PostgreSQL persistence, and optional MCP tools over stdio.

The API manages assistants, chats, and messages. SQLModel and Alembic handle
storage and migrations; services and repositories are assembled with
`dependency-injector`. The current LLM integration uses OpenAI Chat Completions.

## Quick start

Requires Python 3.12+, [uv](https://docs.astral.sh/uv/), and PostgreSQL.
Run the following commands from the repository root.

```bash
git clone https://github.com/Mg30/fastapi-ai-mcp.git
cd fastapi-ai-mcp
uv sync --frozen
```

Create a local `.env` file (already excluded by `.gitignore`):

```dotenv
OPENAI_API_KEY=replace-with-your-key
POSTGRES_USER=assistant
POSTGRES_PASSWORD=local-development-only
POSTGRES_HOST=localhost
POSTGRES_DB=assistant
POSTGRES_PORT=5432
```

`Settings` reads these values from `.env` or environment variables. Use the
credentials for your own PostgreSQL instance, or start a disposable local one:

```bash
docker run --detach --name fastapi-ai-mcp-db \
  --publish 127.0.0.1:5432:5432 \
  --env POSTGRES_USER=assistant \
  --env POSTGRES_PASSWORD=local-development-only \
  --env POSTGRES_DB=assistant \
  postgres:17

docker exec fastapi-ai-mcp-db pg_isready -U assistant -d assistant
```

Wait until PostgreSQL reports that it is accepting connections, then migrate and
start the API:

```bash
uv run alembic upgrade head
uv run uvicorn src.api.main:app --reload --host 127.0.0.1
```

Open [Swagger UI](http://localhost:8000/docs) or
[ReDoc](http://localhost:8000/redoc).

### First conversation

Use Swagger UI to:

1. Create an assistant with `POST /assistants/`, supplying `name`, `description`,
   `system_prompt`, and an available `model`. Set `mcp_command` and `mcp_args` to
   `null` to start without tools.
2. Create a chat with `POST /chats/`, supplying a `title`, an ISO-formatted
   `created_at`, and the returned `assistant_id`.
3. Send a message to `POST /chats/{chat_id}/completions` with `role: "user"`,
   `content`, and an ISO-formatted `date`. The endpoint streams plain text.

The completion path saves the incoming user message. It does not automatically
save the generated assistant response; persist that response through
`POST /chats/{chat_id}/message` if it should appear in later conversation history.
LLM requests require a valid provider key and may incur usage charges.

## MCP tools

MCP configuration belongs to each assistant record, through `mcp_command` and
`mcp_args`; it is not read from `MCP_SERVER_COMMAND` or `MCP_SERVER_ARGS`.

To use the included echo server, set these assistant fields while running the API
from the repository root:

```json
{
  "mcp_command": "uv",
  "mcp_args": ["run", "src/mcp/servers/example.py"]
}
```

The server declares its own dependencies through inline script metadata. Only
configure trusted MCP commands: they start local subprocesses with the API
process's privileges.

## Scope and limitations

This is a starter project. The current routes have no authentication or tenant
authorization, and CORS is configured for development. Add those application
boundaries and restrict tool configuration before exposing the service to
untrusted clients. PostgreSQL calls use synchronous SQLModel sessions.

The repository contains no Compose configuration, so the quick start uses
`docker run`. A Dockerfile is included, but database provisioning and migrations
are separate steps. No license file is currently included.

## Development

```bash
uv run pytest tests/test_llm_streaming.py
uv run pytest tests/test_mcp_tool.py
```

The streaming tests mock OpenAI. MCP tests check tool schema conversion; API tests
use Testcontainers and need Docker plus the settings required at app import.
Inspect those fixtures before running the full suite. The repository currently
has no GitHub Actions CI workflow.
