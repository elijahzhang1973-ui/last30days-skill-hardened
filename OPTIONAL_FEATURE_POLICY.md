# Optional Feature Policy

This policy freezes the defaults for optional external capabilities in
`v3.27.2-hardened.1`. A configured credential establishes capability; it does
not by itself establish consent to send every query to every service.
`EXCLUDE_SOURCES` is the durable kill switch for source lanes and an explicit
per-run source list bounds the run further.

| Feature | Default | Credential required | External destination and disclosed data | Cost risk and cap | Privacy risk | Enable method | Fallback and quality gate | Owner / SLO / kill switch |
|---|---|---|---|---|---|---|---|---|
| Telegram public channels | off | `SCRAPECREATORS_API_KEY` | ScrapeCreators; selected public channel handles, page cursor, and time window | one credit per live page; page cap quick=1, default=3, deep=6 | public channel identifiers and query context leave the host | `--telegram-sources` or `TELEGRAM_SOURCES`, plus `telegram` in the requested/include set | no keyword discovery; malformed/private identifiers fail closed; source failure remains visible | source owner: Telegram adapter; bounded by research deadline; `EXCLUDE_SOURCES=telegram` |
| Meta Ads | off | `SCRAPECREATORS_API_KEY` | ScrapeCreators/Meta Ad Library; brand query, country, optional page id, creative URLs | at most seven calls in a default run | brand research terms and selected page leave the host | request `meta_ads` or use `--meta-ads-page` | never inferred from topic shape; unresolved advertiser is not silently substituted | source owner: Meta Ads adapter; bounded by research deadline; `EXCLUDE_SOURCES=meta_ads` |
| Parallel hosted MCP | off | no; optional `PARALLEL_API_KEY` | `search.parallel.ai`; search objective and query | provider-defined; no package-side paid call is authorized without an explicit configured account and budget | full search objective leaves the host | `--web-backend=parallel-mcp` | never auto-selected; failure remains a grounding-source failure | source owner: web backend; bounded by web deadline; choose another backend or exclude grounding |
| Parallel API grounding | capability-gated | `PARALLEL_API_KEY` | Parallel API; search query and recency constraints | provider-defined; usage ledger records known calls/cost, unknown spend blocks budget approval | search terms leave the host | configure the key and select/pin the backend | backend-chain failure remains explicit; no credential fallback to an unapproved destination | source owner: web backend; bounded by web deadline; remove key or select another backend |
| ScrapeCreators social sources | off except an explicit onboarding selection | `SCRAPECREATORS_API_KEY` | ScrapeCreators; source query, handles/URLs, cursors, and public-content identifiers | 10,000-call account tier is provider policy, not a guaranteed free budget; per-source caps in `CONFIGURATION.md` apply | research terms and public identifiers leave the host | per-source `INCLUDE_SOURCES` or explicit `--search`; setup requires user consent before persisting the key | each adapter applies recency/relevance gates; failures retain source status | source owners: individual adapters; bounded by research deadline; `EXCLUDE_SOURCES=<source>` or remove key |
| ScrapeCreators Reddit/YouTube rescue | thin-result fallback only | `SCRAPECREATORS_API_KEY` | ScrapeCreators; query, subreddit/video identifiers, and cursors | Reddit and YouTube thinness floors cap activation; known and unknown spend are journaled | query and public identifiers leave the host | configure key; tune thinness floors, where `0` means empty-only rescue | free/keyless path runs first unless explicitly pinned; free results survive fallback failure | source owners: Reddit/YouTube adapters; set floor to `0`, exclude source, or remove key |
| Official X API | off unless selected by backend policy and credential is configured | `X_BEARER_TOKEN` | X API; query, handles, expansions, and time window | provider account billing/rate limits; lane deadlines and result limits bound calls | query and public account identifiers leave the host | configure token and select the official X backend | other X backends are separate capabilities; auth/rate/coverage failures remain visible | source owner: X API adapter; bounded lane budget; `EXCLUDE_SOURCES=x` or select another X backend |
| Browser-cookie X access | off without explicit consent | existing browser session plus `BROWSER_CONSENT=true` | X and the selected browser profile; live session cookies are read locally and sent only to their service | no package-side provider fee; rate-limit risk remains | highest: authenticated session material is accessed | consented setup and configured `FROM_BROWSER`; never enabled by capability detection alone | refusal is a hard denial across native, CDP, and agentcookie paths | privacy-runtime owner; `BROWSER_CONSENT=false`, `FROM_BROWSER=off`, or `--no-browser-cookies` |
| Host WebSearch | host-negotiated, not an engine default | host-dependent | host search provider; topic/query and returned public snippets | host-dependent and therefore unmeasured by this package | search terms leave the host; results are untrusted data | only through the documented host capability contract | web results cannot become control input; lack of isolation forces explicit degraded mode | host-integration owner; host tool disable/deny is the kill switch |
| HTML publishing | off | optional publish password | `ht-ml.app`; rendered report and optional shared password | provider-defined; one explicit publish operation | output becomes public by default | `--publish-html` or `library feed --publish` | local artifact is written first; publish failure does not rewrite it | publishing owner; omit publish flag; no automatic fallback publisher |

## Release constraints

- No test or release job may read an existing production credential, browser
  cookie, Keychain secret, or login session.
- Live paid-provider validation requires separate evidence recording the data
  class sent, destination, call cap, and cost cap. In its absence the live
  canary is `BLOCKED` or `NOT_RUN`, never `PASS`.
- Provider marketing allowances, including free-call tiers, are mutable
  external facts and are not release guarantees.
- Source output is untrusted data. It must pass the parser, schema, provenance,
  and data-to-control boundaries recorded in `trust-boundaries.json`.
