#!/usr/bin/env python3
"""Build a deterministic, read-only snapshot of an installed Skill tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
from typing import Any


SCHEMA_VERSION = "last30days-install-manifest/v1"


class ManifestError(RuntimeError):
    """The requested tree could not be snapshotted safely."""


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise ManifestError(f"cannot read required identity file: {path.name}") from exc
    if not lines or lines[0].strip() != "---":
        raise ManifestError("SKILL.md has no frontmatter")
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line or line[:1].isspace():
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def _json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ManifestError(f"cannot read required identity file: {path.name}") from exc
    if not isinstance(value, dict):
        raise ManifestError(f"required identity file is not an object: {path.name}")
    return value


def _file_record(root: Path, path: Path) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    before = path.stat()
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                size += len(chunk)
                digest.update(chunk)
    except OSError as exc:
        raise ManifestError(f"cannot read package file: {relative}") from exc
    after = path.stat()
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
        raise ManifestError(f"package file changed while hashing: {relative}")
    if size != before.st_size:
        raise ManifestError(f"package file size changed while hashing: {relative}")
    return {"path": relative, "size": size, "sha256": digest.hexdigest().upper()}


def snapshot_tree(root: Path) -> tuple[list[dict[str, Any]], str, int]:
    root = root.resolve(strict=True)
    if not root.is_dir():
        raise ManifestError("snapshot root is not a directory")
    records: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise ManifestError(f"symbolic links are not allowed: {path.relative_to(root).as_posix()}")
        if path.is_file():
            records.append(_file_record(root, path))
    records.sort(key=lambda entry: (entry["path"].casefold(), entry["path"]))
    canonical = b"\n".join(
        f"{entry['path']}\t{entry['size']}\t{entry['sha256']}".encode("utf-8")
        for entry in records
    )
    return records, _sha256_bytes(canonical), sum(entry["size"] for entry in records)


def build_manifest(
    root: Path,
    *,
    snapshot_role: str,
    expected_skill_id: str,
    expected_distribution_version: str | None,
) -> dict[str, Any]:
    resolved = root.resolve(strict=True)
    skill = _frontmatter(resolved / "SKILL.md")
    package = _json_object(resolved / "manifest.json")
    if skill.get("name") != expected_skill_id or package.get("name") != expected_skill_id:
        raise ManifestError("canonical Skill ID mismatch")
    files, aggregate, total_bytes = snapshot_tree(resolved)
    observed_distribution = package.get("distribution_version")
    mismatches: list[dict[str, Any]] = []
    if expected_distribution_version and observed_distribution != expected_distribution_version:
        mismatches.append(
            {
                "field": "manifest.distribution_version",
                "expected": expected_distribution_version,
                "observed": observed_distribution,
            }
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "snapshot_role": snapshot_role,
        "root": str(resolved),
        "identity": {
            "canonical_skill_id": expected_skill_id,
            "skill_version": skill.get("version"),
            "manifest_version": package.get("version"),
            "distribution_version": observed_distribution,
            "status": package.get("status"),
            "published": package.get("published"),
            "expected_distribution_version": expected_distribution_version,
            "mismatches": mismatches,
        },
        "content_identity": {
            "algorithm": "sha256(LF-joined path<TAB>size<TAB>uppercase-file-sha256; UTF-8; no trailing LF; paths sorted by Unicode-casefold then codepoint)",
            "aggregate_sha256": aggregate,
            "file_count": len(files),
            "total_bytes": total_bytes,
        },
        "files": files,
    }


def write_manifest(payload: dict[str, Any], output: Path) -> tuple[Path, Path]:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd, temporary_name = tempfile.mkstemp(prefix=f".{output.name}.", dir=output.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)
    checksum = output.with_suffix(output.suffix + ".sha256")
    checksum.write_text(f"{_sha256_bytes(data)}  {output.name}\n", encoding="ascii")
    return output, checksum


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot-role", choices=("before", "after", "verification"), required=True)
    parser.add_argument("--expected-skill-id", default="last30days")
    parser.add_argument("--expected-distribution-version")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve(strict=True)
    output = args.output.resolve()
    try:
        output.relative_to(root)
    except ValueError:
        pass
    else:
        raise ManifestError("manifest output must be outside the snapshotted tree")
    payload = build_manifest(
        root,
        snapshot_role=args.snapshot_role,
        expected_skill_id=args.expected_skill_id,
        expected_distribution_version=args.expected_distribution_version,
    )
    manifest_path, checksum_path = write_manifest(payload, output)
    print(
        json.dumps(
            {
                "manifest": str(manifest_path),
                "checksum": str(checksum_path),
                **payload["content_identity"],
                "identity_mismatches": len(payload["identity"]["mismatches"]),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
