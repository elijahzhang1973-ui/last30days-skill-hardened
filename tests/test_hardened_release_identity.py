"""Static identity contract for the governed hardened distribution."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from lib.skill_meta import read_skill_version


ROOT = Path(__file__).resolve().parents[1]
PACKAGE_VERSION = "3.27.2+hardened.1"
RELEASE_TAG = "v3.27.2-hardened.1"
CANONICAL_SKILL_ID = "last30days"
TARGET_REPOSITORY = (
    "https://github.com/elijahzhang1973-ui/last30days-skill-hardened"
)


def _json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_package_version_uses_pep440_and_semver_local_form() -> None:
    assert re.fullmatch(
        r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)"
        r"\+[0-9A-Za-z]+(?:[.-][0-9A-Za-z]+)*",
        PACKAGE_VERSION,
    )


def test_active_version_surfaces_are_lockstep() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    versions = {
        "pyproject": pyproject["project"]["version"],
        "skill": read_skill_version(ROOT / "skills" / "last30days" / "SKILL.md"),
        "claude": _json(".claude-plugin/plugin.json")["version"],
        "codex": _json(".codex-plugin/plugin.json")["version"],
        "grok": _json(".grok-plugin/plugin.json")["version"],
        "gemini": _json("gemini-extension.json")["version"],
        "mcp": _json("mcp/manifest.json")["version"],
        "claude_marketplace": _json(".claude-plugin/marketplace.json")["plugins"][0][
            "version"
        ],
        "grok_marketplace": _json(".grok-plugin/marketplace.json")["plugins"][0][
            "version"
        ],
    }
    assert set(versions.values()) == {PACKAGE_VERSION}, versions
    lock_text = (ROOT / "uv.lock").read_text(encoding="utf-8")
    assert re.search(
        rf'(?ms)^\[\[package\]\]\nname = "last30days-skill"\nversion = "{re.escape(PACKAGE_VERSION)}"$',
        lock_text,
    )


def test_canonical_skill_id_is_stable() -> None:
    skill_text = (ROOT / "skills" / "last30days" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert re.search(r"(?m)^name: last30days$", skill_text)
    assert _json(".codex-plugin/plugin.json")["name"] == CANONICAL_SKILL_ID
    assert _json(".claude-plugin/plugin.json")["name"] == CANONICAL_SKILL_ID
    assert _json(".grok-plugin/plugin.json")["name"] == CANONICAL_SKILL_ID


def test_static_identity_declares_release_to_package_mapping() -> None:
    identity = (ROOT / "VERSION_IDENTITY.md").read_text(encoding="utf-8")
    assert RELEASE_TAG in identity
    assert PACKAGE_VERSION in identity
    assert "267d50f7fcbab8a6457a93ad6ca15cbc199f633c" in identity
    assert "c2964132f3167cac73be03cf378bb74893492885" in identity
    assert "Candidate commits" in identity

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert f"## [{RELEASE_TAG.removeprefix('v')}] - " in changelog


def test_active_install_sources_point_to_hardened_repository() -> None:
    codex_source = _json(".agents/plugins/marketplace.json")["plugins"][0]["source"]
    grok_source = _json(".grok-plugin/marketplace.json")["plugins"][0]["source"]
    assert codex_source["url"] == f"{TARGET_REPOSITORY}.git"
    assert grok_source["url"] == f"{TARGET_REPOSITORY}.git"
    for relative in (
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        ".grok-plugin/plugin.json",
    ):
        manifest = _json(relative)
        assert manifest["homepage"] == TARGET_REPOSITORY
        assert manifest["repository"] == TARGET_REPOSITORY


def test_formal_package_has_no_dynamic_release_state() -> None:
    active = [
        ROOT / "VERSION_IDENTITY.md",
        ROOT / "pyproject.toml",
        ROOT / "uv.lock",
        ROOT / "skills" / "last30days" / "SKILL.md",
        ROOT / ".claude-plugin" / "plugin.json",
        ROOT / ".codex-plugin" / "plugin.json",
        ROOT / ".grok-plugin" / "plugin.json",
        ROOT / "gemini-extension.json",
        ROOT / "mcp" / "manifest.json",
    ]
    forbidden = ("published=false", "release-candidate", "hardened.0")
    for path in active:
        text = path.read_text(encoding="utf-8").lower()
        assert not any(token in text for token in forbidden), path
