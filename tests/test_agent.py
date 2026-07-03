from app.agent import ClinicalTrialAgent


RESPONSE_KEYS = {
    "answer",
    "plan_summary",
    "tools_used",
    "retrieved_sources",
    "memory_used",
}


def test_agent_response_shape_and_memory_style(monkeypatch):
    monkeypatch.setattr(
        "app.agent.list_memories",
        lambda: [
            {
                "id": 1,
                "key": "answer_style",
                "value": "I prefer concise bullet points",
                "created_at": "2026-01-01 00:00:00",
            }
        ],
    )
    monkeypatch.setattr(
        "app.agent.search_protocol",
        lambda query: {
            "query": query,
            "count": 1,
            "results": [
                {
                    "source": "sample_protocol.txt",
                    "chunk_id": 1,
                    "text": (
                        "INCLUSION CRITERIA Participants must be aged 18 through "
                        "65 years and provide written informed consent."
                    ),
                    "text_preview": "INCLUSION CRITERIA",
                    "score": 0.9,
                }
            ],
            "sources": ["sample_protocol.txt#chunk-1"],
            "message": "Relevant document chunks retrieved.",
        },
    )

    result = ClinicalTrialAgent().run(
        "Based on my memory, answer in my preferred style: "
        "what are the inclusion criteria?",
        use_memory=True,
        debug=True,
    )

    assert set(result) == RESPONSE_KEYS
    assert result["tools_used"] == ["search_protocol"]
    assert result["retrieved_sources"] == ["sample_protocol.txt#chunk-1"]
    assert result["memory_used"] == [
        "answer_style=I prefer concise bullet points"
    ]
    assert "18 through 65" in result["answer"]
    assert result["plan_summary"]


def test_agent_reports_absent_document_information(monkeypatch):
    monkeypatch.setattr("app.agent.list_memories", lambda: [])
    monkeypatch.setattr(
        "app.agent.search_protocol",
        lambda query: {
            "query": query,
            "count": 0,
            "results": [],
            "sources": [],
            "message": "No relevant information was found in the indexed documents.",
        },
    )

    result = ClinicalTrialAgent().run("What is the pediatric dose?")

    assert "No relevant information" in result["answer"]
    assert result["retrieved_sources"] == []
