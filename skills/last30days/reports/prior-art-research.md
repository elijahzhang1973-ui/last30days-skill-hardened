# Prior-art research

Research date: 2026-08-29. Rating evidence: unavailable; GitHub issue and pull-request state was used only as design evidence, not adoption evidence.

| Source | Role | Finding | Decision |
|---|---|---|---|
| Upstream v3.21.1 | Canonical baseline | Complete current released behavior and package topology | Keep exact baseline and preserve interfaces |
| Upstream PR #1060 | Endpoint-boundary proposal | Useful problem framing; raw rejected URL logging and policy split required independent correction | Adapt shared policy; reject raw-URL logging |
| Upstream issue #1062 / PR #1069 | Redirect boundary | Confirms credential propagation risk; complete Origin must include scheme, host, effective port | Adapt complete-origin stripping |
| Upstream PR #1061 | Keychain hygiene | Confirms argv/presence-check exposure; static continuation handling needed stronger regression | Adapt stdin and exit-status pattern |
| Upstream issues #1053 and #1054 | Prompt/data boundary | Confirms structural sentinel and closing-fence collisions | Extend existing render/fence helpers |
| Vendored bird-search v0.8.0 | Runtime dependency | MIT; identified X/Twitter network destinations and inherited environment copy | Keep; defer env allowlist pending compatibility evidence |

Design advantage: a small number of shared boundary helpers covers runtime and diagnostics without deleting sources. Validated advantage: deterministic security tests and A/B full-suite comparison show the intended boundaries and zero new failure nodes. Hypothesis: the changes reduce real-world credential and prompt-injection incidents; no production telemetry or human blind review is available, so this remains missing evidence.
