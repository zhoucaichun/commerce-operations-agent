# Identity provider design (not implemented)

Future production authentication should use OIDC Authorization Code with PKCE at a company-approved identity provider. Validate issuer, audience, expiry, signature and nonce; map verified groups to `viewer`, `support`, and `operator` server-side. Store provider client secrets only in a managed secret store, rotate them, and never forward access tokens to merchant tools.

Before enabling it, add tenant isolation, audited authorization decisions, revocation handling, threat modeling, and an approval review. The MVP's environment-only synthetic token map remains intentionally separate and is not a production identity solution.
