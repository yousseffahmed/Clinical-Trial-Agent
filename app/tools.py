"""Agent tools shared by FastAPI orchestration and the MCP server."""

import re
from typing import Dict, List, Union

from .config import settings
from .memory import list_memories, save_memory, search_memory
from .rag import get_all_documents, is_index_ready, search_documents


def _source_label(item: Dict[str, object]) -> str:
    return f"{item['source']}#chunk-{item['chunk_id']}"


def search_protocol(query: str) -> Dict[str, object]:
    """Search indexed study documents and return evidence with source metadata.

    This is the primary RAG tool used for protocol Q&A. It does not generate
    facts; it only returns chunks that pass the configured relevance threshold.
    """

    results = search_documents(query, top_k=settings.rag_top_k)
    return {
        "query": query,
        "count": len(results),
        "results": results,
        "sources": [_source_label(result) for result in results],
        "message": (
            "Relevant document chunks retrieved."
            if results
            else (
                "No relevant information was found in the indexed documents."
                if is_index_ready()
                else "No indexed content found. Run POST /ingest before searching."
            )
        ),
    }


def _sentences(text: str) -> List[str]:
    return [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+|\n+", text)
        if len(sentence.strip()) > 20
    ]


def summarize_protocol_section(section_query: str) -> Dict[str, object]:
    """Retrieve a section and produce a deterministic extractive summary.

    Generic instruction words are removed before retrieval. Exact section
    headings are preferred, then up to five unique evidence sentences are
    returned with source labels.
    """

    instruction_words = {
        "a",
        "an",
        "give",
        "me",
        "of",
        "overview",
        "rules",
        "section",
        "short",
        "summarize",
        "summary",
        "the",
    }
    query_tokens = re.findall(r"[a-z0-9]+", section_query.lower())
    content_tokens = [token for token in query_tokens if token not in instruction_words]
    retrieval_query = " ".join(content_tokens) or section_query
    retrieval = search_protocol(retrieval_query)
    if not retrieval["results"]:
        return {
            "section_query": section_query,
            "summary": retrieval["message"],
            "key_points": [],
            "sources": [],
        }

    query_terms = set(content_tokens)
    target_phrase = " ".join(content_tokens)
    candidates = []
    exact_results = [
        result
        for result in retrieval["results"]
        if target_phrase and target_phrase in str(result["text"]).lower()
    ]
    selected_results = exact_results[:2] or retrieval["results"][:3]
    for result_rank, result in enumerate(selected_results):
        text = str(result["text"])
        paragraphs = text.split("\n\n")
        exact_paragraphs = [
            paragraph
            for paragraph in paragraphs
            if target_phrase and target_phrase in paragraph.lower()
        ]
        section_text = "\n".join(exact_paragraphs) if exact_paragraphs else text
        for position, sentence in enumerate(_sentences(section_text)):
            terms = set(re.findall(r"[a-z0-9]+", sentence.lower()))
            overlap = len(query_terms & terms)
            phrase_bonus = 5 if target_phrase and target_phrase in sentence.lower() else 0
            candidates.append(
                (
                    overlap + phrase_bonus,
                    -result_rank,
                    -position,
                    sentence,
                    _source_label(result),
                )
            )
    candidates.sort(reverse=True)

    selected = []
    seen = set()
    for _, _, _, sentence, source in candidates:
        normalized = sentence.lower()
        if normalized not in seen:
            selected.append({"text": sentence, "source": source})
            seen.add(normalized)
        if len(selected) == 5:
            break

    return {
        "section_query": section_query,
        "summary": " ".join(point["text"] for point in selected[:3]),
        "key_points": selected,
        "sources": list(dict.fromkeys(point["source"] for point in selected)),
    }


def _evidence(
    chunks: List[Dict[str, object]], patterns: List[str]
) -> Union[Dict[str, object], None]:
    for chunk in chunks:
        lowered = str(chunk["text"]).lower()
        if all(pattern.lower() in lowered for pattern in patterns):
            return chunk
    return None


def detect_protocol_risks(focus_area: str = "general") -> Dict[str, object]:
    """Detect evidence-backed operational risks using transparent rules.

    Each risk rule must match text in the indexed documents. Recommendations
    are deliberately separated from quoted evidence and operational impact.
    """

    chunks = get_all_documents()
    if not chunks:
        return {
            "focus_area": focus_area,
            "risks": [],
            "sources": [],
            "message": "No indexed content found. Run POST /ingest first.",
        }

    candidates = [
        {
            "match": ["no allowable visit window"],
            "risk": "Undefined follow-up visit window",
            "severity": "High",
            "impact": (
                "Sites cannot consistently classify out-of-window visits, which can "
                "cause protocol deviations and inconsistent endpoint timing."
            ),
            "recommended_action": (
                "Obtain a protocol clarification defining the allowable window and "
                "update the visit calculator before enrollment."
            ),
            "tags": "visit schedule timing window general",
        },
        {
            "match": ["escalation threshold", "not specified"],
            "risk": "Incomplete safety escalation thresholds",
            "severity": "High",
            "impact": (
                "Investigators may apply inconsistent escalation decisions for "
                "clinically significant findings."
            ),
            "recommended_action": (
                "Medical monitoring should publish measurable escalation criteria "
                "and a 24-hour contact pathway."
            ),
            "tags": "safety monitoring escalation general",
        },
        {
            "match": ["paper diary", "transcribed"],
            "risk": "Paper-to-EDC transcription and missing-data risk",
            "severity": "Medium",
            "impact": (
                "Manual transcription can introduce errors, late entries, and "
                "unresolved discrepancies in patient-reported data."
            ),
            "recommended_action": (
                "Assign a reconciliation owner, perform source-to-EDC checks at each "
                "visit, and track overdue diary entries."
            ),
            "tags": "data missing diary quality general",
        },
        {
            "match": ["approximately 4.5 hours"],
            "risk": "High participant burden at Baseline",
            "severity": "Medium",
            "impact": (
                "A long visit with fasting and multiple assessments may increase "
                "fatigue, rescheduling, and early withdrawal."
            ),
            "recommended_action": (
                "Provide pre-visit instructions, stagger assessments, and monitor "
                "visit duration and discontinuation signals."
            ),
            "tags": "patient participant burden retention general",
        },
        {
            "match": ["confirmation owner is not named"],
            "risk": "Unclear randomization responsibility",
            "severity": "Medium",
            "impact": (
                "An unnamed owner can delay randomization or permit randomization "
                "before all eligibility evidence is confirmed."
            ),
            "recommended_action": (
                "Define the accountable site role and require a signed eligibility "
                "checklist before randomization."
            ),
            "tags": "eligibility site responsibility randomization general",
        },
    ]

    focus = focus_area.lower().strip()
    risks = []
    for candidate in candidates:
        if focus not in {"", "general", "all"}:
            focus_terms = set(re.findall(r"[a-z0-9]+", focus))
            tag_terms = set(candidate["tags"].split())
            if not focus_terms & tag_terms:
                continue
        match = _evidence(chunks, candidate["match"])
        if not match:
            continue
        evidence_sentences = [
            sentence
            for sentence in _sentences(str(match["text"]))
            if any(pattern in sentence.lower() for pattern in candidate["match"])
        ]
        risks.append(
            {
                "risk": candidate["risk"],
                "severity": candidate["severity"],
                "evidence": (
                    evidence_sentences[0]
                    if evidence_sentences
                    else str(match["text"])[:240]
                ),
                "source": _source_label(match),
                "impact": candidate["impact"],
                "recommended_action": candidate["recommended_action"],
            }
        )

    return {
        "focus_area": focus_area,
        "risks": risks,
        "sources": list(dict.fromkeys(risk["source"] for risk in risks)),
        "message": (
            f"Detected {len(risks)} evidence-backed operational risk(s)."
            if risks
            else "No configured risk indicators matched the indexed documents."
        ),
    }


def generate_action_plan(risks: Union[List[Dict[str, object]], str]) -> Dict[str, object]:
    """Convert risk records or a focus-area string into an owned action plan.

    This tool is sequenced after risk detection by the agent planner so actions
    always retain a traceable evidence basis.
    """

    if isinstance(risks, str):
        risk_records = detect_protocol_risks(risks)["risks"]
    else:
        risk_records = risks

    owner_rules = {
        "safety": "Medical Monitor",
        "visit": "Clinical Project Manager",
        "data": "Data Manager",
        "burden": "Site PI / CRA",
        "randomization": "Site PI / CRA",
        "eligibility": "Site PI / CRA",
    }
    timeline_rules = {"High": "Before first subject enrolled / within 5 business days"}
    plan = []
    for index, risk in enumerate(risk_records, start=1):
        name = str(risk.get("risk", "Operational risk"))
        owner = "CRA"
        for keyword, candidate_owner in owner_rules.items():
            if keyword in name.lower():
                owner = candidate_owner
                break
        severity = str(risk.get("severity", "Medium"))
        plan.append(
            {
                "priority": f"P{index} ({severity})",
                "owner": owner,
                "action": str(
                    risk.get("recommended_action", "Assess and mitigate the risk.")
                ),
                "timeline": timeline_rules.get(
                    severity, "Within 10 business days and before the affected visit"
                ),
                "expected_outcome": f"Controlled risk: {name}.",
            }
        )
    return {
        "action_plan": plan,
        "count": len(plan),
        "message": (
            f"Generated {len(plan)} owned action(s)."
            if plan
            else "No risks were supplied; no action plan was generated."
        ),
    }


def save_user_memory(key: str, value: str) -> Dict[str, object]:
    record = save_memory(key, value)
    return {"status": "saved", "memory": record}


def recall_user_memory(query: str) -> Dict[str, object]:
    records = search_memory(query)
    return {"query": query, "count": len(records), "memories": records}


def list_capabilities() -> Dict[str, object]:
    return {
        "tools": [
            {
                "name": "search_protocol",
                "description": "Retrieve relevant protocol, SOP, and visit chunks.",
            },
            {
                "name": "summarize_protocol_section",
                "description": "Create a grounded extractive section summary.",
            },
            {
                "name": "detect_protocol_risks",
                "description": "Identify evidence-backed operational risks.",
            },
            {
                "name": "generate_action_plan",
                "description": "Turn risks into owned, timed actions.",
            },
            {
                "name": "save_user_memory",
                "description": "Store a user preference or durable fact in SQLite.",
            },
            {
                "name": "recall_user_memory",
                "description": "Search locally stored user memories.",
            },
            {
                "name": "list_capabilities",
                "description": "List the agent's available tools.",
            },
        ],
        "memory_count": len(list_memories()),
    }
