# Hardened release report

## Identity

Upstream: `https://github.com/mvanhorn/last30days-skill`  
Tag: `v3.21.1`  
Commit SHA: `9243a32d823c7c8659e44b92f2dedcf1b7397137`  
Hardened distribution version: `v3.21.1-hardened.1` (engine/package compatibility version remains `3.21.1`)  
Branch: `codex/hardening-v3.21.1-h1`  
Release commit/tag/URL: pending governed PR, merge, tag, and Release; MISSING EVIDENCE until GitHub authentication succeeds.

This is an unofficial hardened distribution, not an official mvanhorn release. Upstream MIT license, copyright, project name, CLI identity, and invocation remain intact. Hardened maintainer ownership is neutral because neither the user nor project supplied a distinct owner.

## Security fixes

- Endpoint boundary: one policy allows remote HTTPS and explicit loopback HTTP, rejects remote cleartext/unsupported/malformed/userinfo endpoints, and never logs the rejected raw URL. Runtime and permission preflight share the same policy for `OPENAI_BASE_URL`, `XAI_BASE_URL`, and `OPENROUTER_BASE_URL`.
- Redirect credentials: a default urllib redirect handler compares scheme, normalized hostname, and effective port; it strips the audited credential-header class on any cross-Origin redirect and preserves them only for same-Origin redirects.
- Keychain hygiene: macOS password writes use stdin rather than plaintext argv; existence checks use exit status without decrypting via `-w`; temporary plaintext is unset. Real Keychain mutation was NOT RUN to avoid polluting a user namespace; deterministic static and behavioral guards passed.
- Structural sentinel injection (#1053): attacker-controlled titles and evidence are normalized/defanged through shared render helpers so they cannot mint footer, synthesis, or HTML-comment control lines.
- Untrusted fence escape (#1054): the common fence helper encodes closing untrusted tags, including mixed-case, repeated, whitespace, and newline forms; rerank and discovery handoff inherit the boundary.

Credential header inventory stripped cross-Origin: `Authorization`, `Proxy-Authorization`, `Cookie`, `api-key`, `x-api-key`, `x-auth-token`, `x-csrf-token`, `subscription-key`, and `ocp-apim-subscription-key` (case-insensitive).

## Accuracy change

Polymarket remains fetched, ranked, displayed with percentages and movements, and usable as supporting evidence. The contract now labels prices as market-implied expectations rather than verified facts or universal confidence. Available liquidity, volume, spread, update time, and resolution conditions may qualify material claims; unavailable data must not be invented. Finance, elections, war/geopolitics, health, safety, and legal/regulatory claims require uncertainty framing and independent corroboration.

## Compatibility

CLI: preserved; `--help`, isolated `--preflight --no-browser-cookies`, and isolated `--diagnose --no-browser-cookies` executed successfully.  
Sources: all baseline adapters preserved; no default source was removed or disabled.  
Config: existing variables preserved; endpoint rejection is the intended security behavior.  
Output: existing schemas and formats preserved; only source-controlled attempts to create engine control structures are encoded.  
Install: the committed archive resolves `last30days` 3.21.1 / distribution `v3.21.1-hardened.1`; governance validation, help, preflight, diagnose, and five isolated no-key mock dogfood tasks passed from the extracted artifact.

## Test evidence

| Gate | Result |
|---|---|
| Baseline | 3956 passed, 58 failed, 36 skipped, 51 subtests passed; failures recorded before patch |
| Targeted security/compatibility | 176 passed after README topology correction |
| Full normalized A/B | Candidate and exact upstream baseline have identical 46 failed test nodes plus identical 2 changelog subtest failures; zero new failure nodes |
| Deterministic eval | 10 passed; citation 1.000, recency 1.000, cluster coherence 0.910, coverage 1.000, determinism 1.000 |
| Trigger eval | 11/11 passed |
| Coverage | 87.95%; required floor 84% reached; security regression module 100% |
| CLI smoke | help, preflight, diagnose passed with cookies disabled and isolated HOME |
| Go MCP | NOT RUN locally: Go unavailable |
| Package | PASS: upstream clean-tree builder produced 147 archive entries; committed-file inventory matched the package subtree and exactly one root `SKILL.md` was present |
| Install | PASS: isolated extraction and governance validation; help/preflight/diagnose plus general, comparison, GitHub, community-recommendation, and Polymarket-relevant no-key mock runs exited 0 |
| Archive scan | PASS for `.skill`: main/vendor licenses, attribution, manifest identity, inventory, secret patterns, and dangerous primitive inventory checked; `bird_x.py` environment copy remains the documented deferred item |
| MCPB | NOT RUN/NOT BUILT: Go unavailable locally; the upstream release workflow remains responsible for its cross-platform matrix |

The non-normalized candidate full run reported 3976 passed, 69 failed, 36 skipped, and 51 subtests passed. The 11-count increase versus the first baseline came from one corrected README topology regression plus repository-local TEMP/default-encoding test artifacts; the normalized same-environment A/B comparison is the release regression evidence.

## Vendor audit

`scripts/lib/vendor/bird-search` identifies v0.8.0 and MIT lineage from `@steipete/bird` v0.8.0. Static inspection found no `child_process` or `eval`; network destinations are X/Twitter endpoints and environment reads include X cookies plus `BIRD_*` cache/debug paths. The wrapper currently starts from `os.environ.copy()`. Replacing that with an allowlist is deferred as `NEXT_HARDENING`: current compatibility evidence is insufficient for a minimal safe change.

## Evidence labels

Validated advantages: deterministic boundary tests, normalized A/B failure-set equality, coverage floor, eval metrics, trigger boundary, and isolated permission diagnostics.  
Design advantages: shared policies reduce runtime/diagnostic drift and central helpers cover multiple rendering/fence paths.  
Hypotheses: fewer real credential leaks and prompt-control collisions in production. Provider-backed representative live runs, human blind review, production telemetry, macOS Keychain runtime, local MCP build, and public Release verification are MISSING EVIDENCE.

The governance validator passes with no warnings. Its local release checker reports 6 pass, 3 warn, 0 block: unit-test execution is evidenced by the repository pytest/eval gates rather than the checker's nonexistent package-local unittest suite; remote clean install awaits a remote revision; provider/human output evidence is deliberately missing. The checker initially blocked on one developer script lacking `--help` and one password-environment documentation line that matched its conservative assigned-credential pattern; both were corrected without changing the public engine. The self-contained publisher dry-run remains locally unavailable because its Windows subprocess invokes bare `npx` instead of the installed `npx.cmd`; this is labeled MISSING EVIDENCE rather than bypassed.

The package subtree used for the successful build/install/archive checks is committed. This report-only evidence update does not change that subtree; the clean-tree artifact is rebuilt once more after the evidence commit. Current release status remains PARTIAL until PR checks/review, merge, tag, Release, MCPB CI artifacts, remote clean install, and post-release discovery are proven.
