# Final live demo commands

Run commands from the `clinical_trial_agent` directory. Keep two terminal
windows open: one for the server and one for `curl`.

## 1. Start the app locally

Say:

> I am starting the FastAPI service with the submitted blank API key, so it
> will run in deterministic mock mode.

Command:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Expected result:

```text
Uvicorn running on http://127.0.0.1:8000
Application startup complete.
```

## 2. Open Swagger UI

Say:

> FastAPI automatically exposes interactive API documentation. This also makes
> the endpoint contracts easy for an examiner or another client to inspect.

URL:

<http://localhost:8000/docs>

macOS command:

```bash
open http://localhost:8000/docs
```

Expected result: Swagger UI lists `/`, `/health`, `/chat`, `/ingest`,
`/memory`, and `/tools`.

## 3. Ingest documents

Say:

> First I will ingest the synthetic protocol, SOP, and visit schedule into the
> local vector index.

```bash
curl -s -X POST http://localhost:8000/ingest
```

Expected result: status `success`, `documents: 3`, approximately 16 chunks,
embedding backend `hash`, and three source filenames.

## 4. Health check

Say:

> I will confirm the API is healthy, RAG is ready, and no LLM key is required.

```bash
curl -s http://localhost:8000/health
```

Expected result:

```json
{"status":"healthy","rag_ready":true,"llm_enabled":false}
```

## 5. List tools

Say:

> These are the explicit tools available to the planner. The system is not one
> large prompt.

```bash
curl -s http://localhost:8000/tools
```

Expected result: seven local capabilities, including protocol search, summary,
risk detection, action planning, memory save, and memory recall.

## 6. Ask the Visit 2 question

Say:

> I will ask a factual question whose answer must come from the documents.

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is the visit window for Visit 2?","use_memory":true,"debug":true}'
```

Expected result: Day 28, plus or minus 3 days; tool
`search_protocol`; protocol and visit-schedule source chunks.

Point out:

- `plan_summary`
- `tools_used`
- `retrieved_sources`

## 7. Summarize safety monitoring

Say:

> Next I will ask for a grounded summary rather than a raw document dump.

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Summarize the safety monitoring section.","use_memory":true,"debug":true}'
```

Expected result: monitoring at post-Baseline contacts, scheduled laboratory
testing, ECG requirements, and escalation ambiguity, with protocol sources.

## 8. Detect operational risks

Say:

> Now the agent will inspect the indexed evidence for operational risk
> indicators and explain why each one matters.

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Analyze this protocol for operational risks.","use_memory":true,"debug":true}'
```

Expected result: evidence-backed risks such as the undefined follow-up window,
incomplete safety escalation thresholds, data-transcription risk, participant
burden, and unclear responsibility.

## 9. Generate the CRA action plan

Say:

> I will convert the risks into owned, timed actions. This deliberately uses a
> two-tool workflow.

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Create an action plan for the CRA based on these risks.","use_memory":true,"debug":true}'
```

Expected result: a table with priority, owner, action, timeline, and expected
outcome. `tools_used` contains both risk detection and action planning.

## 10. Save memory

Say:

> I will save a durable answer-style preference in local SQLite memory.

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Remember that I prefer concise bullet points.","use_memory":true,"debug":true}'
```

Expected result: `answer_style` is saved locally.

## 11. Recall and use the preferred style

Say:

> I will first show that the preference persisted, and then reuse it while
> answering a protocol question.

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What do you remember about my preferences?","use_memory":true,"debug":true}'
```

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Based on my memory, answer in my preferred style: what are the inclusion criteria?","use_memory":true,"debug":true}'
```

Expected result: concise inclusion-criteria evidence and
`memory_used: ["answer_style=I prefer concise bullet points"]`.

Point out: memory affects style; retrieved documents still provide the facts.

## 12. Build the Docker image

Say:

> Docker packages the tested runtime so the examiner does not depend on my
> local Python setup.

Stop the local Uvicorn process first, then run:

```bash
docker build -t clinical-trial-agent .
```

Expected result:

```text
Successfully tagged clinical-trial-agent:latest
```

## 13. Run the Docker container

Say:

> I will run the same application in the container with the blank submitted
> environment file.

```bash
docker run --rm -p 8000:8000 --env-file .env clinical-trial-agent
```

Expected result: Uvicorn starts on `0.0.0.0:8000`; `/` reports mode `mock`.

In a second terminal:

```bash
curl -s -X POST http://localhost:8000/ingest
curl -s http://localhost:8000/health
```

Expected result: ingestion succeeds and `rag_ready` becomes `true`.

## Emergency fallback

If the terminal display is difficult to read, use Swagger UI at
<http://localhost:8000/docs>. The full demo does not require an API key or
network access after dependencies are installed.
