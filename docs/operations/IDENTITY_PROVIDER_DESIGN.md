# Identity provider design (not implemented)

Future production authentication should use OIDC Authorization Code with PKCE at a company-approved identity provider. Validate issuer, audience, expiry, signature and nonce; map verified groups to `viewer`, `support`, and `operator` server-side. Store provider client secrets only in a managed secret store, rotate them, and never forward access tokens to merchant tools.

Before enabling it, add tenant isolation, audited authorization decisions, revocation handling, threat modeling, and an approval review. The MVP's environment-only synthetic token map remains intentionally separate and is not a production identity solution.

## Approval-gated rollout

1. Design review: security approves issuer, scopes, group-to-role mapping, tenant model and audit retention.
2. Sandbox: use a non-production tenant with synthetic identities only; add negative token, expired token and role-escalation tests.
3. Pilot: enable for a small approved internal group behind a feature flag, with rollback to the current synthetic mode.
4. Production: requires signed security approval, secret-manager integration, monitoring, revocation runbook and no connection to merchant mutation tools.

No stage above is implemented by this repository; it is a decision record, not an authorization to connect an identity provider.
