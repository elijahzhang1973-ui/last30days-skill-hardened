"""Static policy gates for FU-015 and FU-016."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_fu015_optional_policy_has_every_required_field() -> None:
    policy = (ROOT / "OPTIONAL_FEATURE_POLICY.md").read_text(encoding="utf-8")
    header = next(line for line in policy.splitlines() if line.startswith("| Feature |"))
    for field in (
        "Default",
        "Credential required",
        "External destination and disclosed data",
        "Cost risk and cap",
        "Privacy risk",
        "Enable method",
        "Fallback and quality gate",
        "Owner / SLO / kill switch",
    ):
        assert field in header


def test_fu015_expansion_sources_are_governed_and_default_off() -> None:
    policy = (ROOT / "OPTIONAL_FEATURE_POLICY.md").read_text(encoding="utf-8")
    for feature in (
        "Telegram public channels",
        "Meta Ads",
        "Parallel hosted MCP",
        "ScrapeCreators social sources",
        "Official X API",
        "Browser-cookie X access",
        "Host WebSearch",
    ):
        assert f"| {feature} |" in policy
    assert "EXCLUDE_SOURCES" in policy
    assert "BLOCKED" in policy
    assert "NOT_RUN" in policy


def test_fu016_release_note_states_actual_mcp_and_websearch_contracts() -> None:
    note = (ROOT / "docs/releases/v3.27.2-hardened.1.md").read_text(encoding="utf-8")
    normalized = " ".join(note.split())
    assert "two tools: `preflight` and `research`" in note
    assert "trailing `Sources` section" in note
    assert "did not prove runtime process isolation" in normalized
    assert "https://github.com/mvanhorn/last30days-skill/pull/1250" in note
    assert "https://github.com/mvanhorn/last30days-skill/commit/77e42dd" in note
    assert "untrusted data" in note
