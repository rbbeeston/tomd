"""LLM repair in the corpus profile: budget, fail-safe status, first reading kept, stays flagged."""

from lib.pdf import llmrepair as L
from lib.pdf.types import Confidence, Section, SectionKind, Span


def _fresh(monkeypatch, **env):
    monkeypatch.setattr(L, "_DISABLED", False)
    monkeypatch.setattr(L, "_SPENT", 0)
    for k in ("TOMD_LLM", "TOMD_LLM_BUDGET", "ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    L.reset_paper()


def test_no_credentials_runs_on_and_says_so(monkeypatch, tmp_path):
    _fresh(monkeypatch, TOMD_LLM="1", ANTHROPIC_CONFIG_DIR=str(tmp_path))
    assert not L.llm_enabled()
    assert L.paper_record()["status"] == "unavailable: no credentials"


def test_off_by_default(monkeypatch):
    _fresh(monkeypatch)
    assert L.paper_record()["status"] == "off"


def test_budget_stops_repair(monkeypatch):
    _fresh(monkeypatch, TOMD_LLM="1", TOMD_LLM_BUDGET="100", ANTHROPIC_API_KEY="x")
    assert L.llm_enabled()
    monkeypatch.setattr(L, "_SPENT", 100)
    assert not L.llm_enabled() and L.paper_record()["status"] == "budget reached"


def test_verified_repair_keeps_first_reading_and_stays_flagged(monkeypatch):
    _fresh(monkeypatch, TOMD_LLM="1", ANTHROPIC_API_KEY="x")
    words = [(0, 0, 10, 10, "a"), (20, 0, 30, 10, "b"), (0, 20, 10, 30, "c"), (20, 20, 30, 30, "d")]
    sec = Section(kind=SectionKind.TABLE, text="a b | c d", confidence=Confidence.UNCERTAIN,
                  columns=[[[Span("a b")], [Span("c d")]]])
    sec.metadata["table_source"] = "grid"
    monkeypatch.setattr(L, "ask", lambda *a: ([[[0], [1]], [[2], [3]]], "claude-test", 1.5,
                                               {"input_tokens": 10, "output_tokens": 2}))
    assert L.repair(sec, None, (0, 0, 30, 30), words, lambda new, w: "", client=object()) == "verified"
    assert sec.confidence == Confidence.UNCERTAIN and "llm-repaired" in sec.metadata["uncertain_reasons"]
    assert sec.metadata["llm_repair"]["first_reading"] == "a b | c d"
    assert sec.metadata["llm_repair"]["first_source"] == "grid"
    rec = L.paper_record()
    assert rec["calls"] == 1 and rec["verified"] == 1 and rec["input_tokens"] == 10 and rec["models"] == ["claude-test"]
