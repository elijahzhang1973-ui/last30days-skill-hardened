"""Deterministic output checks for prediction-market calibration.

The synthesis itself is produced by the host.  This module provides a bounded,
offline evaluator for release tests and downstream publishers that need to
reject common category errors before presenting market-derived language.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Sequence


_MARKET = re.compile(
    r"(?:polymarket|prediction[- ]market|market[- ]implied|"
    r"预测市场|市场隐含|赔率|mercado\s+de\s+predicci[oó]n|impl[ií]cit[ao]\s+por\s+el\s+mercado)",
    re.IGNORECASE,
)
_PERCENT = re.compile(r"\b\d{1,3}(?:[.,]\d+)?\s*%")
_TIMESTAMP = re.compile(
    r"(?:\b20\d{2}-\d{2}-\d{2}\b|\bas\s+of\b|\bat\s+\d{1,2}:\d{2}\b|"
    r"截至|采集于|\ba\s+fecha\s+de\b|\bal\s+\d{1,2}\s+de\b)",
    re.IGNORECASE,
)
_EXPECTATION = re.compile(
    r"(?:trader[- ]expectation|market[- ]implied|交易者预期|市场隐含|"
    r"expectativas?\s+de\s+(?:los\s+)?(?:operadores|participantes)|impl[ií]cit[ao]\s+por\s+el\s+mercado)",
    re.IGNORECASE,
)
_NOT_TRUTH = re.compile(
    r"(?:not\s+(?:a\s+)?(?:fact|truth|verification|model\s+confidence)|"
    r"does\s+not\s+(?:prove|verify|establish)|"
    r"(?:不是|不代表|不能证明|并非)(?:事实|真相|独立核验|模型置信度)|"
    r"no\s+es\s+(?:un\s+)?(?:hecho|verdad|verificaci[oó]n)|"
    r"no\s+(?:demuestra|verifica|establece))",
    re.IGNORECASE,
)
_FORBIDDEN = (
    re.compile(r"(?:polymarket|market|odds).{0,48}\b\d{1,3}(?:[.,]\d+)?\s*%\s+(?:confidence|certain)", re.IGNORECASE),
    re.compile(r"\b\d{1,3}(?:[.,]\d+)?\s*%\s+(?:confidence|certain)\b", re.IGNORECASE),
    re.compile(r"(?:market|odds).{0,64}(?:proves?|confirms?)\s+(?:it|this|that).{0,16}(?:true|fact)", re.IGNORECASE),
    re.compile(r"(?:赔率|市场).{0,32}\d{1,3}(?:[.,]\d+)?\s*%\s*(?:置信度|确定|真实性|事实概率)", re.IGNORECASE),
    re.compile(r"\d{1,3}(?:[.,]\d+)?\s*%\s*(?:的?置信度|确定为真|事实概率)", re.IGNORECASE),
    re.compile(r"(?:mercado|cuotas?).{0,48}\d{1,3}(?:[.,]\d+)?\s*%\s+de\s+(?:confianza|certeza)", re.IGNORECASE),
    re.compile(r"\d{1,3}(?:[.,]\d+)?\s*%\s+de\s+(?:confianza|certeza|probabilidad\s+de\s+verdad)", re.IGNORECASE),
)
_HIGH_RISK = re.compile(
    r"(?:election|vote|war|strike|invasion|public\s+safety|health|medical|treatment|"
    r"legal|lawsuit|financial|investment|stock|crypto|"
    r"选举|投票|战争|袭击|公共安全|健康|医疗|治疗|法律|诉讼|金融|投资|股票|加密|"
    r"elecci[oó]n|votar|guerra|ataque|salud|m[eé]dic|tratamiento|legal|inversi[oó]n|acciones|cripto)",
    re.IGNORECASE,
)
_CORROBORATED = re.compile(
    r"(?:independent\s+non-market\s+(?:primary|authoritative\s+)?source|independently\s+corroborated|"
    r"独立非市场(?:一手|权威)?来源|经独立(?:一手|非市场|权威)来源核验|"
    r"fuente\s+independiente\s+(?:primaria\s+)?ajena\s+al\s+mercado|corroborad[oa]\s+independientemente)",
    re.IGNORECASE,
)
_UNCORROBORATED = re.compile(
    r"(?:uncorroborated|not\s+independently\s+(?:verified|corroborated)|"
    r"未获独立(?:来源)?(?:核验|佐证)|未经独立(?:来源)?(?:核验|佐证)|"
    r"sin\s+corroboraci[oó]n\s+independiente|no\s+verificad[oa]\s+independientemente)",
    re.IGNORECASE,
)
_ACTION = re.compile(
    r"(?:\b(?:recommend|should|must|buy|sell|vote|trade|invest|take\s+this\s+treatment)\b|"
    r"建议|应该|必须|买入|卖出|投票给|交易|投资|接受治疗|"
    r"\b(?:recomiend[oa]|deber[ií]a|debe|comprar|vender|votar|invertir)\b)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class CalibrationAudit:
    status: str
    violations: tuple[str, ...]


def audit_market_language(text: str) -> CalibrationAudit:
    """Return PASS unless market language violates the release contract."""

    if not (_MARKET.search(text) and _PERCENT.search(text)):
        return CalibrationAudit("PASS", ())

    violations: list[str] = []
    if any(pattern.search(text) for pattern in _FORBIDDEN):
        violations.append("ODDS_AS_FACTUAL_CONFIDENCE")
    if not _EXPECTATION.search(text):
        violations.append("MISSING_MARKET_EXPECTATION_LABEL")
    if not _NOT_TRUTH.search(text):
        violations.append("MISSING_NOT_TRUTH_CALIBRATION")
    if not _TIMESTAMP.search(text):
        violations.append("MISSING_OBSERVATION_TIME")

    if _HIGH_RISK.search(text):
        has_corroboration = bool(_CORROBORATED.search(text))
        admits_no_corroboration = bool(_UNCORROBORATED.search(text))
        if not (has_corroboration or admits_no_corroboration):
            violations.append("MISSING_HIGH_RISK_CORROBORATION_STATUS")
        if admits_no_corroboration and _ACTION.search(text):
            violations.append("ACTION_FROM_UNCORROBORATED_ODDS")

    return CalibrationAudit("FAIL" if violations else "PASS", tuple(violations))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit prediction-market language in a synthesis file.")
    parser.add_argument("path", type=Path)
    args = parser.parse_args(argv)
    try:
        text = args.path.read_text(encoding="utf-8")
    except OSError as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False))
        return 2
    audit = audit_market_language(text)
    print(json.dumps(asdict(audit), ensure_ascii=False))
    return 0 if audit.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
