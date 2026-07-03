from app import tools


def test_search_protocol_shape(monkeypatch):
    monkeypatch.setattr(
        tools,
        "search_documents",
        lambda query, top_k: [
            {
                "source": "sample_protocol.txt",
                "chunk_id": 2,
                "text": "Visit 2 is Day 28 plus or minus 3 days.",
                "text_preview": "Visit 2",
                "score": 0.8,
            }
        ],
    )

    result = tools.search_protocol("Visit 2 window")

    assert result["count"] == 1
    assert result["sources"] == ["sample_protocol.txt#chunk-2"]


def test_risk_detection_and_action_plan(monkeypatch):
    monkeypatch.setattr(
        tools,
        "get_all_documents",
        lambda: [
            {
                "source": "protocol.txt",
                "chunk_id": 1,
                "text": "Follow-up is targeted for Day 98; no allowable visit window is defined.",
                "text_preview": "Follow-up",
            }
        ],
    )

    risk_result = tools.detect_protocol_risks("visit window")
    plan_result = tools.generate_action_plan(risk_result["risks"])

    assert risk_result["risks"][0]["severity"] == "High"
    assert plan_result["count"] == 1
    assert plan_result["action_plan"][0]["owner"] == "Clinical Project Manager"


def test_summary_has_sources(monkeypatch):
    monkeypatch.setattr(
        tools,
        "search_protocol",
        lambda query: {
            "query": query,
            "results": [
                {
                    "source": "protocol.txt",
                    "chunk_id": 4,
                    "text": (
                        "Serious adverse events must be reported within 24 hours. "
                        "Follow-up information is due within three business days."
                    ),
                }
            ],
            "sources": ["protocol.txt#chunk-4"],
            "message": "Relevant document chunks retrieved.",
        },
    )

    result = tools.summarize_protocol_section("safety reporting")

    assert result["key_points"]
    assert result["sources"] == ["protocol.txt#chunk-4"]
