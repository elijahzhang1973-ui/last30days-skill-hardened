# Diff audit

The patch is boundary-focused: it does not rewrite the engine, remove adapters, rename public configuration, or redesign outputs.

| File/group | Necessity and finding | Public behavior | Regression evidence | Further reduction |
|---|---|---|---|---|
| `lib/providers.py`, `permission_preflight.py`, `CONFIGURATION.md` | Provider credential endpoint boundary and single source of truth (#1060 prior art) | Unsafe overrides now ignored; safe uses unchanged | Endpoint matrix, redaction, inventory, preflight tests | Three propagated variables are the actual audited set |
| `lib/http.py` | Cross-Origin redirect credential leak (#1062/#1069 prior art) | Credentials retained only same-Origin | Scheme/host/effective-port and header inventory matrix | One global urllib boundary avoids caller duplication |
| `setup-keychain.sh` | Plaintext argv and unnecessary decryption (#1061 prior art) | List/delete/replace contract retained | Static argv/presence/ALL_KEYS guards | Real Keychain test deferred to avoid user mutation |
| `lib/render.py` | Structural sentinel/data-control collision (#1053) | Malicious control-shaped text encoded; ordinary text readable | Fake footer/synthesis/comment/multiline corpus | Extends existing evidence/corpus formatting rather than new renderer |
| `lib/rerank.py` | Closing untrusted fence escape (#1054) | Closing tags encoded within untrusted data | mixed case, multiple, whitespace/newline, title/snippet/comment | Common helper covers rerank and discovery |
| `SKILL.md`, public READMEs | Prediction-market calibration and unofficial identity | Market data preserved; claims calibrated; fork clearly disclosed | Contract/public-claim tests and translation topology test | Localized sentence-level edits only |
| `tests/test_hardening_security.py` | Unified executable regression corpus | Test-only | 100% test-module coverage | Consolidated instead of one file per patch |
| `changelog.d/*` | Upstream-compatible feature-branch release notes | None at runtime | Changelog workflow contract | Required by repository contribution policy |
| `skills/last30days/{manifest,README,LICENSE,evals,reports}`, `agents/openai.yaml` | Governed package, attribution in the actual archive, Skill IR, routing and trust/release evidence | Metadata only | governance validate, trigger eval, and archive inventory | Minimum missing artifacts reported by authoritative validator and packaging gate |
| Root audit reports | Required reproducible release evidence | None | reviewable commands/results | Required deliverables |

No unrelated cleanup was accepted. The vendored environment allowlist idea was rejected for this release because its compatibility cost was not proven. Final line counts and archive inventory are recorded after committed packaging so generated artifacts are not confused with source diff.

Pre-publication committed diff versus exact upstream baseline: 34 files, 1,182 insertions, 64 deletions. Most additions are executable regression tests and required evidence/Skill IR rather than runtime code; the runtime/security implementation remains localized to five Python modules and one Keychain script.
