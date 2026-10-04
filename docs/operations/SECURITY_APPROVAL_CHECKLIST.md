# OIDC sandbox security approval checklist

Status: **not approved**. This document is an evidence checklist, not an approval record.

Before any OIDC sandbox configuration is enabled, the designated security owner must review and sign off on all items below outside this repository:

- Approved OIDC issuer, audience, redirect URIs, PKCE requirement, scopes and nonce/state validation.
- Synthetic-only sandbox tenant, users and test data; no production tenant, merchant data or merchant tool credentials.
- Server-side group-to-role mapping, tenant isolation and negative authorization tests.
- Secret-manager location, rotation owner, access logs and incident/revocation contacts.
- Threat model, audit fields/retention, feature-flag rollback plan and successful rollback exercise.
- Explicit confirmation that no refund, cancellation, inventory, address or other merchant mutation is enabled.

Evidence to attach to the external approval ticket: CI reports, `docs/operations/PRODUCTION.md` validation results, OIDC negative-test plan and named rollback owner. Until written approval is recorded by the security owner, keep `COMMERCE_AUTH_REQUIRED` in its current synthetic-only mode and do not add any OIDC provider configuration.
