"""
LangChain cache configuration for MediGuide AI.

Supported modes:
- disabled: no cache (default, best for medical privacy)
- memory: InMemoryCache (RAM only, forgotten when the app stops)
- sqlite: SQLiteCache (saved on disk in the data/ folder)

Privacy: caching can store model inputs and responses, including
symptom descriptions. Hashing a cache key does not protect the
cached response itself. Users must opt in.
"""

from __future__ import annotations

from typing import Any

from src.config import (
    CACHE_MODE_DISABLED,
    CACHE_MODE_MEMORY,
    CACHE_MODE_SQLITE,
    CACHE_MODES,
    LLM_CACHE_DB_PATH,
    ensure_data_dir,
)
from src.utils import LOGGER

# Module-level memory of the last successful cache mode.
# Streamlit reruns the script, so we skip duplicate initialization.
_active_mode = CACHE_MODE_DISABLED
_active_cache: Any = None


def _set_llm_cache(cache_obj: Any) -> None:
    """Register a cache with LangChain. Try both supported import paths."""
    try:
        from langchain_core.globals import set_llm_cache
    except ImportError:  # pragma: no cover
        from langchain.globals import set_llm_cache  # type: ignore[import-not-found]
    set_llm_cache(cache_obj)


def get_active_mode() -> str:
    return _active_mode


def apply_cache(mode: str) -> tuple[str, str]:
    """
    Activate a cache mode.

    Returns (actual_mode, status_message).
    If initialization fails, the cache is disabled.
    """
    global _active_mode, _active_cache

    requested = (mode or CACHE_MODE_DISABLED).strip().lower()
    if requested not in CACHE_MODES:
        requested = CACHE_MODE_DISABLED

    if requested == _active_mode and requested != CACHE_MODE_DISABLED:
        return _active_mode, f"Cache already using '{_active_mode}' mode."

    try:
        if requested == CACHE_MODE_DISABLED:
            _set_llm_cache(None)
            _active_cache = None
            _active_mode = CACHE_MODE_DISABLED
            return _active_mode, "LLM cache is disabled. New model calls will not be stored."

        if requested == CACHE_MODE_MEMORY:
            from langchain_community.cache import InMemoryCache

            cache = InMemoryCache()
            _set_llm_cache(cache)
            _active_cache = cache
            _active_mode = CACHE_MODE_MEMORY
            return _active_mode, (
                "In-memory cache is on. Repeated identical model requests in this "
                "app session may reuse a stored response. The cache is cleared "
                "when the process ends. Cached entries can include patient prompts."
            )

        # sqlite
        from langchain_community.cache import SQLiteCache

        ensure_data_dir()
        cache = SQLiteCache(database_path=str(LLM_CACHE_DB_PATH))
        _set_llm_cache(cache)
        _active_cache = cache
        _active_mode = CACHE_MODE_SQLITE
        return _active_mode, (
            "SQLite cache is on. Repeated identical model requests may reuse a "
            f"stored response in {LLM_CACHE_DB_PATH.name}. This file can persist "
            "after the app restarts and may contain patient prompts and responses."
        )
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Cache initialization failed type=%s", type(exc).__name__)
        try:
            _set_llm_cache(None)
        except Exception:
            pass
        _active_cache = None
        _active_mode = CACHE_MODE_DISABLED
        return _active_mode, (
            "Cache could not be started, so it was left disabled. "
            "Assessments can still run without caching."
        )


def clear_cache() -> str:
    """
    Clear the currently active cache.

    In-memory: replace with a new empty InMemoryCache.
    SQLite: delete rows from the LangChain cache table when possible.
    Disabled: nothing to clear.
    """
    global _active_cache

    mode = _active_mode
    if mode == CACHE_MODE_DISABLED or _active_cache is None:
        apply_cache(CACHE_MODE_DISABLED)
        return "No cache is active."

    try:
        if mode == CACHE_MODE_MEMORY:
            apply_cache(CACHE_MODE_DISABLED)
            apply_cache(CACHE_MODE_MEMORY)
            return "In-memory cache cleared."

        # SQLiteCache stores rows in a table usually named full_llm_cache
        import sqlite3

        if LLM_CACHE_DB_PATH.exists():
            with sqlite3.connect(LLM_CACHE_DB_PATH) as connection:
                tables = [
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                ]
                for table in tables:
                    # Table names come from sqlite_master, not from user input.
                    connection.execute(f'DELETE FROM "{table}"')
                connection.commit()
        apply_cache(CACHE_MODE_DISABLED)
        apply_cache(CACHE_MODE_SQLITE)
        return "SQLite cache cleared."
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("Cache clear failed type=%s", type(exc).__name__)
        return "The cache could not be cleared completely. You can also delete the cache file in the data folder."


def cache_privacy_notice() -> str:
    return (
        "Caching may store model inputs and the text returned by "
        "the model. That can include symptoms. Hashing a cache key does not "
        "hide the stored response. Default is disabled. Only turn caching on "
        "for educational experiments, then clear it afterwards."
    )
