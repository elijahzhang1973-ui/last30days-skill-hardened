from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "release.yml"


def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")


def test_rc_tags_are_validation_checkpoints_not_formal_releases() -> None:
    text = _workflow_text()

    assert '- "!v*-rc*"' in text
    assert "Reject release-candidate dispatches" in text
    assert '*-rc*)' in text
    assert "needs: release-guard" in text
    assert "needs: [release-guard, build-skill, build-mcpb]" in text


def test_formal_release_has_governed_identity_and_scope_notes() -> None:
    text = _workflow_text()

    assert '--title "last30days ${RELEASE_TAG} (unofficial)"' in text
    assert "--notes-file dist/release-notes.md" in text
    assert "Unofficial governed hardened distribution." in text
    assert "Based exactly on upstream v3.27.2." in text
    assert "267d50f7fcbab8a6457a93ad6ca15cbc199f633c" in text
    assert "c2964132f3167cac73be03cf378bb74893492885" in text
    assert 'candidate_commit="$(git rev-parse HEAD)"' in text
    assert 'candidate_tree="$(git rev-parse \'HEAD^{tree}\')"' in text
    assert "sha256sum dist/last30days.skill" in text
    assert "sha256sum dist/last30days-pp-mcp-linux-amd64.mcpb" in text
    assert "Missing evidence:" in text
    assert "Windows and macOS MCPB artifacts and host-E2E claims are excluded" in text
    assert "--generate-notes" not in text
