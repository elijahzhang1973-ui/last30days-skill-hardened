"""FU-007 unified explicit consent and five-dimensional no-value status."""

import json
import subprocess
from unittest import mock

import pytest

from lib import agentcookie, chrome_cdp, cookie_consent, env


_PAIR_JSON = json.dumps({"auth_token": "test-auth-token", "ct0": "test-ct0"})


@pytest.mark.parametrize(
    "config,expected",
    [
        ({}, "not_requested"),
        ({"AGENTCOOKIE": "on"}, "not_requested"),
        ({"BROWSER_CDP_URL": "http://127.0.0.1:18800"}, "not_requested"),
        ({"BROWSER_CONSENT": "true"}, "granted"),
        ({"FROM_BROWSER": "chrome"}, "granted"),
        ({"FROM_BROWSER": "firefox,safari"}, "granted"),
        ({"BROWSER_CONSENT": "false", "FROM_BROWSER": "chrome"}, "denied"),
        ({"BROWSER_CONSENT": "unknown", "AGENTCOOKIE": "on"}, "denied"),
        ({"BROWSER_CONSENT": "true", "FROM_BROWSER": "off"}, "denied"),
    ],
)
def test_unified_consent_precedence(config, expected):
    assert cookie_consent.consent_state(config) == expected
    assert cookie_consent.access_allowed(config) is (expected == "granted")


def test_browser_selector_cannot_authorize_a_different_cookie_source():
    firefox = {"FROM_BROWSER": "firefox"}
    assert cookie_consent.access_allowed(firefox, "native-browser") is True
    assert cookie_consent.access_allowed(firefox, "chrome-cdp") is False
    assert cookie_consent.access_allowed(firefox, "agentcookie") is False

    chrome = {"FROM_BROWSER": "chrome"}
    assert cookie_consent.access_allowed(chrome, "native-browser") is True
    assert cookie_consent.access_allowed(chrome, "chrome-cdp") is True
    assert cookie_consent.access_allowed(chrome, "agentcookie") is False

    global_consent = {"BROWSER_CONSENT": "true"}
    for source in ("native-browser", "chrome-cdp", "agentcookie"):
        assert cookie_consent.access_allowed(global_consent, source) is True


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"AGENTCOOKIE": "on"},
        {"BROWSER_CDP_URL": "http://127.0.0.1:18800"},
        {"BROWSER_CONSENT": "false", "FROM_BROWSER": "chrome", "AGENTCOOKIE": "on"},
        {"BROWSER_CONSENT": "true", "FROM_BROWSER": "off", "AGENTCOOKIE": "on"},
    ],
)
def test_denial_or_absence_cannot_fall_through_to_any_cookie_reader(config):
    with (
        mock.patch("platform.system", return_value="Linux"),
        mock.patch("lib.agentcookie.read_x_cookies", side_effect=AssertionError("sidecar read")),
        mock.patch("lib.chrome_cdp.read_x_cookies", side_effect=AssertionError("CDP read")),
        mock.patch.object(env, "extract_browser_credentials", side_effect=AssertionError("native read")),
    ):
        env._discover_and_apply_x_credentials(config)

    status = config[cookie_consent.STATUS_KEY]
    assert status["consent"] in {"denied", "not_requested"}
    assert status["extraction"] == "not_attempted"
    assert status["permission"] == "not_checked"
    assert status["completeness"] == "not_checked"


def test_direct_readers_share_the_same_denial_gate():
    for reader in (agentcookie.read_x_cookies, chrome_cdp.read_x_cookies):
        config = {"BROWSER_CONSENT": "false", "FROM_BROWSER": "chrome"}
        with (
            mock.patch("shutil.which", side_effect=AssertionError("capability probe")),
            mock.patch("subprocess.run", side_effect=AssertionError("subprocess")),
            mock.patch.object(chrome_cdp, "candidate_endpoints", side_effect=AssertionError("socket path")),
        ):
            assert reader(config) is None
        status = config[cookie_consent.STATUS_KEY]
        assert status == {
            "capability": "not_checked",
            "consent": "denied",
            "completeness": "not_checked",
            "permission": "not_checked",
            "extraction": "not_attempted",
            "source": "agentcookie" if reader is agentcookie.read_x_cookies else "chrome-cdp",
        }


@pytest.mark.parametrize(
    "runner,expected",
    [
        (PermissionError("denied"), ("available", "not_checked", "denied", "failed")),
        (subprocess.TimeoutExpired("agentcookie", 10), ("available", "not_checked", "unknown", "failed")),
        (mock.Mock(returncode=0, stdout=json.dumps({"auth_token": "test-auth-token"}), stderr=""),
         ("available", "incomplete", "granted", "empty")),
        (mock.Mock(returncode=0, stdout=_PAIR_JSON, stderr=""),
         ("available", "complete", "granted", "succeeded")),
    ],
)
def test_agentcookie_structures_capability_completeness_permission_and_extraction(runner, expected):
    config = {"BROWSER_CONSENT": "true"}
    effect = runner if isinstance(runner, BaseException) else None
    result = None if effect else runner
    with (
        mock.patch("shutil.which", return_value="/usr/bin/agentcookie"),
        mock.patch("subprocess.run", side_effect=effect, return_value=result),
    ):
        agentcookie.read_x_cookies(config)
    status = config[cookie_consent.STATUS_KEY]
    assert status["consent"] == "granted"
    assert (
        status["capability"], status["completeness"],
        status["permission"], status["extraction"],
    ) == expected


def test_capability_unavailable_is_distinct_from_denied_and_failed():
    config = {"BROWSER_CONSENT": "true"}
    with mock.patch("shutil.which", return_value=None):
        assert agentcookie.read_x_cookies(config) is None
    assert config[cookie_consent.STATUS_KEY] == {
        "capability": "unavailable",
        "consent": "granted",
        "completeness": "not_checked",
        "permission": "not_checked",
        "extraction": "not_attempted",
        "source": "agentcookie",
    }


def test_structured_status_and_events_never_contain_cookie_values():
    config = {"BROWSER_CONSENT": "true"}
    run = mock.Mock(returncode=0, stdout=_PAIR_JSON, stderr="")
    with mock.patch("shutil.which", return_value="/usr/bin/agentcookie"), mock.patch(
        "subprocess.run", return_value=run
    ):
        assert agentcookie.read_x_cookies(config)
    serialized = json.dumps(
        {cookie_consent.STATUS_KEY: config[cookie_consent.STATUS_KEY],
         cookie_consent.EVENTS_KEY: config[cookie_consent.EVENTS_KEY]},
        sort_keys=True,
    )
    assert "test-auth-token" not in serialized
    assert "test-ct0" not in serialized
    assert set(config[cookie_consent.STATUS_KEY]) == {
        "capability", "consent", "completeness", "permission", "extraction", "source"
    }


def test_later_non_x_browser_scan_does_not_overwrite_successful_sidecar_status():
    config = {"BROWSER_CONSENT": "true", "FROM_BROWSER": "firefox"}
    run = mock.Mock(returncode=0, stdout=_PAIR_JSON, stderr="")
    with (
        mock.patch("platform.system", return_value="Linux"),
        mock.patch("shutil.which", return_value="/usr/bin/agentcookie"),
        mock.patch("subprocess.run", return_value=run),
        mock.patch.object(env, "extract_browser_credentials", return_value={
            "TRUTHSOCIAL_TOKEN": "test-truthsocial-token"
        }),
    ):
        env._discover_and_apply_x_credentials(config)
    assert config["_AUTH_TOKEN_SOURCE"] == "agentcookie"
    assert config[cookie_consent.STATUS_KEY]["source"] == "agentcookie"
    assert config[cookie_consent.STATUS_KEY]["completeness"] == "complete"
    assert "test-truthsocial-token" not in json.dumps(config[cookie_consent.STATUS_KEY])
