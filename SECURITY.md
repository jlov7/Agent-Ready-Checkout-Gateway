# Security Policy

## Supported Versions

| Version | Supported |
| --- | --- |
| v0.1.x | ✅ |
| < v0.1.0 | ❌ |

## Reporting a Vulnerability

Email `security@yourcompany.example` with the following:

- Description of the vulnerability and impact
- Steps to reproduce or proof of concept
- Suggested remediation if available
- Contact information for follow-up

We target initial response within 48 hours. Please do not open public issues for security reports.

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
