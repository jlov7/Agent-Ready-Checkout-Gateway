# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| v0.1.x | ✅ |
| < v0.1.0 | ❌ |

## Reporting a Vulnerability

No customer data or PII is processed or stored by this alpha project. Secrets are managed locally and secret scanning is enabled in GitHub.

Please use GitHub Issues to report vulnerabilities:

- Include a description of the vulnerability and potential impact
- Provide steps to reproduce or proof of concept
- Add remediation ideas if available

Issues marked as security-related will be triaged within 48 hours.

## Patching process

- Triage and reproduce issue.
- Develop and test fix in a private branch.
- Coordinate disclosure timing with reporter.
- Publish patched release and update `CHANGELOG.md`.

## Security hardening guide

- Run the gateway behind a WAF with HTTPS termination.
- Configure Postgres with TLS and least-privilege roles.
- Rotate `STRIPE_API_KEY`, `HMAC_WEBHOOK_SECRET`, and receipt signing keys regularly.
- Monitor Langfuse for anomalous tool-use patterns.
- Keep Dependabot alerts addressed promptly and monitor GitHub secret scanning findings.
