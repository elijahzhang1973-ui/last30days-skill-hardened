#!/usr/bin/env python3
"""Fail closed unless Semgrep results exactly match an audited baseline."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "last30days-semgrep-baseline/v1"
ALLOWED_DISPOSITIONS = frozenset({"FALSE_POSITIVE", "NOT_APPLICABLE", "ACCEPTED_LIMITATION"})


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _key(value: dict[str, Any]) -> tuple[str, str, int, int]:
    try:
        return (
            str(value["check_id"]),
            str(value["path"]).replace("\\", "/"),
            int(value["line"]),
            int(value["col"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid finding identity: {value!r}") from exc


def _observed_key(value: dict[str, Any]) -> tuple[str, str, int, int]:
    try:
        return (
            str(value["check_id"]),
            str(value["path"]).replace("\\", "/"),
            int(value["start"]["line"]),
            int(value["start"]["col"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid Semgrep result identity: {value!r}") from exc


def validate(results_path: Path, baseline_path: Path) -> dict[str, Any]:
    results = _load(results_path)
    baseline = _load(baseline_path)
    if baseline.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Semgrep baseline schema mismatch")

    errors = results.get("errors")
    if not isinstance(errors, list):
        raise ValueError("Semgrep results errors field is missing or invalid")
    if errors:
        raise ValueError(f"Semgrep reported {len(errors)} scan error(s); baseline comparison refused")

    baseline_rows = baseline.get("findings")
    result_rows = results.get("results")
    if not isinstance(baseline_rows, list) or not isinstance(result_rows, list):
        raise ValueError("Semgrep baseline/results finding lists are missing or invalid")

    expected: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for row in baseline_rows:
        if not isinstance(row, dict):
            raise ValueError("Semgrep baseline finding must be an object")
        key = _key(row)
        if key in expected:
            raise ValueError(f"duplicate Semgrep baseline identity: {key}")
        if row.get("disposition") not in ALLOWED_DISPOSITIONS:
            raise ValueError(f"invalid Semgrep disposition for {key}")
        if not isinstance(row.get("rationale"), str) or not row["rationale"].strip():
            raise ValueError(f"missing Semgrep rationale for {key}")
        test_ids = row.get("test_ids")
        if not isinstance(test_ids, list) or not test_ids or not all(
            isinstance(test_id, str) and test_id.strip() for test_id in test_ids
        ):
            raise ValueError(f"missing Semgrep test IDs for {key}")
        expected[key] = row

    observed: dict[tuple[str, str, int, int], dict[str, Any]] = {}
    for row in result_rows:
        if not isinstance(row, dict):
            raise ValueError("Semgrep result must be an object")
        key = _observed_key(row)
        if key in observed:
            raise ValueError(f"duplicate Semgrep result identity: {key}")
        observed[key] = row

    missing = sorted(set(expected) - set(observed))
    unexpected = sorted(set(observed) - set(expected))
    if missing or unexpected:
        raise ValueError(
            "Semgrep baseline mismatch: "
            + json.dumps({"missing": missing, "unexpected": unexpected}, separators=(",", ":"))
        )

    return {
        "status": "PASS_WITH_TRIAGED_FINDINGS" if observed else "PASS",
        "findings": len(observed),
        "errors": 0,
        "dispositions": {
            disposition: sum(1 for row in expected.values() if row["disposition"] == disposition)
            for disposition in sorted(ALLOWED_DISPOSITIONS)
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    args = parser.parse_args()
    try:
        summary = validate(args.results, args.baseline)
    except ValueError as exc:
        print(f"Semgrep baseline validation failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
