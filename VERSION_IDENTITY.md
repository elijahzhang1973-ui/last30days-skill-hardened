# Static Version Identity

This file contains only immutable release-line identity. Candidate commits,
candidate trees, artifact digests, CI run identifiers, publication state, and
post-release readback belong in the external evidence ledger and must not be
written back into a validated candidate tree.

| Field | Value |
|---|---|
| Distribution | Unofficial governed hardened distribution |
| Canonical Skill ID | `last30days` |
| Upstream tag | `v3.27.2` |
| Upstream commit | `267d50f7fcbab8a6457a93ad6ca15cbc199f633c` |
| Upstream tree | `c2964132f3167cac73be03cf378bb74893492885` |
| Target release/tag version | `v3.27.2-hardened.1` |
| Package/manifest version | `3.27.2+hardened.1` |
| Target repository | `https://github.com/elijahzhang1973-ui/last30days-skill-hardened` |

The release tag uses the user-required hardened label. Active package and
manifest surfaces use the equivalent SemVer build metadata form because
`3.27.2-hardened.1` is not a valid PEP 440 project version, while
`3.27.2+hardened.1` is valid PEP 440 and SemVer. These two spellings are a
declared mapping, not two independently moving versions.

The canonical Skill ID remains `last30days`; the hardened suffix identifies
this distribution and does not create a second command or routing identity.
Historical upstream documents and changelog entries retain their original
versions and links for attribution and traceability.
