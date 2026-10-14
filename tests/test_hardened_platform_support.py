"""Static release-scope contract for FU-009."""

from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _policy() -> dict:
    return json.loads((ROOT / "platform-support.json").read_text(encoding="utf-8"))


def _mcpb_rows() -> dict[tuple[str, str], dict]:
    return {
        (row["platform"], row["architecture"]): row
        for row in _policy()["surfaces"]
        if row["surface"] == "mcpb"
    }


def _release_matrix() -> set[tuple[str, str]]:
    workflow = (ROOT / ".github/workflows/release.yml").read_text(encoding="utf-8")
    return set(
        re.findall(
            r"- goos:\s*([a-z0-9_-]+)\s*\n\s*goarch:\s*([a-z0-9_-]+)",
            workflow,
        )
    )


def test_fu009_windows_mcpb_is_explicitly_excluded() -> None:
    row = _mcpb_rows()[("windows", "any")]
    assert row == {
        "surface": "mcpb",
        "platform": "windows",
        "architecture": "any",
        "source_supported": "NOT_ESTABLISHED",
        "unit_tested": "NO",
        "integration_tested": "NO",
        "host_e2e_verified": "NO",
        "release_supported": "NO",
        "excluded": "YES",
    }


def test_fu009_manifest_claims_only_the_verified_linux_target() -> None:
    manifest = json.loads((ROOT / "mcp/manifest.json").read_text(encoding="utf-8"))
    assert manifest["compatibility"]["platforms"] == ["linux"]


def test_fu009_release_matrix_is_linux_amd64_only() -> None:
    assert _release_matrix() == {("linux", "amd64")}


def test_fu009_policy_manifest_and_workflow_crosscheck() -> None:
    conditional = {
        key
        for key, row in _mcpb_rows().items()
        if row["release_supported"] == "CONDITIONAL_G5"
        and row["excluded"] == "NO"
    }
    assert conditional == _release_matrix()
    assert all(platform != "windows" for platform, _arch in conditional)


def test_fu009_docs_exclude_unverified_hosts_without_qualified_claims() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    matrix = (ROOT / "PLATFORM_SUPPORT.md").read_text(encoding="utf-8")
    assert "Windows and macOS are excluded" in readme
    assert "release-supported only on Linux" in readme
    assert "Only Linux Skill/Python and Linux amd64 MCPB" in matrix
    assert "SUPPORTED_WITH_LIMITATION" not in readme + matrix
    assert "NOT_FULLY_VALIDATED" not in readme + matrix


def test_fu009_unverified_skill_and_macos_surfaces_are_excluded() -> None:
    rows = {
        (row["surface"], row["platform"], row["architecture"]): row
        for row in _policy()["surfaces"]
    }
    for key in (
        ("skill-python", "windows", "any"),
        ("skill-python", "darwin", "any"),
        ("macos-keychain", "darwin", "any"),
        ("mcpb", "darwin", "arm64"),
        ("mcpb", "darwin", "amd64"),
    ):
        assert rows[key]["release_supported"] == "NO"
        assert rows[key]["excluded"] == "YES"


def test_fu009_mcp_docs_match_the_two_registered_tools() -> None:
    readme = (ROOT / "mcp/README.md").read_text(encoding="utf-8")
    assert "two tools" in readme
    assert "`preflight`" in readme
    assert "`research`" in readme
    assert "single `research` tool" not in readme


def test_fu009_reopen_guard_has_all_scope_expansion_triggers() -> None:
    triggers = _policy()["reopen_conditions"]["windows_mcpb"]
    joined = " ".join(triggers).lower()
    for token in ("win32", "goos", "artifact", "support claim"):
        assert token in joined
