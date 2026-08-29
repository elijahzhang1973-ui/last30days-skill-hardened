# last30days hardened skill package

一句话价值：在保留上游 `last30days` CLI、数据源和调用习惯的前提下，对近期网络研究增加统一的凭据端点、重定向、Keychain 与提示结构边界，并校准预测市场证据语义。

This is an unofficial hardened distribution of `https://github.com/mvanhorn/last30days-skill` v3.21.1. It is not an official mvanhorn release. Upstream copyright and MIT terms are preserved.

## Install

After the pull request and release gates pass, install from the hardened repository or release artifact. For compatible installers the repository form is:

```bash
npx skills add <hardened-repository-url> --skill last30days
```

Do not treat this placeholder as a published URL. The final repository and immutable release URL are established only by the governed publication flow.

## Natural-language examples

- “研究最近 30 天大家如何评价这个产品，并给出处。”
- “Compare PostgreSQL and ClickHouse based on recent community discussion.”
- “检查最近一个月这个 GitHub 项目的发布、issue 和开发者讨论。”
- “先运行 last30days preflight，不读取浏览器 cookie。”

The skill should not trigger for timeless encyclopedia questions, requests that prohibit recent-source research, or unrelated file/code editing.

## Trust and permissions

Internet text and local corpus text are untrusted data. Browser cookies remain consent-gated and default-off. Network calls use configured sources; paid or credentialed providers require their existing keys and budgets. Local writes occur only for explicit output, store, library, watchlist, or publish modes. Public publishing remains explicit opt-in.

Prediction-market prices are trader-expectation signals, not verified facts or universal confidence scores. High-risk claims require independent corroboration.

## Verification

From the repository root:

```bash
python C:/Users/minzh/.codex/skills/skill-engineering-governance/scripts/validate_skill.py skills/last30days
python C:/Users/minzh/.codex/skills/skill-engineering-governance/scripts/trigger_eval.py skills/last30days --cases evals/trigger_cases.json
python -m pytest tests/test_hardening_security.py
python -m pytest tests/eval -x -s
```

## Troubleshooting

- Run `last30days --preflight --no-browser-cookies` before research to inspect planned reads, writes, credentials, commands, and sources without printing secret values.
- Run `last30days --diagnose --no-browser-cookies` for source availability.
- A rejected provider endpoint warning intentionally names only the environment variable; it does not echo the supplied URL.
- See the repository `BASELINE_REPORT.md` for upstream Windows/POSIX test limitations and `HARDENING_REPORT.md` for current evidence.

Rollback is package-scoped: revert the hardened commits or reinstall exact upstream v3.21.1. Existing user stores, credentials, and research outputs are not deleted by rollback.
