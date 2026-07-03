# Three-slide presentation

## Slide 1 — Problem and solution

**Title:** Clinical Trial Protocol & Risk Assistant

**Problem**

- Protocol requirements are spread across long protocols, visit schedules, and
  SOPs.
- Manual searching is slow and can miss unclear windows, responsibilities,
  safety escalation rules, or participant-burden concerns.

**Solution**

- A grounded operations assistant for protocol Q&A, section summaries,
  evidence-backed risk detection, CRA action plans, and remembered user
  preferences.
- Synthetic data and mock mode make the demonstration safe and reliable.

**Speaker takeaway:** “The goal is not another chatbot. It converts controlled
study documents into traceable operational answers and actions.”

**Suggested visual:** Documents → Assistant → sourced answer / risk register /
owned CRA action.

## Slide 2 — Architecture

**Title:** Inspectable agent workflow with standardized tools

```text
User → FastAPI → Agent Planner → Memory → RAG → Tools → Final Answer
                           ↘ plan summary + sources ↗

MCP client → FastMCP server → the same tool functions
```

- FastAPI validates requests and exposes the demo API.
- The planner classifies intent and chooses a bounded tool sequence.
- SQLite stores user preferences; it is separate from protocol knowledge.
- Local vector retrieval supplies source-labelled document chunks.
- Tools implement search, summary, risk, plan, save, and recall capabilities.
- The optional OpenAI layer rewrites grounded output; mock mode remains fully
  functional without a key.
- Docker supplies a reproducible Python 3.11 runtime.

**Speaker takeaway:** “Every answer exposes the plan, tools, sources, and memory
used, so behavior is inspectable.”

## Slide 3 — Demo and course mapping

**Title:** From document evidence to accountable action

**Live flow**

1. Ingest three synthetic study documents.
2. Ask for the Visit 2 window and inspect sources.
3. Summarize safety monitoring.
4. Detect operational risks with evidence, impact, and mitigation.
5. Generate an owned, timed CRA action plan.
6. Save a concise-output preference and reuse it.

**Course requirements**

| Persona | Tools | MCP | Planning | RAG + memory | Docker |
|---|---|---|---|---|---|
| Domain role and safety rules | Typed capabilities | Standard external interface | Intent routing and multi-tool workflow | Grounded facts plus preferences | Reproducible deployment |

**Boundary:** Educational synthetic-data prototype; not validated for GxP use
and never a replacement for investigator or Medical Monitor judgment.
