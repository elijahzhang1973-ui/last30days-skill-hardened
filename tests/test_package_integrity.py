from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "last30days"
MODULE_PATH = SKILL_ROOT / "scripts" / "package_integrity.py"
SPEC = importlib.util.spec_from_file_location("package_integrity_under_test", MODULE_PATH)
assert SPEC and SPEC.loader
integrity = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(integrity)


def _copy_package(tmp_path: Path) -> Path:
    destination = tmp_path / "last30days"
    for relative in (*integrity.REQUIRED_HASH_PATHS, integrity.MANIFEST_NAME):
        source = SKILL_ROOT / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    return destination


def test_repository_package_integrity_passes():
    result = integrity.verify_package(SKILL_ROOT)
    assert result == {
        "status": "PASS",
        "skill_id": "last30days",
        "package_version": "3.27.2+hardened.1",
        "verified_files": len(integrity.REQUIRED_HASH_PATHS),
    }


def test_manifest_reference_set_matches_root_contract_and_directory():
    root_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    linked = {f"references/{name}" for name in re.findall(r"references/([A-Za-z0-9_.-]+)", root_text)}
    present = {
        path.relative_to(SKILL_ROOT).as_posix()
        for path in (SKILL_ROOT / "references").glob("*.md")
    }
    assert linked == present == set(integrity.REQUIRED_REFERENCE_PATHS)


def test_missing_required_reference_fails_closed(tmp_path):
    package = _copy_package(tmp_path)
    (package / integrity.REQUIRED_REFERENCE_PATHS[0]).unlink()
    with pytest.raises(integrity.PackageIntegrityError, match="unreadable"):
        integrity.verify_package(package)


def test_unreadable_required_reference_fails_closed(tmp_path, monkeypatch):
    package = _copy_package(tmp_path)
    blocked = package / integrity.REQUIRED_REFERENCE_PATHS[1]
    original = integrity._read_bytes

    def deny(path: Path) -> bytes:
        if path == blocked:
            raise integrity.PackageIntegrityError("required package file is unreadable: fixture")
        return original(path)

    monkeypatch.setattr(integrity, "_read_bytes", deny)
    with pytest.raises(integrity.PackageIntegrityError, match="unreadable"):
        integrity.verify_package(package)


def test_wrong_root_fails_closed(tmp_path):
    package = _copy_package(tmp_path)
    wrong = tmp_path / "renamed-skill"
    package.rename(wrong)
    with pytest.raises(integrity.PackageIntegrityError, match="root mismatch"):
        integrity.verify_package(wrong)


def test_skill_version_mismatch_fails_closed(tmp_path):
    package = _copy_package(tmp_path)
    manifest_path = package / integrity.MANIFEST_NAME
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value["package_version"] = "3.27.2+hardened.other"
    manifest_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(integrity.PackageIntegrityError, match="package version mismatch"):
        integrity.verify_package(package)


def test_content_hash_mismatch_fails_closed(tmp_path):
    package = _copy_package(tmp_path)
    target = package / integrity.REQUIRED_REFERENCE_PATHS[2]
    target.write_bytes(target.read_bytes() + b"\nchanged")
    with pytest.raises(integrity.PackageIntegrityError, match="size mismatch"):
        integrity.verify_package(package)


def test_manifest_cannot_drop_a_required_file(tmp_path):
    package = _copy_package(tmp_path)
    manifest_path = package / integrity.MANIFEST_NAME
    value = json.loads(manifest_path.read_text(encoding="utf-8"))
    value["files"] = value["files"][:-1]
    manifest_path.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(integrity.PackageIntegrityError, match="required-file set mismatch"):
        integrity.verify_package(package)


def test_startup_hook_precedes_all_lib_imports():
    text = (SKILL_ROOT / "scripts" / "last30days.py").read_text(encoding="utf-8")
    verify_at = text.index("package_integrity.verify_runtime(SCRIPT_DIR)")
    lib_import_at = text.index("from lib import")
    assert verify_at < lib_import_at


def test_manifest_hashes_are_exact_for_all_required_files():
    value = json.loads((SKILL_ROOT / integrity.MANIFEST_NAME).read_text(encoding="utf-8"))
    records = {entry["path"]: entry for entry in value["files"]}
    assert set(records) == set(integrity.REQUIRED_HASH_PATHS)
    for relative, record in records.items():
        data = (SKILL_ROOT / relative).read_bytes()
        assert record["size"] == len(data)
        assert record["sha256"] == hashlib.sha256(data).hexdigest()


def test_real_cli_runs_integrity_preflight_before_help():
    completed = subprocess.run(
        [sys.executable, str(SKILL_ROOT / "scripts" / "last30days.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "usage: last30days.py" in completed.stdout


def test_real_cli_missing_reference_stops_before_lib_import(tmp_path):
    package = _copy_package(tmp_path)
    (package / integrity.REQUIRED_REFERENCE_PATHS[0]).unlink()
    completed = subprocess.run(
        [sys.executable, str(package / "scripts" / "last30days.py"), "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        check=False,
    )
    assert completed.returncode == 1
    assert completed.stdout == ""
    assert "package integrity check failed" in completed.stderr
    assert "No module named 'lib'" not in completed.stderr


def test_vendored_engine_layout_has_independent_integrity_gate(tmp_path):
    scripts = tmp_path / "vendored"
    scripts.mkdir()
    for name in ("last30days.py", "package_integrity.py", "engine-integrity.json"):
        shutil.copyfile(SKILL_ROOT / "scripts" / name, scripts / name)
    result = integrity.verify_runtime(scripts)
    assert result["layout"] == "mcp-vendored-engine"
    assert result["verified_files"] == 2


def test_vendored_engine_layout_fails_on_entrypoint_drift(tmp_path):
    scripts = tmp_path / "vendored"
    scripts.mkdir()
    for name in ("last30days.py", "package_integrity.py", "engine-integrity.json"):
        shutil.copyfile(SKILL_ROOT / "scripts" / name, scripts / name)
    (scripts / "last30days.py").write_bytes((scripts / "last30days.py").read_bytes() + b"\nchanged")
    with pytest.raises(integrity.PackageIntegrityError, match="size mismatch"):
        integrity.verify_runtime(scripts)
