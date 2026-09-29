# Production boundary

Use `src/infra/nginx/commerce-agent.conf` only behind a managed certificate mount. Keep the actual certificate files and environment file outside Git. Copy `src/infra/production.env.example` to an operator-controlled secret store, replace every placeholder, and inject it at deployment time. Do not use Compose demo passwords or `COMMERCE_DEMO_TOKENS` outside a synthetic environment.

The reverse proxy enforces HTTPS and HSTS; FastAPI retains CSP and browser security headers. This repository does not provision DNS, certificates, a secrets manager, or a production identity provider.
