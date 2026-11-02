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


## 2 November 2026 — security checkpoint reconciliation

- Session-security implementation verified on PR #9 head `77f44c7299f5e7157a4cdb2f8dfe7fbbfb6c08c6`: Backend CI #41460334989 and Security analysis #41460334979 passed on that exact head. Persisted sessions, refresh-token rotation/replay rejection, logout revocation and reserved JWT `sid`/`jti` handling are covered by tests.
- Transactional key-rotation service implementation commit `960c099b53d4c8e41daeb4f5691bc0972d5fb7b2`: Backend CI #41456734039 and Security analysis #41456734074 passed. It covers encrypted broker credentials, OAuth access tokens, Upstox Analytics Tokens, platform settings and MFA secrets; unreadable ciphertext fails closed. No production keys/data were rotated or accessed.
- Current documentation head is being checked separately. Do not call docs checkpoint green until both Backend CI and Security analysis pass on the final documentation head.
- Security assessment remains incomplete: endpoint IDOR authorization matrix, secret/token redaction review, broker-write reachability, staging DAST, abuse/load and tenant-isolation tests, deployment/restore/incident-response review and independent penetration testing remain.
- PAPER mandatory; LIVE broker `place_order`, `modify_order`, `cancel_order` writes disabled; PR #9 OPEN/Draft/unmerged; original `tarunsharma2610-del/Tradepro` untouched.
