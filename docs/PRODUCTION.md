# Production boundary

Use `src/infra/nginx/commerce-agent.conf` only behind a managed certificate mount. Keep the actual certificate files and environment file outside Git. Copy `src/infra/production.env.example` to an operator-controlled secret store, replace every placeholder, and inject it at deployment time. Do not use Compose demo passwords or `COMMERCE_DEMO_TOKENS` outside a synthetic environment.

The reverse proxy enforces HTTPS and HSTS; FastAPI retains CSP and browser security headers. This repository does not provision DNS, certificates, a secrets manager, or a production identity provider.

## Pre-deployment and certificate rotation

1. Run `python src/infra/validate_proxy_config.py --host agent.example.com`; it rejects placeholder hosts and missing TLS/proxy directives without reading a certificate.
2. In the operator environment, render the Nginx template with the managed hostname, mount the managed `fullchain.pem` and `privkey.pem`, then run `nginx -t` in the deployment container.
3. Verify the published chain with `openssl s_client -connect agent.example.com:443 -servername agent.example.com` and confirm HTTPS redirect, HSTS, CSP and `/ready`.
4. Rotate by placing the new certificate and key through the secret manager's atomic mount/update mechanism, run `nginx -t`, then `nginx -s reload`. Keep the prior certificate available until a successful handshake and health check are recorded.
5. If validation or handshake fails, restore the previous secret version and reload Nginx. Do not copy private keys into Git, CI logs, tickets or this repository.
