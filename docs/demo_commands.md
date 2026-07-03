# Copy-paste demo commands

Run all commands from the `clinical_trial_agent` directory.

## Local install and run

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The submitted `.env` has a blank key, so this starts in deterministic mock mode.

## Status and ingestion

```bash
curl -s http://localhost:8000/
curl -s http://localhost:8000/health
curl -s -X POST http://localhost:8000/ingest
```

## Protocol Q&A

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is the visit window for Visit 2?","use_memory":true,"debug":true}'
```

## Summarization

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Summarize the safety monitoring section.","use_memory":true,"debug":true}'
```

## Risk detection

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Analyze this protocol for operational risks.","use_memory":true,"debug":true}'
```

## Action plan

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Create an action plan for the CRA based on these risks.","use_memory":true,"debug":true}'
```

## Memory save and recall

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Remember that I prefer concise bullet points.","use_memory":true,"debug":true}'

curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What do you remember about my preferences?","use_memory":true,"debug":true}'

curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Based on my memory, answer in my preferred style: what are the inclusion criteria?","use_memory":true,"debug":true}'
```

## Direct memory endpoints

```bash
curl -s http://localhost:8000/memory
curl -s -X POST http://localhost:8000/memory \
  -H 'Content-Type: application/json' \
  -d '{"key":"user_role","value":"CRA"}'
curl -s -X DELETE http://localhost:8000/memory
```

## Tools and MCP

```bash
curl -s http://localhost:8000/tools
python -m app.mcp_server
```

The MCP command starts a stdio protocol server and waits for an MCP client.

## Tests

```bash
pytest -q
```

## Docker build and run

```bash
docker build -t clinical-trial-agent .
docker run --rm -p 8000:8000 --env-file .env clinical-trial-agent
```

In another terminal:

```bash
curl -s -X POST http://localhost:8000/ingest
curl -s http://localhost:8000/health
```
