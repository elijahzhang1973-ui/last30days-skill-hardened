Make the Semgrep security workflow fail closed and use an explicit registry
ruleset that remains compatible with disabled telemetry. Harden evaluated
Gemini requests so credentials stay out of URLs, constrain browser CDP and
YouTube caption destinations before network access, route remaining direct
HTTP calls through the credential-safe redirect transport, and redact
credential-shaped fields from device-auth error diagnostics.
