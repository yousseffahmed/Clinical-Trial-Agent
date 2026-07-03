# Final 10-minute presentation script

This is written to be spoken word-for-word. Keep the terminal and Swagger UI
open before the discussion starts.

## 0:00–1:00 — Opening and project idea

“Good morning. My project is the Clinical Trial Protocol and Risk Assistant
Agent.

Clinical trial operations teams work with long protocols, visit schedules, and
standard operating procedures. The information is available, but the team
often needs it quickly: What are the inclusion criteria? What is the visit
window? Is there an operational gap? Who should act, and by when?

My solution is an agentic AI assistant that turns controlled study documents
into sourced answers and practical actions. It can answer protocol questions,
summarize sections, detect operational risks, generate a CRA action plan, and
remember how the user prefers the answer.

This is not a medical decision system. The included documents are synthetic,
and the assistant supports operations without replacing the investigator,
Medical Monitor, or approved protocol.

The key design principle is traceability. Every response shows the plan, tools
used, retrieved sources, and memory used.”

Move to Slide 2.

## 1:00–3:00 — Architecture

“The architecture starts with FastAPI. It provides typed endpoints for chat,
ingestion, memory, tools, and health.

The request then reaches the agent planner. The planner classifies the user’s
intent. A protocol question uses the search tool. A summary request uses the
summary tool. A risk request uses risk detection. An action-plan request first
detects risks and then passes those risks to the planning tool.

Memory and RAG are separate by design. SQLite memory stores user preferences,
such as role, concise style, or output format. RAG stores study knowledge. A
memory can change how I present an answer, but it cannot establish a protocol
fact.

During ingestion, the RAG service loads the text files, creates overlapping
chunks, embeds them, and stores vectors with source file and chunk metadata.
At query time, it retrieves the most relevant evidence and rejects weak
matches.

The tool layer contains protocol search, summary, risk detection, action
planning, memory save, and memory recall.

FastAPI calls these Python functions directly for a reliable local demo. The
FastMCP server exposes the same functions through the standardized Model
Context Protocol. This gives one implementation with both local and external
tool interfaces.

Finally, Docker packages the API, tools, data, memory, and vector store into a
reproducible runtime.

The OpenAI layer is optional. With a valid key it can improve the final wording
using grounded tool output. With the submitted blank key, deterministic mock
mode still demonstrates the complete agent workflow.”

Move to Slide 3 and the terminal.

## 3:00–8:00 — Live demo

### Ingest

Say:

“First, I will ingest the three synthetic study documents. This creates the
local vector index.”

Run the `/ingest` command from `docs/final_live_demo_commands.md`.

Then say:

“The response confirms three documents, sixteen chunks, the local hash
embedding backend, and all three source filenames.”

### Health and tools

Say:

“Next, I will confirm that the service is healthy and that RAG is ready.”

Run the health command.

Then say:

“The service is healthy, `rag_ready` is true, and `llm_enabled` is false. That
means the demo is running successfully without an API key.”

Run the tools command and say:

“This endpoint exposes the explicit capabilities available to the planner.
These are structured tools, not one large chatbot prompt.”

### Protocol Q&A

Say:

“Now I will ask a factual protocol question: What is the visit window for Visit
2?”

Run the Visit 2 command.

Then say:

“The answer identifies Day 28 with a plus-or-minus three-day window. I can also
see that the planner selected `search_protocol`, and the answer includes source
file and chunk identifiers.”

### Summarization

Say:

“Next, I will request a summary of the safety monitoring section.”

Run the summary command.

Then say:

“The summary is extractive and grounded. It identifies adverse-event review,
laboratory timing, ECG requirements, and the safety escalation gap, all linked
to the protocol source.”

### Risk detection

Say:

“Now I will ask the agent to analyze the protocol for operational risks.”

Run the risk command.

Then say:

“Each risk has four parts: the risk, severity, document evidence, operational
impact, and recommended action. For example, the follow-up visit has no defined
window, which can create protocol deviations and inconsistent endpoint timing.”

### Action plan

Say:

“I will now convert those risks into an accountable CRA action plan.”

Run the action-plan command.

Then say:

“This is a multi-tool workflow. The response shows both
`detect_protocol_risks` and `generate_action_plan`. The result assigns priority,
owner, action, timeline, and expected outcome.”

### Memory

Say:

“Finally, I will save a user preference: I prefer concise bullet points.”

Run the memory-save command.

Then say:

“The preference is saved locally in SQLite as `answer_style`.”

Say:

“I will now ask for the inclusion criteria and explicitly request my preferred
style.”

Run the preferred-style inclusion-criteria command.

Then say:

“The facts still come from RAG, while `memory_used` shows the concise style
preference. This demonstrates the difference between document knowledge and
user memory.”

Return to Slide 3.

## 8:00–10:00 — Course concept mapping and close

“I will finish by mapping the implementation to the required course concepts.

Persona design is implemented in `app/prompts.py`. It defines the Clinical
Trial Operations Assistant, its professional tone, grounding rules, practical
next-step behavior, and medical-decision boundary.

Tool use is implemented in `app/tools.py` through explicit search, summary,
risk, planning, and memory functions.

MCP is implemented in `app/mcp_server.py`, where six tools are registered with
FastMCP.

Reasoning and planning are implemented in `app/agent.py`. The planner selects a
bounded workflow and sequences risk detection before action planning.

RAG knowledge is implemented in `app/rag.py`, including loading, chunking,
embedding, persistence, relevance filtering, and source metadata.

Memory is implemented in `app/memory.py` using SQLite save, search, list, and
clear operations.

Docker deployment is implemented through the Dockerfile and Compose
configuration, including a non-root runtime and health check.

The strongest aspect of this project is that it remains inspectable and
demo-safe. It does not require an API key, it does not invent an answer when
the documents do not contain one, and it exposes the evidence and tool workflow
behind each response.

The current limitations are intentional for a capstone: synthetic text
documents, a small local vector store, rule-based risk coverage, and no
production security or GxP validation.

To make it production-ready, I would add controlled document versioning,
authentication and role-based access, enterprise vector storage, audit trails,
human approval gates, and formal retrieval and groundedness evaluations.

Thank you. I am ready for questions.”
