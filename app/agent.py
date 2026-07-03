"""Intent routing, tool orchestration, memory use, and answer generation."""

import json
import re
from typing import Dict, List, Optional, Tuple

from .config import settings
from .logger import get_logger
from .memory import list_memories
from .prompts import SYSTEM_PROMPT, build_grounded_prompt
from .tools import (
    detect_protocol_risks,
    generate_action_plan,
    list_capabilities,
    recall_user_memory,
    save_user_memory,
    search_protocol,
    summarize_protocol_section,
)

logger = get_logger(__name__)


class ClinicalTrialAgent:
    """A transparent planner that selects and sequences domain tools."""

    def _classify_intent(self, message: str) -> str:
        """Map a request to one bounded workflow.

        The rules are intentionally inspectable for a capstone demo. A
        production planner could replace this classifier while preserving the
        same typed tool boundary.
        """
        lowered = message.lower()
        if any(phrase in lowered for phrase in ["remember that", "save my", "my preference is"]):
            return "save_memory"
        if any(
            phrase in lowered
            for phrase in ["what do you remember", "recall my", "my preferences"]
        ):
            return "recall_memory"
        if any(word in lowered for word in ["capabilities", "available tools", "what can you do"]):
            return "capabilities"
        if "action plan" in lowered or "next steps" in lowered:
            return "action_plan"
        if any(word in lowered for word in ["risk", "gap", "issue", "analyze this protocol"]):
            return "risk"
        if any(word in lowered for word in ["summarize", "summary", "short overview"]):
            return "summary"
        return "question"

    def _memory_context(self, message: str, enabled: bool) -> List[Dict[str, object]]:
        if not enabled:
            return []
        records = list_memories()
        message_terms = set(re.findall(r"[a-z0-9]+", message.lower()))
        relevant = []
        for record in records:
            key = str(record["key"]).lower()
            value_terms = set(re.findall(r"[a-z0-9]+", str(record["value"]).lower()))
            if (
                key in {"answer_style", "output_format", "user_role", "study_focus"}
                or message_terms & value_terms
            ):
                relevant.append(record)
        return relevant[:10]

    def _parse_memory(self, message: str) -> Tuple[str, str]:
        lowered = message.lower()
        key = "user_fact"
        if "role" in lowered or re.search(r"\bi am (?:a|an) ", lowered):
            key = "user_role"
        elif "concise" in lowered or "detailed" in lowered or "answer style" in lowered:
            key = "answer_style"
        elif any(word in lowered for word in ["table", "bullet", "json", "format"]):
            key = "output_format"
        elif "study" in lowered or "focus" in lowered:
            key = "study_focus"

        value = re.sub(
            r"^\s*(please\s+)?(remember that|save my|my preference is)\s*",
            "",
            message,
            flags=re.IGNORECASE,
        ).strip(" .")
        return key, value or message.strip()

    @staticmethod
    def _format_search(payload: Dict[str, object], concise: bool = False) -> str:
        results = payload["results"]
        if not results:
            return str(payload["message"])
        visit_match = re.search(r"\bvisit\s+\d+\b", str(payload["query"]).lower())
        if visit_match:
            exact_results = [
                result
                for result in results
                if visit_match.group(0) in str(result["text"]).lower()
            ]
            if exact_results:
                results = exact_results
        # Convert retrieved chunks into short evidence statements rather than
        # dumping entire chunks into the final response.
        query_terms = {
            token
            for token in re.findall(r"[a-z0-9]+", str(payload["query"]).lower())
            if token
            not in {
                "a",
                "an",
                "and",
                "answer",
                "are",
                "based",
                "in",
                "is",
                "me",
                "my",
                "of",
                "on",
                "preferred",
                "style",
                "the",
                "what",
            }
        }
        evidence = []
        seen = set()
        for result_rank, result in enumerate(results):
            sentences = [
                sentence.strip()
                for sentence in re.split(
                    r"(?<=[.!?])\s+|\n+", str(result["text"])
                )
                if len(sentence.strip()) > 20
            ]
            for sentence_rank, sentence in enumerate(sentences):
                sentence_terms = set(
                    re.findall(r"[a-z0-9]+", sentence.lower())
                )
                overlap = len(query_terms & sentence_terms)
                exact_bonus = (
                    5
                    if visit_match and visit_match.group(0) in sentence.lower()
                    else 0
                )
                normalized = sentence.lower()
                if normalized not in seen:
                    evidence.append(
                        (
                            overlap + exact_bonus,
                            -result_rank,
                            -sentence_rank,
                            sentence,
                            result,
                        )
                    )
                    seen.add(normalized)
        evidence.sort(reverse=True, key=lambda item: item[:3])

        limit = 3 if concise else 5
        lines = ["## Document-based answer"]
        for _, _, _, text, result in evidence[:limit]:
            if concise and len(text) > 320:
                text = text[:317].rsplit(" ", 1)[0] + "..."
            lines.append(
                f"- **{result['source']} (chunk {result['chunk_id']})**: {text}"
            )
        lines.extend(
            [
                "",
                "## Operational note",
                "Confirm decisions against the approved protocol version and applicable SOPs.",
            ]
        )
        return "\n".join(lines)

    @staticmethod
    def _format_summary(payload: Dict[str, object]) -> str:
        if not payload["key_points"]:
            return str(payload["summary"])
        lines = ["## Summary", str(payload["summary"]), "", "## Key points"]
        lines.extend(
            f"- {point['text']} *[{point['source']}]*"
            for point in payload["key_points"]
        )
        return "\n".join(lines)

    @staticmethod
    def _format_risks(payload: Dict[str, object]) -> str:
        if not payload["risks"]:
            return str(payload["message"])
        lines = ["## Operational risks"]
        for number, risk in enumerate(payload["risks"], start=1):
            lines.extend(
                [
                    f"### {number}. {risk['risk']} — {risk['severity']}",
                    f"- **Evidence:** {risk['evidence']} *[{risk['source']}]*",
                    f"- **Why it matters:** {risk['impact']}",
                    f"- **Recommended action:** {risk['recommended_action']}",
                ]
            )
        return "\n".join(lines)

    @staticmethod
    def _format_action_plan(
        risk_payload: Dict[str, object], plan_payload: Dict[str, object]
    ) -> str:
        if not plan_payload["action_plan"]:
            return str(plan_payload["message"])
        lines = [
            "## CRA action plan",
            "| Priority | Owner | Action | Timeline | Expected outcome |",
            "|---|---|---|---|---|",
        ]
        for item in plan_payload["action_plan"]:
            values = [
                str(item[field]).replace("|", "/")
                for field in [
                    "priority",
                    "owner",
                    "action",
                    "timeline",
                    "expected_outcome",
                ]
            ]
            lines.append("| " + " | ".join(values) + " |")
        lines.append(
            f"\nPlan is based on {len(risk_payload['risks'])} evidence-backed risk(s)."
        )
        return "\n".join(lines)

    def _llm_answer(
        self,
        message: str,
        payload: Dict[str, object],
        memory_context: List[Dict[str, object]],
    ) -> Optional[str]:
        if not settings.llm_enabled:
            return None
        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            response = client.responses.create(
                model=settings.openai_model,
                instructions=SYSTEM_PROMPT,
                input=build_grounded_prompt(
                    message,
                    json.dumps(payload, ensure_ascii=False, default=str),
                    json.dumps(memory_context, ensure_ascii=False, default=str),
                ),
            )
            return response.output_text.strip()
        except Exception as exc:
            logger.exception("LLM generation failed; returning deterministic answer: %s", exc)
            return None

    def run(self, message: str, use_memory: bool = True, debug: bool = False) -> Dict[str, object]:
        """Plan and execute one bounded agent turn without exposing chain-of-thought."""

        # Planning has four visible phases: classify intent, select relevant
        # memory, execute the minimum tool sequence, and format grounded output.
        # ``plan_summary`` reports these high-level actions, never hidden
        # chain-of-thought.
        intent = self._classify_intent(message)
        memories = self._memory_context(message, use_memory)
        memory_labels = [f"{item['key']}={item['value']}" for item in memories]
        tools_used: List[str] = []
        sources: List[str] = []
        payload: Dict[str, object]

        logger.info("Agent intent=%s memory_records=%d", intent, len(memories))

        if intent == "save_memory":
            key, value = self._parse_memory(message)
            payload = save_user_memory(key, value)
            tools_used.append("save_user_memory")
            answer = f"Saved locally: **{key}** = {value}"
            plan = "Identify the durable preference/fact, then save it to local SQLite memory."
        elif intent == "recall_memory":
            lowered = message.lower()
            generic_recall = any(
                phrase in lowered
                for phrase in ["what do you remember", "my preferences"]
            )
            payload = recall_user_memory("" if generic_recall else message)
            tools_used.append("recall_user_memory")
            recalled = payload["memories"]
            answer = (
                "\n".join(
                    ["## Stored memories"]
                    + [f"- **{item['key']}**: {item['value']}" for item in recalled]
                )
                if recalled
                else "No matching memories are stored."
            )
            memory_labels = [f"{item['key']}={item['value']}" for item in recalled]
            plan = "Search local SQLite memory and return matching records."
        elif intent == "capabilities":
            payload = list_capabilities()
            tools_used.append("list_capabilities")
            answer = "\n".join(
                ["## Available tools"]
                + [
                    f"- **{tool['name']}** — {tool['description']}"
                    for tool in payload["tools"]
                ]
            )
            plan = "List registered domain, RAG, planning, and memory tools."
        elif intent == "action_plan":
            # Multi-tool workflow: risk evidence must exist before an action
            # can be assigned an owner and timeline.
            risk_payload = detect_protocol_risks("general")
            plan_payload = generate_action_plan(risk_payload["risks"])
            payload = {"risk_analysis": risk_payload, "plan": plan_payload}
            tools_used.extend(["detect_protocol_risks", "generate_action_plan"])
            sources = risk_payload["sources"]
            answer = self._format_action_plan(risk_payload, plan_payload)
            plan = (
                "Retrieve indexed evidence, detect operational risks, then convert "
                "each risk into an owned and timed action."
            )
        elif intent == "risk":
            payload = detect_protocol_risks(message)
            if not payload["risks"]:
                payload = detect_protocol_risks("general")
            tools_used.append("detect_protocol_risks")
            sources = payload["sources"]
            answer = self._format_risks(payload)
            plan = (
                "Inspect indexed documents for evidence-backed risk indicators, "
                "assess impact, and propose practical mitigations."
            )
        elif intent == "summary":
            payload = summarize_protocol_section(message)
            tools_used.append("summarize_protocol_section")
            sources = payload["sources"]
            answer = self._format_summary(payload)
            plan = (
                "Retrieve the most relevant section, extract grounded key points, "
                "and retain source labels."
            )
        else:
            payload = search_protocol(message)
            tools_used.append("search_protocol")
            visit_match = re.search(r"\bvisit\s+\d+\b", message.lower())
            if visit_match:
                exact_results = [
                    result
                    for result in payload["results"]
                    if visit_match.group(0) in str(result["text"]).lower()
                ]
                if exact_results:
                    payload = dict(payload)
                    payload["results"] = exact_results
                    payload["sources"] = [
                        f"{result['source']}#chunk-{result['chunk_id']}"
                        for result in exact_results
                    ]
            sources = payload["sources"]
            concise = any("concise" in label.lower() for label in memory_labels)
            answer = self._format_search(payload, concise=concise)
            plan = (
                "Interpret the protocol question, retrieve relevant indexed chunks, "
                "and answer only from document evidence."
            )

        if intent not in {"save_memory", "recall_memory", "capabilities"}:
            llm_answer = self._llm_answer(message, payload, memories)
            if llm_answer:
                answer = llm_answer

        return {
            "answer": answer,
            "plan_summary": plan if debug else plan,
            "tools_used": tools_used,
            "retrieved_sources": list(dict.fromkeys(sources)),
            "memory_used": memory_labels,
        }


clinical_agent = ClinicalTrialAgent()
