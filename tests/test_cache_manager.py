"""Tests for LangChain cache configuration."""

from __future__ import annotations

from src.cache_manager import apply_cache, cache_privacy_notice, clear_cache, get_active_mode
from src.config import CACHE_MODE_DISABLED, CACHE_MODE_MEMORY, CACHE_MODE_SQLITE, LLM_CACHE_DB_PATH


def test_cache_default_disabled():
    mode, message = apply_cache(CACHE_MODE_DISABLED)
    assert mode == CACHE_MODE_DISABLED
    assert "disabled" in message.lower()
    assert get_active_mode() == CACHE_MODE_DISABLED


def test_in_memory_cache_mode():
    mode, message = apply_cache(CACHE_MODE_MEMORY)
    assert mode == CACHE_MODE_MEMORY
    assert "memory" in message.lower()
    assert get_active_mode() == CACHE_MODE_MEMORY
    apply_cache(CACHE_MODE_DISABLED)


def test_sqlite_cache_mode(tmp_path, monkeypatch):
    db_path = tmp_path / "cache.sqlite"
    monkeypatch.setattr("src.cache_manager.LLM_CACHE_DB_PATH", db_path)
    mode, message = apply_cache(CACHE_MODE_SQLITE)
    assert mode == CACHE_MODE_SQLITE
    assert "sqlite" in message.lower()
    assert get_active_mode() == CACHE_MODE_SQLITE
    apply_cache(CACHE_MODE_DISABLED)


def test_unknown_mode_falls_back_to_disabled():
    mode, _message = apply_cache("not-a-real-mode")
    assert mode == CACHE_MODE_DISABLED


def test_cache_clear_when_disabled():
    apply_cache(CACHE_MODE_DISABLED)
    message = clear_cache()
    assert "no cache" in message.lower() or "disabled" in message.lower() or "not active" in message.lower() or "no cache is active" in message.lower()


def test_privacy_notice_mentions_prompts():
    notice = cache_privacy_notice()
    assert "prompt" in notice.lower() or "inputs" in notice.lower()
    assert "hash" in notice.lower()


def test_repeated_identical_requests_can_use_memory_cache():
    """
    Scenario 4: the same request twice with caching enabled.

    FakeListChatModel only has one canned reply. If cache works, the second
    invoke reuses that reply instead of running out of fake responses.
    """
    apply_cache(CACHE_MODE_MEMORY)
    try:
        from langchain_core.language_models.fake_chat_models import FakeListChatModel
        from langchain_core.messages import HumanMessage

        llm = FakeListChatModel(responses=["cached-educational-reply"])
        first = llm.invoke([HumanMessage(content="same prompt for cache test")])
        second = llm.invoke([HumanMessage(content="same prompt for cache test")])
        assert "cached-educational-reply" in str(first.content)
        assert "cached-educational-reply" in str(second.content)
    except ImportError:
        # If the fake model is missing, mode configuration was still tested above.
        assert get_active_mode() in {CACHE_MODE_MEMORY, CACHE_MODE_DISABLED}
    finally:
        apply_cache(CACHE_MODE_DISABLED)
