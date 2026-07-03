# Presentation speaker notes — 10 minutes

## 0:00–1:00 — Project idea

“Clinical trial operations teams work across protocols, visit schedules, and
SOPs. The facts exist, but finding and translating them into operational action
is slow. Small ambiguities can become deviations, delayed safety escalation,
or missing data.

This capstone is a Clinical Trial Protocol & Risk Assistant. It answers sourced
questions, summarizes sections, detects seeded operational risks, generates
owned action plans, and remembers how the user prefers to work. All documents
are synthetic, and the assistant does not make medical decisions.”

Show Slide 1.

## 1:00–3:00 — Architecture

Show Slide 2 and say:

“FastAPI is the contract layer. The agent planner classifies each request and
chooses the smallest tool workflow. Protocol facts come from local RAG:
documents are chunked, embedded, persisted, and retrieved with source
metadata. User preferences are separate in SQLite memory.

The tools are ordinary typed Python functions. FastAPI calls them directly for
offline reliability. The FastMCP server exposes the same functions to external
MCP clients, so there is one implementation and two interfaces.

If a key is configured, the OpenAI Responses API can improve the final wording
using only grounded tool output. With a blank key, deterministic mode still
demonstrates every required capability. Docker provides a reproducible,
non-root Python runtime.”

Point to `plan_summary`, `tools_used`, `retrieved_sources`, and `memory_used`.

## 3:00–8:00 — Live demo

Use `docs/demo_commands.md`.

1. Call `/health`; explain `rag_ready=false` is expected before ingestion.
2. Call `/ingest`; show three documents, chunk count, and `hash` backend.
3. Ask for the Visit 2 window. Read the ±3-day result and show both source file
   and chunk identifier.
4. Summarize safety monitoring. Show extractive facts and sources.
5. Analyze operational risks. Pick the missing follow-up window and explain the
   evidence → impact → recommendation structure.
6. Generate the CRA action plan. Show owner, priority, timeline, and expected
   outcome.
7. Save “I prefer concise bullet points.”
8. Ask the inclusion-criteria question using the stored preference. Show
   `memory_used` while emphasizing that memory changes style, not study facts.

If anything involving an API key is asked, say:

“The assignment `.env` deliberately has a blank key. The application is in
mock mode, but retrieval, tools, planning, risks, and memory are real. Adding a
valid key enables optional grounded rewriting; it is not needed for this demo.”

## 8:00–10:00 — Course concepts

Show Slide 3 and say:

“Persona design appears in the clinical-operations role, grounding behavior,
tone, and safety boundaries. Tool use appears as structured search, summary,
risk, action, and memory functions. MCP exposes six of those functions through
a standard interface.

Reasoning and planning are demonstrated by intent routing and the two-step
risk-to-action workflow. RAG provides sourced protocol knowledge, while SQLite
stores separate user memory. Docker packages the tested service.

The main limitations are intentional: synthetic text, a small local vector
store, transparent but incomplete risk rules, and no production security or
GxP validation. Production readiness would require document governance, RBAC,
audit trails, evaluation datasets, human approvals, and validated change
control.”

End on the passing test result and `/docs` Swagger page.
