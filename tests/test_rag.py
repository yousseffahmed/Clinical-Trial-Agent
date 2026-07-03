from app.rag import RAGService


def test_rag_ingestion_and_search(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "protocol.txt").write_text(
        "INCLUSION CRITERIA\n\nAdults aged 18 through 65 may participate."
        "\n\nVISIT 2\n\nVisit 2 occurs on Day 28 with a window of plus or minus 3 days.",
        encoding="utf-8",
    )
    service = RAGService(
        data_dir=data_dir,
        index_path=tmp_path / "vectors" / "index.json",
        embedding_backend="hash",
        chunk_size=120,
        chunk_overlap=20,
    )

    result = service.ingest_documents()
    matches = service.search_documents("What is the Visit 2 window?", top_k=2)

    assert result["documents"] == 1
    assert result["chunks"] >= 1
    assert matches
    assert matches[0]["source"] == "protocol.txt"
    assert "Day 28" in matches[0]["text"]
    assert service.get_all_documents()


def test_empty_rag_returns_no_results(tmp_path):
    service = RAGService(
        data_dir=tmp_path / "missing",
        index_path=tmp_path / "index.json",
        embedding_backend="hash",
    )

    result = service.ingest_documents()

    assert result["status"] == "no_documents"
    assert service.search_documents("anything") == []


def test_relevance_threshold_rejects_unrelated_matches(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "protocol.txt").write_text(
        "Visit 2 occurs on Day 28.", encoding="utf-8"
    )
    service = RAGService(
        data_dir=data_dir,
        index_path=tmp_path / "index.json",
        embedding_backend="hash",
        min_score=-1.0,
    )
    service.ingest_documents()

    assert service.search_documents("aircraft maintenance schedule") == []


def test_sentence_transformer_failure_falls_back_to_hash(tmp_path, monkeypatch):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "protocol.txt").write_text("Safety monitoring.", encoding="utf-8")

    def unavailable(_):
        raise ImportError("sentence-transformers not installed")

    monkeypatch.setattr("app.rag.SentenceTransformerEmbedder", unavailable)
    service = RAGService(
        data_dir=data_dir,
        index_path=tmp_path / "index.json",
        embedding_backend="sentence-transformers",
    )

    result = service.ingest_documents()

    assert result["embedding_backend"] == "hash"
