import copy
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
CHECKER_PATH = ROOT / ".github" / "scripts" / "validate_semgrep_baseline.py"
BASELINE_PATH = ROOT / ".github" / "semgrep-baseline.json"

spec = importlib.util.spec_from_file_location("validate_semgrep_baseline", CHECKER_PATH)
checker = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(checker)


def _baseline() -> dict:
    return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


def _results_from_baseline(baseline: dict) -> dict:
    return {
        "errors": [],
        "results": [
            {
                "check_id": row["check_id"],
                "path": row["path"],
                "start": {"line": row["line"], "col": row["col"]},
                "extra": {"severity": "ERROR"},
            }
            for row in baseline["findings"]
        ],
    }


def _write_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value), encoding="utf-8")


def test_repository_baseline_is_unique_and_fully_dispositioned(tmp_path: Path) -> None:
    baseline = _baseline()
    results = _results_from_baseline(baseline)
    results_path = tmp_path / "results.json"
    _write_json(results_path, results)

    summary = checker.validate(results_path, BASELINE_PATH)

    assert summary["status"] == "PASS_WITH_TRIAGED_FINDINGS"
    assert summary["findings"] == 18
    assert summary["errors"] == 0
    assert summary["dispositions"] == {
        "ACCEPTED_LIMITATION": 0,
        "FALSE_POSITIVE": 16,
        "NOT_APPLICABLE": 2,
    }


@pytest.mark.parametrize("mutation", ["new", "missing", "drift"])
def test_baseline_rejects_any_finding_set_change(tmp_path: Path, mutation: str) -> None:
    baseline = _baseline()
    results = _results_from_baseline(baseline)
    if mutation == "new":
        results["results"].append({
            "check_id": "new.rule",
            "path": "new.py",
            "start": {"line": 1, "col": 1},
        })
    elif mutation == "missing":
        results["results"].pop()
    else:
        results["results"][0]["start"]["line"] += 1
    results_path = tmp_path / "results.json"
    _write_json(results_path, results)

    with pytest.raises(ValueError, match="baseline mismatch"):
        checker.validate(results_path, BASELINE_PATH)


def test_baseline_rejects_scan_errors_before_comparison(tmp_path: Path) -> None:
    results = _results_from_baseline(_baseline())
    results["errors"] = [{"type": "PartialParsing", "message": "parser failed"}]
    results_path = tmp_path / "results.json"
    _write_json(results_path, results)

    with pytest.raises(ValueError, match="scan error"):
        checker.validate(results_path, BASELINE_PATH)


def test_baseline_rejects_duplicate_identity(tmp_path: Path) -> None:
    baseline = _baseline()
    duplicate = copy.deepcopy(baseline["findings"][0])
    baseline["findings"].append(duplicate)
    baseline_path = tmp_path / "baseline.json"
    results_path = tmp_path / "results.json"
    _write_json(baseline_path, baseline)
    _write_json(results_path, _results_from_baseline(baseline))

    with pytest.raises(ValueError, match="duplicate Semgrep baseline"):
        checker.validate(results_path, baseline_path)
