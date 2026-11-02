# Production HTTPS and CORS deployment controls

## Scope

The default `docker-compose.yml` and `nginx/nginx.conf` remain HTTP-only for local development. They are not an approved production deployment configuration.

## Production launch requirements

1. Provision a real DNS name and valid TLS certificate outside Git. Place the certificate chain at `./certs/fullchain.pem` and private key at `./certs/privkey.pem`; restrict filesystem permissions and never commit the directory.
2. Set `ENVIRONMENT=production`, an explicit stable `SECRET_KEY` (at least 32 characters), a valid `MASTER_ENCRYPTION_KEY`, and `CORS_ORIGINS` as a JSON list of exact HTTPS origins, e.g. `[\"https://trade.example.com\"]`. Production rejects HTTP origins, wildcards, paths, queries, fragments and userinfo.
3. Start with `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`. The override mounts the production Nginx configuration and TLS material and publishes port 443. Port 80 redirects to HTTPS.
4. Keep backend and worker ports unpublished. The backend HTTPS middleware trusts `X-Forwarded-Proto` only at the reverse-proxy boundary; production Nginx overwrites this header with the fixed value `https`. Do not expose the backend directly or put an untrusted proxy in front of it.
5. Verify certificate renewal, redirect behavior, HSTS, browser CORS preflight and the application endpoints before any OAuth redirect URI is registered.

## Important limits

- This repository change provides a production TLS reverse-proxy configuration and an application-side forwarded-protocol guard. It does not provision DNS, issue/renew certificates, configure a cloud firewall, or prove the deployed host is HTTPS reachable.
- Do not use the default HTTP-only compose stack for production. Do not point real broker OAuth redirects at it.
- PAPER-only mode remains mandatory. No live broker order writes are enabled by this deployment configuration.
