from app.memory import MemoryStore


def test_memory_save_search_list_and_clear(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")

    saved = store.save_memory("answer_style", "concise bullet points")

    assert saved["id"] > 0
    assert store.search_memory("concise")[0]["key"] == "answer_style"
    assert len(store.list_memories()) == 1
    assert store.clear_memories() == 1
    assert store.list_memories() == []


def test_memory_rejects_blank_values(tmp_path):
    store = MemoryStore(tmp_path / "memory.db")

    try:
        store.save_memory("", "value")
    except ValueError as exc:
        assert "must not be blank" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
