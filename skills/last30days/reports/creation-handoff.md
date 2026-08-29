# Creation handoff — last30days 3.21.1 / v3.21.1-hardened.1

Canonical runtime name remains `last30days`. The hardened distribution is based on upstream tag v3.21.1 at commit `9243a32d823c7c8659e44b92f2dedcf1b7397137`; it does not replace upstream ownership.

The release candidate centralizes provider endpoint policy, complete-origin redirect credential stripping, Keychain stdin handling, engine-sentinel defanging, untrusted-fence encoding, and prediction-market evidence calibration. Roll back by reverting the hardened commits or reinstalling the exact upstream tag. Do not delete user credentials, stores, or outputs during rollback.

Review monthly, after any upstream release, and after a material security finding. Resolve ownership from explicit user or project metadata; otherwise keep the hardened maintainer neutral. Provider-backed production output and human blind review are missing evidence. Local deterministic eval and security regression results are recorded in the repository hardening report.
