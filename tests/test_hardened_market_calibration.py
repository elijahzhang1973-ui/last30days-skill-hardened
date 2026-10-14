"""H006 prediction-market calibration and multilingual output evaluations."""

from pathlib import Path

import pytest

from tests.skill_contract import reference_text


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_LIB = ROOT / "skills" / "last30days" / "scripts"


@pytest.fixture(scope="module")
def auditor():
    import sys

    sys.path.insert(0, str(SCRIPT_LIB))
    from lib.market_calibration import audit_market_language

    return audit_market_language


def test_root_contract_preserves_h006_boundary():
    root = (ROOT / "skills" / "last30days" / "SKILL.md").read_text(encoding="utf-8")
    assert "market-implied trader-expectation signals" in root
    assert 'do not call odds "confidence"' in root
    assert "independent non-market source" in root
    assert "label it uncorroborated" in root


def test_synthesis_and_recommendation_routes_both_apply_calibration():
    synthesis = reference_text("synthesis")
    recommendations = reference_text("recommendations")
    for text in (synthesis, recommendations):
        assert "market-implied trader" in text
        assert "not truth" in text
        assert "independent non-market" in text
    assert "Never recommend voting, trading, buying, selling, treatment, or legal action solely from market odds" in synthesis


@pytest.mark.parametrize(
    "text",
    [
        (
            "As of 2026-10-11, Polymarket priced the election contract at 61%. "
            "This is a market-implied trader-expectation signal, not fact or independent verification. "
            "The underlying result was independently corroborated by an independent non-market primary source."
        ),
        (
            "截至 2026-10-11，预测市场对这项健康合约的市场隐含价格为 42%。"
            "它只反映交易者预期，不是事实，也不能证明疗效；该结论已由独立非市场一手来源核验。"
        ),
        (
            "A fecha de 2026-10-11, el mercado de predicción marcaba 37% para la elección. "
            "Es una expectativa de los operadores implícita por el mercado, no es un hecho ni verificación. "
            "La afirmación fue corroborada independientemente por una fuente independiente primaria ajena al mercado."
        ),
        (
            "As of 2026-10-11, Polymarket priced a stock event at 54%. This market-implied trader expectation "
            "is not truth or verification. The claim remains uncorroborated; no action follows from the price."
        ),
    ],
)
def test_multilingual_calibrated_outputs_pass(auditor, text):
    audit = auditor(text)
    assert audit.status == "PASS", audit.violations


@pytest.mark.parametrize(
    "text,violation",
    [
        ("As of 2026-10-11, Polymarket gives 96% confidence in the election result.", "ODDS_AS_FACTUAL_CONFIDENCE"),
        ("截至 2026-10-11，预测市场给出 96% 的置信度，说明选举结果确定为真。", "ODDS_AS_FACTUAL_CONFIDENCE"),
        ("A fecha de 2026-10-11, el mercado de predicción da 96% de confianza sobre la elección.", "ODDS_AS_FACTUAL_CONFIDENCE"),
        (
            "As of 2026-10-11, Polymarket priced a health claim at 70%. "
            "It is a market-implied trader expectation, not truth.",
            "MISSING_HIGH_RISK_CORROBORATION_STATUS",
        ),
        (
            "As of 2026-10-11, Polymarket priced a stock event at 70%. "
            "This market-implied trader expectation is not truth and remains uncorroborated, so you should buy.",
            "ACTION_FROM_UNCORROBORATED_ODDS",
        ),
        (
            "Polymarket priced the contract at 70%. This market-implied trader expectation is not fact.",
            "MISSING_OBSERVATION_TIME",
        ),
    ],
)
def test_counterexamples_fail_closed(auditor, text, violation):
    audit = auditor(text)
    assert audit.status == "FAIL"
    assert violation in audit.violations


def test_non_market_output_is_out_of_scope(auditor):
    audit = auditor("Independent records show the project shipped on 2026-10-11.")
    assert audit.status == "PASS"
    assert audit.violations == ()


def test_cli_returns_machine_readable_pass_and_fail(tmp_path, capsys):
    import sys

    sys.path.insert(0, str(SCRIPT_LIB))
    from lib import market_calibration

    good = tmp_path / "good.md"
    good.write_text(
        "As of 2026-10-11, Polymarket priced the contract at 51%. "
        "This market-implied trader expectation is not fact or verification.",
        encoding="utf-8",
    )
    assert market_calibration.main([str(good)]) == 0
    assert '"status": "PASS"' in capsys.readouterr().out

    bad = tmp_path / "bad.md"
    bad.write_text("Polymarket gives 96% confidence.", encoding="utf-8")
    assert market_calibration.main([str(bad)]) == 1
    output = capsys.readouterr().out
    assert '"status": "FAIL"' in output
    assert "ODDS_AS_FACTUAL_CONFIDENCE" in output
