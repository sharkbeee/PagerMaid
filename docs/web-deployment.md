# Web Deployment Guidance

This document describes the expected deployment model for the PagerMaid web admin.
The web admin is intended to run behind HTTPS and a reverse proxy when exposed on a network.

## Recommended Deployment Model

- Run PagerMaid on a private bind address where practical, such as `127.0.0.1`.
- Put a reverse proxy such as Nginx, Caddy, or Traefik in front of the web admin.
- Terminate HTTPS at the reverse proxy.
- Forward only the required admin host/path to PagerMaid.
- Keep `WEB_SECRET_KEY` private and rotate it if it was exposed.

Avoid exposing the PagerMaid web server directly to the public internet.

## Host and Port

`WEB_HOST` and `WEB_PORT` control where the internal Uvicorn server binds.

Recommended internal defaults:

- `WEB_HOST=127.0.0.1`
- `WEB_PORT=3333`

Use `WEB_HOST=0.0.0.0` only when the deployment environment requires binding to all interfaces, such as some container or platform setups. If `0.0.0.0` is used, restrict network access outside the application process.

## HTTPS and Cookies

The admin session uses an HTTP-only cookie. For network-exposed deployments:

- serve the admin over HTTPS
- set secure cookie behavior when the runtime supports it
- keep `SameSite=Lax` unless a specific deployment requires a different value
- do not rely on browser `localStorage` for admin authentication

If the admin is accessed over plain HTTP, secure cookies may not be sent by browsers. Use that only for local development.

## CORS

Use explicit CORS origins when the admin is exposed on a network.

Recommended:

```yaml
web_interface:
  origins:
    - "https://admin.example.com"
```

Avoid credentialed CORS with `["*"]` for network deployments. Wildcard origins are acceptable only for local experiments where browser credentials are not part of the trust boundary.

## Reverse Proxy Checklist

The reverse proxy should:

- serve HTTPS
- forward requests to the internal PagerMaid web host and port
- preserve normal cookie headers
- restrict access to the intended admin hostname
- avoid caching admin API responses
- apply any additional access controls required by the operator

## Dangerous Operations

The web admin disables dangerous execution operations by default:

- `shell`
- `eval`

These operations are not part of the normal network-exposed admin surface. If an operator explicitly enables them for development, the admin should remain limited to a trusted local environment.

## Operational Notes

- Treat plugin installation, plugin removal, update, and restart actions as sensitive admin operations.
- Review logs after deployment changes.
- Prefer changing one deployment setting at a time so failures are easy to isolate.
- Document the deployed admin URL and reverse proxy configuration for maintainers.
