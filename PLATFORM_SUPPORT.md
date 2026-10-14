# Platform Support Matrix

This file defines the static release scope for `v3.27.2-hardened.1`. It is not
a test report. Candidate commit/tree, test results, CI run IDs, artifact hashes,
and host-E2E receipts belong in the external release evidence ledger. A
`CONDITIONAL_G5` row becomes release-supported only if the exact frozen
candidate passes its G5 requirements.

| Surface | Platform | Architecture | SOURCE_SUPPORTED | UNIT_TESTED | INTEGRATION_TESTED | HOST_E2E_VERIFIED | RELEASE_SUPPORTED | EXCLUDED |
|---|---|---:|---|---|---|---|---|---|
| Skill/Python | Windows | any | YES | PARTIAL | NO | NO | NO | YES |
| Skill/Python | macOS | any | YES | NOT_RUN | NOT_RUN | NO | NO | YES |
| Skill/Python | Linux | any | YES | G5_REQUIRED | G5_REQUIRED | G5_REQUIRED | CONDITIONAL_G5 | NO |
| macOS Keychain | macOS | any | YES | NOT_RUN | NOT_RUN | NO | NO | YES |
| MCPB | macOS | arm64 | YES | NOT_RUN | NOT_RUN | NO | NO | YES |
| MCPB | macOS | amd64 | YES | NOT_RUN | NOT_RUN | NO | NO | YES |
| MCPB | Linux | amd64 | YES | G5_REQUIRED | G5_REQUIRED | G5_REQUIRED | CONDITIONAL_G5 | NO |
| MCPB | Windows | any | NOT_ESTABLISHED | NO | NO | NO | NO | YES |

The machine-readable policy is
[`platform-support.json`](platform-support.json). `G5_REQUIRED` is a gate, not
a claim that testing has already passed.

## Release scope

Only Linux Skill/Python and Linux amd64 MCPB remain conditional G5 release
surfaces. Source support is not release support. Windows Skill/Python is
excluded because the complete Windows suite, NTFS private-file behavior, and a
Windows Codex host E2E have not passed. Windows MCPB is separately excluded:
this release has no `win32` manifest entry, Windows build-matrix row, Windows
MCPB, Windows executable, artifact hash, signing receipt, or host E2E evidence.
Windows-specific source files are development intent, not a support claim.

Adding any Windows MCPB claim or artifact reopens FU-009 and requires native
Windows Go tests plus stdio, Python resolution, cache, cancellation, timeout,
descendant-cleanup, signing, host-install, and post-release readback evidence.

## macOS scope

macOS Skill/Python, both macOS MCPB architectures, and the Keychain integration
are excluded from this release. The source integrations remain, but the exact
candidate has no native macOS host E2E or real Keychain evidence. Windows-hosted
fake-`security` tests validate secret-flow invariants; they do not substitute
for a macOS host result.

## MCPB release invariant

Only the Linux amd64 MCPB row may be built. Its presence in this matrix is
conditional, not approval: the artifact still needs exact
candidate provenance, unpacked identity checks, Go/MCP tests, applicable host
E2E evidence, and release-asset readback. An excluded row must not appear in
the manifest, release matrix, build output, or published assets.
