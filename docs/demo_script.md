# 10-minute live demo script

## 0:00–1:00 — Problem

- Clinical operations teams repeatedly search long protocols, visit schedules,
  and SOPs under time pressure.
- Small ambiguities can cause deviations, inconsistent site behavior, delayed
  escalation, or avoidable participant burden.
- This assistant grounds answers in study documents, identifies operational
  risks, remembers how the user works, and converts findings into actions.
- State clearly that all bundled content is synthetic and the assistant does
  not make medical decisions.

## 1:00–3:00 — Architecture

- Show the diagram in `docs/architecture.md`.
- Explain FastAPI as the user interface and contract layer.
- Explain that the planner selects tools rather than sending every request to a
  single chatbot prompt.
- Show local chunk embeddings and source metadata in the vector index.
- Show SQLite memory and the separate standardized MCP interface.
- Mention deterministic mock mode and optional OpenAI answer refinement.

## 3:00–8:00 — Live demo

Start from a clean running service:

```bash
curl -X POST http://localhost:8000/ingest
```

1. Protocol Q&A:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What is the visit window for Visit 2?","use_memory":true,"debug":true}'
```

Point out the retrieved source and `search_protocol` tool.

2. Summarization:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Summarize the subject withdrawal rules.","use_memory":true,"debug":true}'
```

Point out extractive key points and source labels.

3. Risk detection:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Analyze this protocol for operational risks.","use_memory":true,"debug":true}'
```

Discuss evidence, impact, severity, and recommendation.

4. Action planning:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Create an action plan for the CRA based on these risks.","use_memory":true,"debug":true}'
```

Highlight owners and timelines.

5. Memory:

```bash
curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"Remember that I prefer concise bullet points.","use_memory":true,"debug":true}'

curl -s http://localhost:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"message":"What are the inclusion criteria?","use_memory":true,"debug":true}'
```

Point out `memory_used` and the more concise response.

## 8:00–10:00 — Course concept mapping

- Persona: domain role, tone, grounding rules, and medical-decision boundary.
- Tool use: seven explicit, reusable functions with structured results.
- MCP: FastMCP exposes the same core tools to any compatible client.
- Reasoning/planning: intent classification and bounded multi-tool sequences,
  with a safe `plan_summary`.
- RAG and memory: local embeddings and source metadata plus separate SQLite
  user preferences.
- Docker: reproducible non-root runtime, health check, and persistent volumes.

End by showing `/docs`, `/health`, and the passing test command.
