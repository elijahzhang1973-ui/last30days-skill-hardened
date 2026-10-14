"""H003 / FU-003 secret-material boundary tests."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from lib import env


ROOT = Path(__file__).resolve().parents[1]
KEYCHAIN_SCRIPT = ROOT / "skills" / "last30days" / "scripts" / "setup-keychain.sh"
PASS_SCRIPT = ROOT / "skills" / "last30days" / "scripts" / "setup-pass.sh"

SECRET_CASES = (
    "space secret",
    'quote\"single\'secret',
    "dollar$backtick`slash\\",
    "line-one\nline-two",
    "秘密-🔐-credential",
    "x" * 65536,
)


def _shell_code(path: Path) -> str:
    return "\n".join(
        line
        for line in path.read_text(encoding="utf-8").splitlines()
        if not line.lstrip().startswith("#")
    )


def _bash() -> str | None:
    found = shutil.which("bash")
    if found:
        return found
    if os.name == "nt":
        candidate = Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Git" / "bin" / "bash.exe"
        if candidate.is_file():
            return str(candidate)
    return None


def _run_bash_helper(script: Path, stub_dir: Path, args: list[str], *, stdin: str, env: dict[str, str]):
    bash = _bash()
    if not bash:
        pytest.skip("bash unavailable for shell-helper integration test")
    if os.name == "nt":
        wrapper = (
            'script=$(/usr/bin/cygpath -u "$1"); '
            'stub=$(/usr/bin/cygpath -u "$2"); '
            'STUB_ARGV_LOG=$(/usr/bin/cygpath -u "$STUB_ARGV_LOG"); '
            'STUB_STDIN_LOG=$(/usr/bin/cygpath -u "$STUB_STDIN_LOG"); '
            'export STUB_ARGV_LOG STUB_STDIN_LOG; '
            'OSTYPE=darwin; export OSTYPE; PATH="$stub:/usr/bin"; export PATH; '
            'shift 2; exec "$script" "$@"'
        )
    else:
        wrapper = (
            'OSTYPE=darwin; export OSTYPE; PATH="$2:$PATH"; export PATH; '
            'script="$1"; shift 2; exec "$script" "$@"'
        )
    return subprocess.run(
        [bash, "--noprofile", "--norc", "-c", wrapper, "fixture", str(script), str(stub_dir), *args],
        input=stdin,
        text=True,
        capture_output=True,
        timeout=15,
        env=env,
    )


def test_h003_shell_sources_never_place_value_in_secret_command_argv():
    """TEST_ID=H003-ARGV-001."""
    keychain = _shell_code(KEYCHAIN_SCRIPT)
    password_store = _shell_code(PASS_SCRIPT)
    assert '-w "$value"' not in keychain
    assert 'pass insert -m -f "${PREFIX}${key}" "$value"' not in password_store
    assert "printf '%s\\n%s\\n' \"$value\" \"$value\" |" in keychain
    assert "printf '%s\\n' \"$value\" | pass insert" in password_store


def test_h003_presence_contract_has_only_non_secret_states():
    """TEST_ID=H003-PRESENCE-001."""
    allowed = {"CONFIGURED", "ABSENT", "INACCESSIBLE", "UNKNOWN"}
    assert allowed == {"CONFIGURED", "ABSENT", "INACCESSIBLE", "UNKNOWN"}
    assert "find-generic-password -a \"$USER\" -s \"${PREFIX}${key}\" -w" not in _shell_code(KEYCHAIN_SCRIPT)
    assert "pass show" not in _shell_code(PASS_SCRIPT)


@pytest.mark.parametrize(
    "secret",
    SECRET_CASES,
    ids=("spaces", "quotes", "shell-metacharacters", "multiline", "unicode", "very-long"),
)
def test_h003_keychain_writer_runtime_keeps_secret_off_argv_and_output(tmp_path, secret):
    """TEST_ID=H003-KEYCHAIN-002: execute the helper against a stub security CLI."""
    stub = tmp_path / "security"
    stub.write_text(
        "#!/bin/sh\n"
        "printf '%s\\0' \"$@\" >> \"$STUB_ARGV_LOG\"\n"
        "case \"$1\" in\n"
        "  find-generic-password) exit 44 ;;\n"
        "  add-generic-password) /usr/bin/cat > \"$STUB_STDIN_LOG\"; exit 0 ;;\n"
        "  *) exit 99 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    argv_log = tmp_path / "argv.bin"
    stdin_log = tmp_path / "stdin.bin"
    run_env = {
        **os.environ,
        "USER": "fixture-user",
        "STUB_ARGV_LOG": str(argv_log),
        "STUB_STDIN_LOG": str(stdin_log),
    }
    result = _run_bash_helper(
        KEYCHAIN_SCRIPT,
        tmp_path,
        ["OPENAI_API_KEY"],
        stdin=secret + "\n",
        env=run_env,
    )
    assert result.returncode == 0, result.stderr
    observable = result.stdout + result.stderr + argv_log.read_bytes().decode("utf-8", errors="replace")
    for fragment in secret.splitlines() or [secret]:
        assert fragment not in observable
    expected = secret.splitlines()[0] if secret.splitlines() else secret
    assert stdin_log.read_text(encoding="utf-8") == f"{expected}\n{expected}\n"


@pytest.mark.parametrize(
    "secret",
    SECRET_CASES,
    ids=("spaces", "quotes", "shell-metacharacters", "multiline", "unicode", "very-long"),
)
def test_h003_pass_writer_runtime_uses_metadata_presence_and_stdin(tmp_path, secret):
    """TEST_ID=H003-PASS-002: execute the helper against a stub pass CLI."""
    stub = tmp_path / "pass"
    stub.write_text(
        "#!/bin/sh\n"
        "printf '%s\\0' \"$@\" >> \"$STUB_ARGV_LOG\"\n"
        "case \"$1\" in\n"
        "  ls) exit 1 ;;\n"
        "  insert) /usr/bin/cat > \"$STUB_STDIN_LOG\"; exit 0 ;;\n"
        "  show) exit 98 ;;\n"
        "  *) exit 99 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)
    argv_log = tmp_path / "argv.bin"
    stdin_log = tmp_path / "stdin.bin"
    run_env = {
        **os.environ,
        "USER": "fixture-user",
        "STUB_ARGV_LOG": str(argv_log),
        "STUB_STDIN_LOG": str(stdin_log),
    }
    result = _run_bash_helper(
        PASS_SCRIPT,
        tmp_path,
        ["OPENAI_API_KEY"],
        stdin=secret + "\n",
        env=run_env,
    )
    assert result.returncode == 0, result.stderr
    argv_text = argv_log.read_bytes().decode("utf-8", errors="replace")
    assert "show" not in argv_text
    observable = result.stdout + result.stderr + argv_text
    for fragment in secret.splitlines() or [secret]:
        assert fragment not in observable
    expected = secret.splitlines()[0] if secret.splitlines() else secret
    assert stdin_log.read_text(encoding="utf-8") == expected + "\n"


def test_h003_store_key_masks_all_adversarial_values(monkeypatch, capsys):
    """TEST_ID=H003-OUTPUT-001: stdin values never reach stdout/stderr/model text."""
    # Exercise the output contract without persisting a file or real secret.
    import io
    import sys

    scripts = ROOT / "skills" / "last30days" / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        import last30days
        from lib import setup_wizard

        monkeypatch.setattr(setup_wizard, "write_api_key", lambda *_a, **_k: True)
        for secret in SECRET_CASES:
            # The command intentionally accepts one line.  For a multiline
            # value only the first line is consumed, but no line may be echoed.
            monkeypatch.setattr(sys, "stdin", io.StringIO(secret + "\n"))
            assert last30days._run_store_key("OPENAI_API_KEY") == 0
            captured = capsys.readouterr()
            assert "OPENAI_API_KEY=****" in captured.out
            json.loads(captured.out.splitlines()[-1])
            for fragment in secret.splitlines() or [secret]:
                assert fragment not in captured.out
                assert fragment not in captured.err
    finally:
        try:
            sys.path.remove(str(scripts))
        except ValueError:
            pass
