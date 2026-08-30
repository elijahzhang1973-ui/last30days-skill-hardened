# Upstream sync strategy

Remotes are intended to remain:

```text
upstream = https://github.com/mvanhorn/last30days-skill.git
origin   = hardened fork (created only through the governed publication flow)
```

For each upstream release:

1. Fetch upstream tags and verify the new release commit/tree and release date.
2. Compare the new tag with the previous pinned baseline and review upstream PRs/issues for each local finding.
3. Identify local commits whose behavior is fully upstreamed. Prefer the upstream implementation and drop the superseded local patch rather than maintaining parallel policy.
4. Rebase or replay only the remaining minimal hardened commits on a new `codex/hardening-<version>` feature branch. Never push directly to the default branch.
5. Re-freeze CLI help, source adapters, configuration/environment variables, output schemas, permission behavior, and vendor inventory.
6. Run targeted boundary tests, same-environment upstream/candidate full-suite A/B, deterministic eval, coverage, governance validation, trigger eval, package build, clean install, and archive scans.
7. Open a pull request. Merge only after checks are complete, no requested changes remain, and evidence reports match the candidate commit.
8. Create a distinct unofficial hardened tag and immutable GitHub Release; verify artifact discovery and isolated installation.

Rollback boundary: revert the hardened commits or reinstall the pinned official upstream tag. Do not delete user credential stores, research databases, watchlists, corpora, or outputs. If a new upstream change conflicts with a local patch and correct behavior cannot be proven, block the hardened release and record MISSING EVIDENCE rather than guessing.
