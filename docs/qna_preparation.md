# Examiner Q&A preparation

## Why is this agentic and not just RAG?

RAG is one capability inside the system. The agent first classifies intent,
selects a workflow, decides whether memory or retrieval is relevant, invokes
one or more typed tools, and formats the result with execution metadata. An
action-plan request sequences risk detection before planning. A plain RAG
application would retrieve text and answer; it would not manage these distinct
actions and state.

## Where exactly is MCP used?

`app/mcp_server.py` creates a FastMCP server and registers six functions:
protocol search, section summary, risk detection, action planning, memory save,
and memory recall. An MCP client can launch `python -m app.mcp_server`,
discover their schemas, and invoke them over stdio.

## Why keep direct tool calls inside FastAPI if MCP exists?

MCP is the standardized external interface, not a requirement to add a
transport hop inside one Python process. FastAPI imports the same underlying
functions directly for lower latency and a reliable offline demo. FastMCP wraps
those exact functions for external clients. This keeps one source of business
logic while demonstrating both local orchestration and interoperable tools.

## How does the planner decide tools?

`ClinicalTrialAgent._classify_intent` uses transparent intent rules for memory,
capabilities, action plans, risks, summaries, and protocol questions. Each
intent maps to the smallest workflow. Action plans use two tools; ordinary Q&A
uses only search. The response reports this choice in `tools_used` and a
high-level `plan_summary`.

## How does memory differ from RAG?

Memory stores user-specific preferences and durable facts such as role, output
format, and study focus in SQLite. RAG stores document chunks and embeddings
for protocol evidence. Memory can change presentation but must never establish
a protocol fact. RAG can establish a sourced study fact but should not infer a
user preference.

## How does RAG work?

Ingestion loads `.txt` files, builds overlapping paragraph-aware chunks,
embeds each chunk, and atomically persists vectors and metadata. Query-time
ranking combines cosine similarity with an exact-term signal and a minimum
relevance threshold. Returned chunks include source file, chunk ID, preview,
text, and score.

## What prevents hallucination?

- The persona forbids unsupported protocol facts.
- Deterministic mode extracts evidence directly from retrieved chunks.
- A relevance threshold rejects weak matches.
- Source file and chunk IDs are returned.
- LLM mode receives structured tool output and grounding instructions.
- Memory is explicitly prohibited from acting as protocol evidence.

These controls reduce hallucination; human review remains required.

## What happens if documents do not contain the answer?

If the index is missing, the response instructs the user to run `/ingest`. If
the index exists but no chunk clears the relevance threshold, it states that no
relevant information was found. It does not fabricate a protocol answer.

## What happens if retrieved context is wrong?

The answer may still be wrong or incomplete. Production controls should filter
by approved document version, expose links to authoritative source locations,
evaluate retrieval against a labelled question set, and require review for
critical actions.

## Why FastAPI?

FastAPI gives typed validation, generated OpenAPI/Swagger documentation, clear
endpoint boundaries, simple testing, and a straightforward deployment path.

## Why Docker?

Docker fixes the Python runtime and dependencies, runs as a non-root user, adds
a health check, and makes examiner and developer environments reproducible.

## What happens without an OpenAI API key?

The application reports mock mode and continues to perform real ingestion,
vector retrieval, summaries, risk analysis, action planning, and SQLite
memory. Only optional generative rewriting is skipped. An API failure also
falls back to deterministic output.

## How would this become production-ready?

- Add PDF/DOCX and table-aware parsing with document/version governance.
- Use an enterprise vector store with study and approval-status filters.
- Add SSO/RBAC, tenant isolation, encryption, audit trails, retention controls,
  backups, and observability.
- Add human approval gates before creating or closing operational actions.
- Integrate governed CTMS, EDC, eTMF, and safety-system APIs.
- Establish validated deployment, change control, incident management, and
  model/retrieval monitoring.

## What are the security limitations?

The prototype has no authentication, authorization, tenant separation,
rate-limiting, secrets manager, encryption policy, or tamper-evident audit
trail. SQLite and the local index are plaintext files. It must not process
personal health information or confidential sponsor documents as deployed.

## What are the clinical and GxP limitations?

This is not a validated computerized system, does not implement Part 11
controls, does not preserve regulated audit signatures, and has no approved
clinical decision logic. It cannot replace the investigator, Medical Monitor,
approved protocol, safety database, or sponsor quality process.

## How can outputs be validated?

- Create labelled Q&A and retrieval datasets with expected source sections.
- Measure retrieval precision/recall and unsupported-claim rate.
- Compare every generated statement with its cited chunk.
- Build risk-detection recall tests for known seeded gaps.
- Run regression tests on each prompt, model, rule, and document-parser change.
- Have clinical operations and quality reviewers approve acceptance criteria.
- Record failures and require human approval for consequential actions.

## Why use transparent risk rules?

They are inspectable, deterministic, source-linked, and easy to demonstrate.
They are not exhaustive. A production system could combine controlled rules
with model-assisted review and mandatory human confirmation.

## Is the plan summary chain-of-thought?

No. It reports only workflow actions such as retrieve evidence, detect risks,
and assign owners. It does not reveal private model deliberation.
