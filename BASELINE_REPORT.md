# Baseline report

## Immutable identity

| Field | Value |
|---|---|
| Repository | `https://github.com/mvanhorn/last30days-skill.git` |
| Official release | `v3.21.1` |
| Release date | 2026-08-18 |
| Commit | `9243a32d823c7c8659e44b92f2dedcf1b7397137` |
| Annotated tag object | `c0287901c472fd51786c9495affc560ebc9b0dfa` |
| Tree | `50ef6626b154b16cb3ddb6223a97b627cefc797a` |
| GitHub tag archive SHA-256 | `DF082A12A5C9F29C753429FFA3D707827A871F1B58982972A5D56DF51899E616` |
| Frozen tree | clean; exact 454 tracked files; `git fsck --full --no-dangling` passed |
| Python | 3.12.13 |
| Node | v24.15.0 (initial snapshot v24.19.0; runtime changed during the session, so both are recorded) |
| Git | 2.54.0.windows.1 |
| OS | Windows, PowerShell; Git Bash 5.3.9 available; Go unavailable |

GitHub source archives omit 286 export-ignored development files. The baseline was reconstructed from exact-tag raw objects and verified against the commit tree before modification; the archive hash above is evidence for the downloaded ZIP, not a substitute for the Git tree identity.

## Baseline commands and results

| Surface | Command | Result |
|---|---|---|
| Python suite, first attempt | `python -m pytest` before installing dev dependencies | NOT RUN: pytest unavailable |
| Python suite, frozen baseline | `.venv/Scripts/python.exe -m pytest` with isolated HOME | 3956 passed, 58 failed, 36 skipped, 51 subtests passed; 114.38 s |
| Normalized A/B baseline | `python -m pytest -q` with repository-external HOME/TEMP, UTF-8, Git Bash | FAIL only on 46 Windows-incompatible test nodes plus 2 changelog subtests; exact failure set later matched candidate |
| Eval suite | Included in baseline full suite; explicit candidate eval used for release evidence | Baseline full-run coverage only; no separate pre-change score capture, therefore separate baseline eval metrics are MISSING EVIDENCE |
| Go MCP tests | `go test -race ./...` | NOT RUN: Go unavailable locally |
| Package/release build | Upstream release workflow inspected | NOT RUN before modification; build requires a clean commit |

Known upstream failures are platform or harness issues, not accepted candidate regressions: Windows rejects `strftime("%-d")`; POSIX permission-bit expectations do not hold; several tests require POSIX `bash`, `sed`, process groups, or `$HOME`-literal paths; Windows keeps SQLite files locked at temporary-directory cleanup; some tests rely on Unix unwritable-path semantics. A default-encoding run also exposed GBK reads, and a repository-local TEMP caused version-fallback tests to discover the outer manifest. The normalized A/B run removes those harness artifacts and compares identical failure node sets.

## Frozen compatibility surfaces

CLI: topic research; `--diagnose`; `--preflight`; quick/default/deep; comparison and competitors; discovery nominate/judge/finalize; watchlist scripts; store/library/publish; corpus; hiring signals; freshness verification; Markdown, HTML, JSON, compact, context, and brief outputs; all parser flags captured by `last30days.py --help`.

Source inventory: Reddit (public, RSS, Arctic, Shreddit, keyless and enrichment paths), X (bird, xAI, xurl, xquik, opt-in Grok), YouTube, TikTok, Instagram, Hacker News, GitHub, Polymarket, Bluesky, LinkedIn, arXiv, Techmeme, Digg, StockTwits, Trustpilot, Amazon, Xiaohongshu, Threads, Pinterest, Truth Social, jobs/hiring, Bright Data, Perplexity, Parallel, Brave, Exa, Serper, keyless web/grounding, local corpus, and hosted/native search paths. No adapter was removed or default-disabled.

Configuration/environment inventory: `LAST30DAYS_*` runtime, store, corpus, library, provider, planner/rerank, watchlist, publish, source, cookie, trust, timeout and backend pins; provider keys and endpoints (`OPENAI_*`, `XAI_*`, `OPENROUTER_*`, `PERPLEXITY_*`, `GEMINI_*`/`GOOGLE_*`); web keys (`BRAVE_API_KEY`, `EXA_API_KEY`, `SERPER_API_KEY`, `PARALLEL_API_KEY`); source credentials (`GITHUB_TOKEN`, `AUTH_TOKEN`, `CT0`, `FROM_BROWSER`, `SCRAPECREATORS_API_KEY`, `BRIGHTDATA_API_KEY`, `XQUIK_API_KEY`); and optional command/path configuration. The audit command was a unique-token scan over `SKILL.md`, `CONFIGURATION.md`, and runtime scripts; no variable was intentionally renamed or removed.

Browser-cookie extraction was and remains consent-gated/default-off. Project configuration trust, paid-source budgets, preflight, and doctor are frozen compatibility requirements.
