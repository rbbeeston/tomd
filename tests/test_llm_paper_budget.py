"""Per-paper LLM repair budget (TOMD_LLM_PAPER_BUDGET)."""
from tomd.lib.pdf import llmrepair
from tomd.lib.pdf.types import Section, SectionKind


def test_spent_paper_budget_leaves_table_unrepaired(monkeypatch):
    monkeypatch.setenv("TOMD_LLM_PAPER_BUDGET", "100")
    llmrepair.reset_paper()
    llmrepair._PAPER["input_tokens"] = 150
    sec = Section(kind=SectionKind.TABLE, text="")
    words = [(0, 0, 10, 10, "a")]
    assert llmrepair.repair(sec, None, (0, 0, 10, 10), words, verify=lambda *a: "") == "paper-budget"
    assert llmrepair.paper_record()["unrepaired_by_paper_budget"] == 1
    assert sec.metadata["llm_repair"]["result"].startswith("not asked")


def test_no_budget_set_asks_as_before(monkeypatch):
    monkeypatch.delenv("TOMD_LLM_PAPER_BUDGET", raising=False)
    llmrepair.reset_paper()
    llmrepair._PAPER["input_tokens"] = 10 ** 9
    sec = Section(kind=SectionKind.TABLE, text="")
    monkeypatch.setattr(llmrepair, "_client", lambda: None)
    assert llmrepair.repair(sec, None, (0, 0, 10, 10), [(0, 0, 10, 10, "a")], verify=lambda *a: "") == "no-client"
