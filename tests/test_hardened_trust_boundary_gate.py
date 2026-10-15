from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "trust-boundaries.json"
REGISTRY = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
BOUNDARIES = REGISTRY["boundaries"]
EXPECTED_IDS = {f"TB-{index:03d}" for index in range(1, 14)}
PROHIBITED_STATES = {"UNKNOWN", "PARTIAL", "DOCUMENTED_ONLY", "NOT_RUN"}


def _prefix(boundary_id: str) -> str:
    return "-".join(boundary_id.split("-")[:2])


def test_fu020_registry_covers_every_original_h007_edge_once():
    assert REGISTRY["schema_version"] == "last30days-trust-boundaries/v1"
    assert REGISTRY["patch_id"] == "H007"
    assert REGISTRY["follow_up_id"] == "FU-020"
    assert len(BOUNDARIES) == 13
    assert {_prefix(boundary["id"]) for boundary in BOUNDARIES} == EXPECTED_IDS
    assert len({boundary["id"] for boundary in BOUNDARIES}) == len(BOUNDARIES)


def test_fu020_has_no_unknown_or_partial_high_risk_boundary():
    for boundary in BOUNDARIES:
        assert boundary["risk"] == "HIGH"
        assert boundary["disposition"] not in PROHIBITED_STATES
        assert boundary["disposition"].startswith(("ENFORCED", "EXCLUDED"))
        assert boundary["data_origin"].strip()
        assert boundary["control_sink"].strip()


def test_fu020_every_boundary_maps_existing_control_and_test_files():
    for boundary in BOUNDARIES:
        assert boundary["control_files"]
        assert boundary["test_targets"]
        for relative in boundary["control_files"] + boundary["test_targets"]:
            path = ROOT / relative
            assert path.is_file(), f"{boundary['id']} missing {relative}"


def test_fu020_every_test_target_contains_executable_tests():
    for boundary in BOUNDARIES:
        for relative in boundary["test_targets"]:
            text = (ROOT / relative).read_text(encoding="utf-8")
            if relative.endswith(".py"):
                assert "def test_" in text or "unittest.TestCase" in text
            elif relative.endswith("_test.go"):
                assert "func Test" in text
            else:
                raise AssertionError(f"unsupported test target: {relative}")


def test_fu020_exclusions_are_narrow_and_match_platform_policy():
    excluded = {boundary["id"]: boundary["disposition"] for boundary in BOUNDARIES if boundary["disposition"].startswith("EXCLUDED") or "EXCLUDED" in boundary["disposition"]}
    assert excluded == {
        "TB-005-WEB-RESULT-HOST-INSTRUCTION": "EXCLUDED_CODEX_HOST_NATIVE_WEB",
        "TB-009-MCP-INPUT-ENGINE-ARGV": "ENFORCED_WINDOWS_MCPB_EXCLUDED",
    }
    platform = json.loads((ROOT / "platform-support.json").read_text(encoding="utf-8"))
    windows_mcp = next(
        entry
        for entry in platform["surfaces"]
        if entry["platform"] == "windows" and entry["surface"] == "mcpb"
    )
    assert windows_mcp["release_supported"] == "NO"
    assert windows_mcp["excluded"] == "YES"


def test_fu020_release_gate_language_is_fail_closed():
    gate = REGISTRY["release_gate"]
    assert "Every boundary" in gate
    assert "executable tests" in gate
    assert "no UNKNOWN high-risk state" in gate
