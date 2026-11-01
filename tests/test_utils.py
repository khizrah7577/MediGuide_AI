"""Tests for JSON helpers and formatting utilities."""

from __future__ import annotations

import json

from src.utils import format_symptom_list, parse_json_safely, strip_markdown_fences


def test_strip_markdown_fences():
    raw = """```json
{"summary": "hello"}
```"""
    assert strip_markdown_fences(raw) == '{"summary": "hello"}'


def test_parse_valid_json():
    data, error = parse_json_safely('{"summary": "ok", "n": 1}')
    assert error is None
    assert data["summary"] == "ok"


def test_parse_markdown_fenced_json():
    raw = """```json
{"summary": "fenced", "possible_conditions": []}
```"""
    data, error = parse_json_safely(raw)
    assert error is None
    assert data["summary"] == "fenced"


def test_parse_malformed_json():
    data, error = parse_json_safely("{not json")
    assert data is None
    assert error
    assert "eval" not in error.lower()


def test_parse_empty_response():
    data, error = parse_json_safely("   ")
    assert data is None
    assert "empty" in error.lower()


def test_parse_never_uses_eval(monkeypatch):
    """Guardrail: parsing must go through json.loads, never eval."""
    called = {"eval": False, "loads": False}
    real_loads = json.loads

    def fake_loads(text):
        called["loads"] = True
        return real_loads(text)

    def fake_eval(_text):
        called["eval"] = True
        raise AssertionError("eval should not be used")

    monkeypatch.setattr("src.utils.json.loads", fake_loads)
    monkeypatch.setattr("builtins.eval", fake_eval)
    parse_json_safely('{"summary": "safe"}')
    assert called["loads"] is True
    assert called["eval"] is False


def test_format_symptom_list():
    text = format_symptom_list(["Cough", "Fever"], "night sweats")
    assert "Cough" in text
    assert "night sweats" in text
