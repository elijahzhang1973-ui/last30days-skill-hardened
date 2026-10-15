from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".github" / "scripts" / "build_install_manifest.py"
SPEC = importlib.util.spec_from_file_location("build_install_manifest", SCRIPT)
assert SPEC and SPEC.loader
manifest = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(manifest)


def _tree(root: Path, *, distribution: str = "v1+hardened.1") -> Path:
    root.mkdir()
    (root / "SKILL.md").write_text("---\nname: last30days\nversion: '1.0.0'\n---\n", encoding="utf-8")
    (root / "manifest.json").write_text(
        json.dumps(
            {
                "name": "last30days",
                "version": "1.0.0",
                "distribution_version": distribution,
                "status": "released",
                "published": True,
            }
        ),
        encoding="utf-8",
    )
    (root / "references").mkdir()
    (root / "references" / "b.txt").write_bytes(b"b")
    (root / "a.txt").write_bytes(b"a")
    return root


def test_snapshot_is_deterministic_and_uses_normalized_relative_paths(tmp_path):
    root = _tree(tmp_path / "skill")
    first = manifest.build_manifest(
        root,
        snapshot_role="before",
        expected_skill_id="last30days",
        expected_distribution_version="v1+hardened.1",
    )
    second = manifest.build_manifest(
        root,
        snapshot_role="verification",
        expected_skill_id="last30days",
        expected_distribution_version="v1+hardened.1",
    )
    assert first["content_identity"] == second["content_identity"]
    assert first["content_identity"]["algorithm"] == (
        "sha256(LF-joined path<TAB>size<TAB>uppercase-file-sha256; UTF-8; "
        "no trailing LF; paths sorted by Unicode-casefold then codepoint)"
    )
    assert all(entry["sha256"] == entry["sha256"].upper() for entry in first["files"])
    assert [entry["path"] for entry in first["files"]] == [
        "a.txt",
        "manifest.json",
        "references/b.txt",
        "SKILL.md",
    ]
    assert all("\\" not in entry["path"] for entry in first["files"])


def test_content_change_changes_aggregate_identity(tmp_path):
    root = _tree(tmp_path / "skill")
    before = manifest.snapshot_tree(root)[1]
    (root / "a.txt").write_bytes(b"changed")
    after = manifest.snapshot_tree(root)[1]
    assert before != after


def test_expected_distribution_mismatch_is_explicit_not_laundered(tmp_path):
    root = _tree(tmp_path / "skill", distribution="v1+hardened.1")
    payload = manifest.build_manifest(
        root,
        snapshot_role="before",
        expected_skill_id="last30days",
        expected_distribution_version="v1+hardened.2",
    )
    assert payload["identity"]["mismatches"] == [
        {
            "field": "manifest.distribution_version",
            "expected": "v1+hardened.2",
            "observed": "v1+hardened.1",
        }
    ]


def test_wrong_skill_id_fails_closed(tmp_path):
    root = _tree(tmp_path / "skill")
    with pytest.raises(manifest.ManifestError, match="canonical Skill ID mismatch"):
        manifest.build_manifest(
            root,
            snapshot_role="before",
            expected_skill_id="different-skill",
            expected_distribution_version=None,
        )


def test_detached_checksum_binds_exact_manifest_bytes(tmp_path):
    root = _tree(tmp_path / "skill")
    payload = manifest.build_manifest(
        root,
        snapshot_role="before",
        expected_skill_id="last30days",
        expected_distribution_version=None,
    )
    output, checksum = manifest.write_manifest(payload, tmp_path / "evidence" / "before.json")
    expected = hashlib.sha256(output.read_bytes()).hexdigest()
    assert checksum.read_text(encoding="ascii") == f"{expected}  before.json\n"


def test_snapshot_rejects_symlink_in_package(tmp_path, monkeypatch):
    root = _tree(tmp_path / "skill")
    link = root / "escape"
    link.write_text("fixture", encoding="utf-8")
    original = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda self: self == link or original(self),
    )
    with pytest.raises(manifest.ManifestError, match="symbolic links are not allowed"):
        manifest.snapshot_tree(root)
