# Final Q&A cheat sheet

## 1. Why is this agentic AI and not just a chatbot?

It classifies intent, selects tools, uses memory and retrieval when relevant,
and sequences multiple tools for action plans. It also reports the plan, tools,
sources, and memory used.

## 2. Why is this not only RAG?

RAG retrieves document evidence. The system also plans workflows, calls domain
tools, detects risks, creates actions, persists user memory, and exposes tools
through MCP.

## 3. Where is persona design implemented?

In `app/prompts.py`. It defines the Clinical Trial Operations Assistant, its
professional tone, grounding rules, practical next-step behavior, and
medical-decision boundary.

## 4. Where is tool use implemented?

In `app/tools.py`. The tools cover protocol search, section summary, risk
detection, action planning, memory save, memory recall, and capability listing.

## 5. Where is MCP implemented?

In `app/mcp_server.py`. FastMCP registers six study and memory tools for
standard discovery and invocation over stdio.

## 6. Why does FastAPI call tools directly if MCP exists?

They are in the same Python process, so direct calls remove an unnecessary
transport dependency and make the live demo reliable. MCP wraps the exact same
functions for external clients, so there is still one implementation.

## 7. How does the planner decide which tool to use?

`ClinicalTrialAgent._classify_intent` maps memory, capabilities, action-plan,
risk, summary, and Q&A requests to bounded workflows. Action planning
deliberately runs risk detection first.

## 8. How does RAG work in this project?

It loads `.txt` files, creates overlapping chunks, embeds them, atomically
persists vectors and metadata, then ranks query matches using vector similarity
plus exact terms and a minimum relevance threshold.

## 9. How is memory different from RAG?

Memory stores user preferences and durable context in SQLite. RAG stores study
document knowledge. Memory may change presentation, but protocol facts must
come from retrieved documents.

## 10. What happens if the document does not contain the answer?

If the index is missing, the agent asks the user to run `/ingest`. If the index
exists but no evidence clears the relevance threshold, it explicitly says no
relevant information was found.

## 11. How do you reduce hallucination?

Grounding rules, deterministic extraction, source labels, minimum retrieval
scores, separation of memory from facts, and constrained LLM prompts. These
reduce hallucination but do not replace human review.

## 12. Why did you use FastAPI?

It provides typed validation, generated Swagger/OpenAPI documentation, simple
testing, clear endpoint contracts, and a practical deployment path.

## 13. Why did you use Docker?

Docker fixes the Python runtime and dependencies, runs as a non-root user, adds
a health check, and makes the application reproducible on another machine.

## 14. What is mock mode?

Mock mode is the deterministic no-key path. RAG, tools, planning, risks,
actions, and SQLite memory still run normally; only optional LLM rewriting is
skipped.

## 15. What are the limitations?

Synthetic text only, a small local vector index, lexical default embeddings,
rule-based risk coverage, no authentication, and no regulated audit trail or
GxP validation.

## 16. How would you make it production-ready?

Add controlled document versions, PDF/table parsing, enterprise vector
storage, SSO/RBAC, encryption, tenant isolation, audit trails, observability,
backups, and human approval gates.

## 17. How would you validate this for real clinical use?

Build labelled retrieval and Q&A datasets, measure retrieval precision and
unsupported claims, validate every cited statement, test known risks, run
regression and security evaluations, and require clinical operations and
quality approval under change control.

## 18. What would you improve with more time?

Add document-version filters, semantic embeddings, table-aware visit extraction,
CTMS/EDC/eTMF connectors, human approval workflows, structured evaluations,
and authenticated study-specific workspaces.
