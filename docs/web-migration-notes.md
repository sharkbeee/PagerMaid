# Web Migration Notes

This document summarizes web/admin behavior changes introduced during the web refactor milestones.
It is intended for maintainers and operators upgrading from the pre-refactor web implementation.
These notes apply to the PagerMaid 1.6.0 release.

## Authentication Changes

The web admin now uses cookie-based sessions for authenticated API access.

Changed behavior:

- The login API no longer returns an admin token in the JSON response.
- The admin UI no longer stores authentication data in browser `localStorage`.
- Protected web APIs read the session from the configured HTTP-only cookie.
- The raw `WEB_SECRET_KEY` is no longer accepted as an API credential.

Operational impact:

- Existing browser sessions from the old web UI should be considered invalid.
- Operators should log in again after upgrading.
- If `WEB_SECRET_KEY` was ever exposed in request headers, logs, browser storage, or documentation, rotate it.

## Session Endpoints

The web API now includes explicit session helpers:

- `GET /pagermaid/api/session-check`
- `POST /pagermaid/api/logout`

Expected behavior:

- `session-check` returns success only when the session cookie is valid.
- `logout` clears the session cookie.

## Cookie Behavior

The session cookie is set with:

- `HttpOnly`
- configured `SameSite`
- configured `Secure`
- a max age based on the configured session TTL

For network-exposed deployments, serve the admin over HTTPS and enable secure cookie behavior when supported by the runtime configuration.

## Dangerous Operations

The following web execution operations are disabled by default:

- `shell`
- `eval`

Changed behavior:

- The default admin UI no longer shows `shell` or `eval` controls.
- Authenticated requests to these endpoints return `404` unless explicitly enabled.
- Unauthenticated requests still fail authentication before reaching the disabled-operation check.

Operational impact:

- Do not rely on web `shell` or web `eval` for normal operations.
- If these capabilities are ever enabled for development, keep the web admin limited to a trusted local environment.

## Compatibility Notes

Kept stable during the refactor:

- `/admin`
- `/login`
- `/pagermaid/api/login`
- `/pagermaid/api/status`
- command alias endpoints
- plugin list endpoints
- ignore group list/toggle endpoints

Changed intentionally:

- authentication transport
- browser session storage behavior
- default availability of web `shell` and `eval`
