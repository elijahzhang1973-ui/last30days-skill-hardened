"""Fail-closed integrity preflight for the governed Skill package."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "last30days-package-integrity/v1"
SKILL_ID = "last30days"
PACKAGE_VERSION = "3.27.2+hardened.1"
MANIFEST_NAME = "package-integrity.json"
ENGINE_MANIFEST_NAME = "engine-integrity.json"
REQUIRED_REFERENCE_PATHS = (
    "references/agent-mode.md",
    "references/category-peers.md",
    "references/codex-host.md",
    "references/comparison.md",
    "references/competitors.md",
    "references/discovery.md",
    "references/followups.md",
    "references/grok-bot-x.md",
    "references/hiring-signals.md",
    "references/library-queue.md",
    "references/recommendations.md",
    "references/research-runbook.md",
    "references/runtime.md",
    "references/save-html-brief.md",
    "references/setup-wizard.md",
    "references/synthesis.md",
)
REQUIRED_HASH_PATHS = (
    "SKILL.md",
    "scripts/engine-integrity.json",
    "scripts/last30days.py",
    "scripts/package_integrity.py",
    *REQUIRED_REFERENCE_PATHS,
)


class PackageIntegrityError(RuntimeError):
    """The Skill package is incomplete, misplaced, unreadable, or altered."""


def _read_bytes(path: Path) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise PackageIntegrityError(f"required package file is unreadable: {path.name}") from exc


def _load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_NAME
    try:
        value = json.loads(_read_bytes(path).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PackageIntegrityError("integrity manifest is invalid") from exc
    if not isinstance(value, dict):
        raise PackageIntegrityError("integrity manifest is not an object")
    return value


def _skill_frontmatter_version(data: bytes) -> tuple[str | None, str | None]:
    try:
        lines = data.decode("utf-8").splitlines()
    except UnicodeError as exc:
        raise PackageIntegrityError("SKILL.md is not valid UTF-8") from exc
    if not lines or lines[0].strip() != "---":
        raise PackageIntegrityError("SKILL.md frontmatter is missing")
    found: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        found[key.strip()] = value.strip().strip("\"'")
    return found.get("name"), found.get("version")


def _validated_records(manifest: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if manifest.get("schema_version") != SCHEMA_VERSION:
        raise PackageIntegrityError("integrity manifest schema mismatch")
    if manifest.get("skill_id") != SKILL_ID:
        raise PackageIntegrityError("integrity manifest Skill ID mismatch")
    if manifest.get("package_version") != PACKAGE_VERSION:
        raise PackageIntegrityError("integrity manifest package version mismatch")
    values = manifest.get("files")
    if not isinstance(values, list):
        raise PackageIntegrityError("integrity manifest file list is invalid")
    records: dict[str, dict[str, Any]] = {}
    for value in values:
        if not isinstance(value, dict):
            raise PackageIntegrityError("integrity manifest file record is invalid")
        relative = value.get("path")
        if not isinstance(relative, str) or not relative or "\\" in relative:
            raise PackageIntegrityError("integrity manifest path is invalid")
        pure = Path(relative)
        if pure.is_absolute() or ".." in pure.parts or relative in records:
            raise PackageIntegrityError("integrity manifest path is invalid")
        if not isinstance(value.get("size"), int) or value["size"] < 0:
            raise PackageIntegrityError("integrity manifest size is invalid")
        digest = value.get("sha256")
        if not isinstance(digest, str) or len(digest) != 64:
            raise PackageIntegrityError("integrity manifest digest is invalid")
        try:
            int(digest, 16)
        except ValueError as exc:
            raise PackageIntegrityError("integrity manifest digest is invalid") from exc
        records[relative] = value
    if tuple(sorted(records)) != tuple(sorted(REQUIRED_HASH_PATHS)):
        raise PackageIntegrityError("integrity manifest required-file set mismatch")
    return records


def verify_package(skill_root: Path | None = None) -> dict[str, Any]:
    root = (skill_root or Path(__file__).resolve().parents[1]).resolve(strict=True)
    if root.name != SKILL_ID or not root.is_dir():
        raise PackageIntegrityError("Skill package root mismatch")
    records = _validated_records(_load_manifest(root))
    for relative in REQUIRED_HASH_PATHS:
        path = root / Path(relative)
        if path.is_symlink():
            raise PackageIntegrityError(f"required package file is a symbolic link: {relative}")
        data = _read_bytes(path)
        record = records[relative]
        if len(data) != record["size"]:
            raise PackageIntegrityError(f"required package file size mismatch: {relative}")
        if hashlib.sha256(data).hexdigest() != record["sha256"].lower():
            raise PackageIntegrityError(f"required package file hash mismatch: {relative}")
    name, version = _skill_frontmatter_version(_read_bytes(root / "SKILL.md"))
    if name != SKILL_ID or version != PACKAGE_VERSION:
        raise PackageIntegrityError("SKILL.md identity mismatch")
    return {
        "status": "PASS",
        "skill_id": SKILL_ID,
        "package_version": PACKAGE_VERSION,
        "verified_files": len(records),
    }


def verify_engine_bundle(script_dir: Path) -> dict[str, Any]:
    root = script_dir.resolve(strict=True)
    manifest = _load_named_manifest(root / ENGINE_MANIFEST_NAME)
    if manifest.get("schema_version") != "last30days-engine-integrity/v1":
        raise PackageIntegrityError("engine integrity manifest schema mismatch")
    if manifest.get("skill_id") != SKILL_ID or manifest.get("package_version") != PACKAGE_VERSION:
        raise PackageIntegrityError("engine integrity identity mismatch")
    values = manifest.get("files")
    if not isinstance(values, list):
        raise PackageIntegrityError("engine integrity file list is invalid")
    records = {value.get("path"): value for value in values if isinstance(value, dict)}
    expected = {"last30days.py", "package_integrity.py"}
    if set(records) != expected:
        raise PackageIntegrityError("engine integrity required-file set mismatch")
    for relative in sorted(expected):
        record = records[relative]
        path = root / relative
        data = _read_bytes(path)
        if path.is_symlink() or record.get("size") != len(data):
            raise PackageIntegrityError(f"engine file size mismatch: {relative}")
        digest = record.get("sha256")
        if not isinstance(digest, str) or hashlib.sha256(data).hexdigest() != digest.lower():
            raise PackageIntegrityError(f"engine file hash mismatch: {relative}")
    return {
        "status": "PASS",
        "skill_id": SKILL_ID,
        "package_version": PACKAGE_VERSION,
        "verified_files": len(records),
        "layout": "mcp-vendored-engine",
    }


def _load_named_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(_read_bytes(path).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise PackageIntegrityError("integrity manifest is invalid") from exc
    if not isinstance(value, dict):
        raise PackageIntegrityError("integrity manifest is not an object")
    return value


def verify_runtime(script_dir: Path | None = None) -> dict[str, Any]:
    scripts = (script_dir or Path(__file__).resolve().parent).resolve(strict=True)
    skill_root = scripts.parent
    if (skill_root / "SKILL.md").is_file() and (skill_root / MANIFEST_NAME).is_file():
        return verify_package(skill_root)
    if (scripts / ENGINE_MANIFEST_NAME).is_file():
        return verify_engine_bundle(scripts)
    raise PackageIntegrityError("no recognized package integrity root")
