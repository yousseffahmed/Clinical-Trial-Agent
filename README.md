# Clinical Trial Protocol & Risk Assistant Agent

A complete, local-first Agentic AI capstone project for clinical trial
operations. It answers grounded document questions, summarizes protocol
sections, detects operational risks, creates accountable action plans, remembers
user preferences, exposes MCP tools, and runs with FastAPI or Docker.

**Examiner summary:** this is an inspectable agent workflow, not a single-prompt
chatbot. Every chat response reports the bounded plan, tools invoked, document
sources retrieved, and user memories applied. The full demonstration works with
the submitted blank API key.

## Capstone Submission Notes

- Submit the complete `clinical_trial_agent` folder.
- Do **not** compress the folder into ZIP, RAR, TAR, or another archive.
- Do **not** upload presentation slides to Google Classroom.
- The submitted `.env` is included with `OPENAI_API_KEY=` intentionally blank.
- Run `python scripts/clean_submission.py` immediately before submission.
- Use `docs/clinical_trial_agent_presentation.pptx` only during the live
  capstone discussion.

All bundled study content is fictional. This project is an educational
prototype, not a validated GxP system and not a medical decision-support tool.

## Features

- Protocol, SOP, and visit-schedule Q&A with chunk-level sources.
- Grounded extractive summaries.
- Transparent risk detection with evidence, severity, impact, and mitigation.
- Multi-tool CRA action-plan generation with owners and timelines.
- SQLite preference/fact memory with save, search, list, and clear operations.
- Short public plan summaries without private chain-of-thought.
- A real FastMCP stdio tool server.
- Optional OpenAI Responses API refinement.
- Deterministic mock mode when no API key is present or an API call fails.
- Persisted local vector index with offline and sentence-transformer backends.
- Typed FastAPI endpoints, Swagger UI, tests, Docker, and demo documentation.

## Architecture

```text
Client -> FastAPI -> Agent planner -> Tools -> RAG vector index -> data/*.txt
                         |             |
                         |             +----> SQLite memory
                         |
                         +---- optional grounded OpenAI response

MCP client -> FastMCP server -> same Tools
```

See [docs/architecture.md](docs/architecture.md) for components, data flow, and
deployment details.

## Course concept mapping

| Course requirement | Implementation |
|---|---|
| Persona design | `app/prompts.py` defines the Clinical Trial Operations Assistant, tone, grounding rules, recommendations boundary, and no-medical-advice rule. |
| Tool use | `app/tools.py` implements protocol search, summary, risk, plan, memory, and capability tools with typed, serializable outputs. |
| MCP | `app/mcp_server.py` registers six functions with FastMCP so external MCP clients can discover and invoke them. |
| Agent reasoning/planning | `app/agent.py` classifies intent, selects tools, sequences risk → action plan, uses memory, and returns a safe `plan_summary`. |
| RAG and memory | `app/rag.py` chunks, embeds, persists, and retrieves source documents. `app/memory.py` persists user preferences in SQLite. |
| Docker | `Dockerfile` creates a non-root Python 3.11 service with health check; Compose mounts persistent state. |

## Project structure

```text
clinical_trial_agent/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── agent.py
│   ├── config.py
│   ├── schemas.py
│   ├── rag.py
│   ├── memory.py
│   ├── tools.py
│   ├── mcp_server.py
│   ├── prompts.py
│   └── logger.py
├── data/
│   ├── sample_protocol.txt
│   ├── sample_sop.txt
│   └── sample_visit_schedule.txt
├── memory/
│   └── .gitkeep
├── vector_store/
│   └── .gitkeep
├── tests/
│   ├── test_tools.py
│   ├── test_memory.py
│   ├── test_rag.py
│   ├── test_agent.py
│   └── test_mcp.py
├── docs/
│   ├── architecture.md
│   ├── demo_commands.md
│   ├── demo_script.md
│   ├── presentation_speaker_notes.md
│   ├── qna_preparation.md
│   └── presentation_outline.md
├── scripts/
│   └── clean_submission.py
├── SUBMISSION_CHECKLIST.md
├── Makefile
├── requirements.txt
├── pytest.ini
├── Dockerfile
├── docker-compose.yml
├── .env
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md
```

## Local setup

Python 3.10 or newer is recommended (the Docker image uses 3.11). From this
directory, run the exact capstone setup:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open:

- API: <http://localhost:8000>
- Swagger UI: <http://localhost:8000/docs>
- Health: <http://localhost:8000/health>

The vector index is intentionally not committed. Build it once after startup:

```bash
curl -X POST http://localhost:8000/ingest
```

Run tests:

```bash
pytest -q
```

## Configuration and model modes

The submitted `.env` intentionally contains `OPENAI_API_KEY=` with no value.
Keep it empty for mock mode. Mock mode still performs real local ingestion,
vector retrieval, risk analysis, planning, and memory; only final generative
rewriting is skipped.

To enable LLM mode:

```dotenv
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
```

The Python client uses the Responses API. API failures are logged and return
the deterministic grounded answer instead of failing the demo. For this
assignment, submit the provided blank `.env`; never place or submit a real key
in it.

If asked during the demo why no key is configured, say:

> The API key is deliberately blank for secure submission. The complete
> agent workflow—RAG, tools, risk detection, planning, sources, and SQLite
> memory—runs deterministically without paid API access. A valid key only
> enables optional grounded answer rewriting.

Embedding options:

```dotenv
EMBEDDING_BACKEND=hash
```

`hash` is fully offline and deterministic. For stronger semantic retrieval,
install the optional backend:

```bash
pip install "sentence-transformers>=3.4,<6.0"
```

Then configure:

```dotenv
EMBEDDING_BACKEND=sentence-transformers
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
```

It is optional because it pulls a large ML runtime. The model may download on
first use. Run `/ingest` after changing the embedding backend or model.

## Docker setup

Required commands:

```bash
cp .env.example .env
docker build -t clinical-trial-agent .
docker run -p 8000:8000 --env-file .env clinical-trial-agent
```

The exact `docker run` command uses container-local state. For state that
survives container replacement, use Compose:

```bash
docker compose up --build
curl -X POST http://localhost:8000/ingest
```

Compose mounts `memory/` and `vector_store/` as persistent writable volumes and
mounts `data/` read-only.

## API

### `GET /`

Returns project name, running status, and `mock` or `llm` mode.

```bash
curl http://localhost:8000/
```

### `GET /health`

Returns service health, whether RAG is ready, and whether LLM mode is enabled.

```bash
curl http://localhost:8000/health
```

### `POST /ingest`

Rebuilds the vector index from every `.txt` file under `data/`.

```bash
curl -X POST http://localhost:8000/ingest
```

### `POST /chat`

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{
    "message": "What is the visit window for Visit 2?",
    "use_memory": true,
    "debug": true
  }'
```

Response shape:

```json
{
  "answer": "...",
  "plan_summary": "...",
  "tools_used": ["search_protocol"],
  "retrieved_sources": ["sample_visit_schedule.txt#chunk-2"],
  "memory_used": []
}
```

`plan_summary` is a bounded execution summary, not chain-of-thought.

### Memory endpoints

Save manually:

```bash
curl -X POST http://localhost:8000/memory \
  -H 'Content-Type: application/json' \
  -d '{"key":"user_role","value":"CRA"}'
```

List:

```bash
curl http://localhost:8000/memory
```

Clear:

```bash
curl -X DELETE http://localhost:8000/memory
```

### `GET /tools`

```bash
curl http://localhost:8000/tools
```

Returns the registered local tool catalog.

## Demo commands

Run ingestion before the first question:

```bash
curl -X POST http://localhost:8000/ingest
```

Protocol Q&A:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What are the inclusion criteria?","use_memory":true,"debug":true}'
```

Visit activity:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What should happen during Screening?","use_memory":true,"debug":true}'
```

Summary:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Summarize the safety monitoring section.","use_memory":true,"debug":true}'
```

Risk analysis:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Analyze this protocol for operational risks.","use_memory":true,"debug":true}'
```

Action plan:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Create an action plan for the CRA based on these risks.","use_memory":true,"debug":true}'
```

Memory:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Remember that I prefer concise bullet points.","use_memory":true,"debug":true}'

curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What do you remember about my preferences?","use_memory":true,"debug":true}'
```

See [docs/demo_script.md](docs/demo_script.md) for the timed presentation.
Use [docs/demo_commands.md](docs/demo_commands.md) for copy-paste commands and
[docs/presentation_speaker_notes.md](docs/presentation_speaker_notes.md) for the
10-minute narration.

## MCP usage

Start the stdio server from the project root:

```bash
source venv/bin/activate
python -m app.mcp_server
```

Example MCP client configuration:

```json
{
  "mcpServers": {
    "clinical-trial-tools": {
      "command": "/absolute/path/clinical_trial_agent/venv/bin/python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "/absolute/path/clinical_trial_agent"
    }
  }
}
```

If `No module named mcp` appears, activate the project environment and rerun
`pip install -r requirements.txt`. MCP runs over stdio, so normal server
protocol messages are written to stdout; application logs should remain on
stderr.

## File guide

| File | Responsibility |
|---|---|
| `app/main.py` | FastAPI application and required endpoints. |
| `app/agent.py` | Intent classification, tool planning, memory selection, LLM fallback, answer formatting. |
| `app/config.py` | Environment settings and safe project-relative paths. |
| `app/schemas.py` | API validation and response models. |
| `app/rag.py` | Document loading, chunking, embeddings, persisted vector search. |
| `app/memory.py` | SQLite schema and memory CRUD/search. |
| `app/tools.py` | Shared RAG, summary, risk, action, and memory tools. |
| `app/mcp_server.py` | Standardized FastMCP tool server. |
| `app/prompts.py` | Persona and LLM grounding instructions. |
| `app/logger.py` | Consistent application logging. |
| `data/*.txt` | Synthetic protocol, SOP, and visit schedule. |
| `tests/*.py` | Unit tests for memory, RAG, and tool output. |
| `docs/architecture.md` | Component and data-flow design. |
| `docs/demo_script.md` | Timed 10-minute live demo. |
| `docs/demo_commands.md` | Copy-paste local, API, MCP, and Docker commands. |
| `docs/presentation_outline.md` | Required three-slide outline. |
| `docs/presentation_speaker_notes.md` | Slide-aligned 10-minute script. |
| `docs/qna_preparation.md` | Expected defense questions and concise answers. |
| `SUBMISSION_CHECKLIST.md` | Submit/exclude list and final verification. |
| `scripts/clean_submission.py` | Removes runtime artifacts while preserving source and blank environment files. |
| `Makefile` | Shortcuts for install, test, run, ingest, Docker, and cleanup. |
| `pytest.ini` | Stable test discovery and project import path. |
| `.gitignore` | Excludes virtual environments, caches, and generated runtime state. |
| `.dockerignore` | Keeps local state and the submitted `.env` out of image build context. |
| `Dockerfile` | Reproducible non-root API image. |
| `docker-compose.yml` | Persistent local deployment. |

## Troubleshooting

### Chat says to run `/ingest`

The index is absent or empty. Run:

```bash
curl -X POST http://localhost:8000/ingest
curl http://localhost:8000/health
```

### Search returns no results after changing embedding backend

Stored and query vectors must use the same backend. Delete only the generated
index if needed, then call ingestion again:

```bash
rm -f vector_store/protocol_index.json
curl -X POST http://localhost:8000/ingest
```

### Sentence-transformer startup is slow

The first run may download a model and uses significantly more memory. Use
`EMBEDDING_BACKEND=hash` for the guaranteed offline capstone demo.

### OpenAI request fails

Check the key, model access, network, and logs. The request should still return
a deterministic result. Remove the key to explicitly use mock mode.

### Docker cannot write memory or vector store

Ensure the host directories exist and are writable by the container user, or
first run the non-Compose command to verify the image.

### Port 8000 is already used

Run Uvicorn on another port or map another host port:

```bash
uvicorn app.main:app --reload --port 8001
docker run -p 8001:8000 --env-file .env clinical-trial-agent
```

## Demo flow

1. Start the API and show `/health`.
2. Call `/ingest` and show document/chunk counts.
3. Ask about Visit 2 and point to retrieved sources.
4. Summarize withdrawal or safety rules.
5. Detect operational risks and inspect evidence.
6. Generate the CRA action plan.
7. Save a concise-output preference and show `memory_used`.
8. Show `/tools`, the MCP file, tests, and Docker configuration.

## Q&A preparation notes

Be ready to explain:

- The planner and multi-tool sequence make this agentic; an LLM alone does not.
- MCP standardizes tool discovery and invocation independently of FastAPI.
- RAG stores document evidence; memory stores user preferences. They are
  intentionally separate.
- Grounding, source labels, deterministic fallback, and explicit absence
  messages reduce unsupported claims but do not guarantee correctness.
- A production regulated system needs validation, RBAC, tenant isolation,
  encryption, audit trails, document-version control, and human approvals.

Full answers are in [docs/qna_preparation.md](docs/qna_preparation.md).

## Submission contents

Submit the source tree directly, including `app/`, `data/`, `docs/`, `tests/`,
`scripts/`, Docker files, requirements, README, Makefile, `.env` with a blank
key, and `.env.example`. Keep `.gitkeep` in the empty runtime directories.

Before submission:

```bash
python scripts/clean_submission.py
```

Do not submit:

- `venv/`, `.venv/`, `__pycache__/`, `.pytest_cache/`, or `*.pyc`
- `memory/*.db` or generated `vector_store/` content
- real credentials or confidential study material
- ZIP/RAR/TAR or another compressed archive
- documentation containing a personal absolute filesystem path
- presentation slides to Google Classroom when the assignment says not to

See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md) for the final sign-off.

## Known limitations

- Synthetic text only; no PDF/DOCX or table-specific parser.
- The default hash embedder prioritizes offline reliability over semantic depth.
- Rule-based risks are inspectable but do not cover every protocol ambiguity.
- No authentication, user/study isolation, regulated audit trail, or e-signature.
- SQLite is suitable for a single-node demo, not concurrent enterprise scale.
- LLM output still requires human verification against approved documents.
# Clinical-Trial-Agent
