"""One explicit-consent boundary and value-free cookie-read status records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal, MutableMapping


ConsentState = Literal["granted", "denied", "not_requested"]
CapabilityState = Literal["available", "unavailable", "not_checked"]
CompletenessState = Literal["complete", "incomplete", "not_checked"]
PermissionState = Literal["granted", "denied", "unknown", "not_checked"]
ExtractionState = Literal["succeeded", "empty", "failed", "not_attempted"]

_TRUE = {"1", "true", "yes", "on"}
_BROWSER_SELECTORS = {
    "auto", "firefox", "safari", "chrome", "brave", "edge",
    "vivaldi", "opera", "arc", "chromium",
}
_CHROMIUM_SELECTORS = {"auto", "chrome", "brave", "edge", "vivaldi", "opera", "arc", "chromium"}
STATUS_KEY = "_BROWSER_COOKIE_STATUS"
EVENTS_KEY = "_BROWSER_COOKIE_EVENTS"


@dataclass(frozen=True)
class CookieReadStatus:
    """Five orthogonal states; contains metadata only, never cookie values."""

    capability: CapabilityState
    consent: ConsentState
    completeness: CompletenessState
    permission: PermissionState
    extraction: ExtractionState
    source: str

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


def consent_state(
    config: MutableMapping[str, Any] | None = None, source: str | None = None
) -> ConsentState:
    """Resolve durable refusal/consent once for every cookie-reading path.

    ``FROM_BROWSER=off`` and any explicit non-true ``BROWSER_CONSENT`` are
    denials. A true consent value or an explicit supported browser selector is
    a grant. ``AGENTCOOKIE=on`` and ``BROWSER_CDP_URL`` select capabilities;
    neither can grant cookie access by itself.
    """

    config = config or {}
    from_browser = str(config.get("FROM_BROWSER") or "").strip().lower()
    if from_browser == "off":
        return "denied"
    explicit = config.get("BROWSER_CONSENT")
    if explicit is not None:
        return "granted" if str(explicit).strip().lower() in _TRUE else "denied"
    requested = {item.strip() for item in from_browser.split(",") if item.strip()}
    if source == "agentcookie":
        return "not_requested"
    if source == "chrome-cdp":
        return "granted" if requested & _CHROMIUM_SELECTORS else "not_requested"
    if requested & _BROWSER_SELECTORS:
        return "granted"
    return "not_requested"


def access_allowed(
    config: MutableMapping[str, Any] | None = None, source: str | None = None
) -> bool:
    return consent_state(config, source) == "granted"


def record(config: MutableMapping[str, Any] | None, status: CookieReadStatus) -> None:
    """Append one value-free event and publish the latest status."""

    if config is None:
        return
    payload = status.as_dict()
    config[STATUS_KEY] = payload
    events = config.setdefault(EVENTS_KEY, [])
    if isinstance(events, list):
        events.append(dict(payload))


def blocked_status(config: MutableMapping[str, Any] | None, source: str) -> CookieReadStatus:
    return CookieReadStatus(
        capability="not_checked",
        consent=consent_state(config, source),
        completeness="not_checked",
        permission="not_checked",
        extraction="not_attempted",
        source=source,
    )
