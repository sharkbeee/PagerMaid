# Web Refactor Plan

This document tracks the detailed implementation plan for the `pagermaid/web` refactor.
Keep [ROADMAP.md](/Users/quby/X/Python/play/PagerMaid/ROADMAP.md) high-level.
Use this file to manage scope, status, decisions, and milestone deliverables.

## Goal

Refactor `pagermaid/web` into a safer, testable, maintainable FastAPI-based admin surface that can be exposed on a network behind HTTPS and a reverse proxy.

## Current Decisions

- Keep AMIS during the first backend-focused refactor stages.
- Do not create a second independent config system inside `pagermaid/web`.
- Start with a typed web settings boundary over the existing `pagermaid.config.Config`.
- Revisit full `pydantic-settings` adoption after the web boundary is stable, or as part of a broader config refactor.
- Introduce an app factory and lifespan-based startup/shutdown flow.
- Disable `shell` and `eval` in the web UI by default.
- Treat `shell` and `eval` as development-only capabilities.
- Design the admin panel for safe network exposure, not only localhost use.

## Non-Goals for the Early Stages

- Removing AMIS.
- Rewriting the whole UI before backend contracts are stabilized.
- Broad changes to unrelated bot runtime areas unless required by the web boundary.
- Large-scale repo-wide renames or formatting churn.

## Working Rules

- One milestone at a time.
- One architectural concern per branch or PR when possible.
- No commented-out legacy code.
- No temporary compatibility layer without a clear removal reason.
- No mixing refactor work with unrelated cleanup.
- Prefer additive migration first, then cutover, then removal.
- If new problems are discovered, log them here before expanding scope.

## Status Legend

- `planned`
- `in_progress`
- `blocked`
- `done`
- `deferred`

## Architecture Target

Target package direction:

```text
pagermaid/web/
  app.py
  lifespan.py
  settings.py
  dependencies.py
  state.py
  auth/
  routers/
  schemas/
  services/
  amis/
  templates/
  static/
```

Design rules:

- `app.py` creates the FastAPI app.
- `settings.py` defines the typed web settings boundary.
- `routers/` contains HTTP-facing route handlers only.
- `services/` contains business logic and integration logic.
- `schemas/` contains request/response models.
- `auth/` contains session and authentication logic.
- AMIS integration should depend on stable backend contracts, not the other way around.

## Milestones

### Milestone 0. Inventory and Characterization

Status: `done`

Goal:

- Understand exactly what the current web module does before changing architecture.

Deliverables:

- Current web API inventory.
- Current page -> API mapping.
- Compatibility table:
  - which endpoints must remain compatible
  - which endpoints can be marked deprecated
- Three to five characterization tests.

Suggested output files:

- `docs/web-inventory.md`
- `docs/web-compatibility.md`
- characterization tests under a future test directory

Suggested characterization test targets:

- Login success and failure behavior.
- `/status` response shape.
- Alias read/write response shape.
- Plugin list response shape.
- Current existence and auth gating of dangerous endpoints.

Primary source files to inspect:

- `pagermaid/web/api/login.py`
- `pagermaid/web/api/web_login.py`
- `pagermaid/web/api/status.py`
- `pagermaid/web/api/plugin.py`
- `pagermaid/web/api/command_alias.py`
- `pagermaid/web/api/ignore_groups.py`
- `pagermaid/web/api/bot_info.py`
- `pagermaid/web/pages/home_page.py`
- `pagermaid/web/pages/login.py`
- `pagermaid/web/pages/command_alias.py`
- `pagermaid/web/pages/ignore_groups.py`
- `pagermaid/web/pages/plugin_local_manage.py`
- `pagermaid/web/pages/plugin_remote_manage.py`

Exit criteria:

- The current behavior is documented.
- The route surface is no longer implicit.
- A minimal compatibility baseline exists before refactor work begins.

### Milestone 1. Web Settings Boundary

Status: `done`

Goal:

- Make web configuration readable, typed, validated, and override-friendly without creating a second independent config system.

Deliverables:

- `WebSettings` schema.
- Legacy YAML/env -> typed web settings adapter.
- Clear field definitions for host, port, origins, secret, enable, and dangerous feature flags.
- Optional `pydantic-settings` adoption if it cleanly fits the single-source-of-truth model.
- `.env.example` only if environment loading semantics are made explicit and real.

Suggested file-level scope:

- Create:
  - `pagermaid/web/settings.py`
- Modify lightly:
  - `pagermaid/config.py` only if a minimal bridge is required
  - `pyproject.toml`
  - `requirements.txt`
  - `uv.lock`

Constraints:

- Do not redesign auth in this milestone.
- Do not rewrite routers or pages in this milestone.
- Do not move to a separate web-only config source.

Exit criteria:

- Web code can depend on a typed web settings object instead of the full legacy config surface.
- Web-related config fields and defaults are explicit and reviewable.

### Milestone 2. App Factory and Router Split

Status: `planned`

Goal:

- Make the web app independently runnable and independently testable.

Deliverables:

- `create_app(settings, runtime_services)`.
- Lifespan-based startup/shutdown.
- Router split such as:
  - `auth_router`
  - `status_router`
  - `plugin_router`
  - additional routers as needed
- Router-level auth dependency wiring where appropriate.
- Unified exception handling.

Suggested file-level scope:

- Create:
  - `pagermaid/web/app.py`
  - `pagermaid/web/lifespan.py`
  - `pagermaid/web/dependencies.py`
  - `pagermaid/web/state.py` if needed
  - new modules under `pagermaid/web/routers/`
- Modify:
  - `pagermaid/web/__init__.py`
  - `pagermaid/__main__.py`

Constraints:

- Preserve current behavior as much as practical.
- Do not fully redesign login/session behavior yet.
- Keep AMIS in place for now.

Exit criteria:

- The app can be instantiated without starting the full bot runtime.
- App assembly is no longer buried in module import side effects.
- Router boundaries are clearer than the current monolithic arrangement.

### Milestone 3. Authentication Consolidation

Status: `planned`

Goal:

- Move from “works” to “reasonably safe to expose behind HTTPS and reverse proxy”.

Deliverables:

- `login`
- `logout`
- `session-check`
- `HttpOnly` cookie-based session flow
- Explicit dev/prod differences where needed
- Expiry and invalidation policy
- Removal of `localStorage` auth dependency

Suggested file-level scope:

- Modify or replace:
  - `pagermaid/web/api/login.py`
  - `pagermaid/web/api/utils.py`
  - `pagermaid/web/api/web_login.py`
  - AMIS login integration
  - QR login UI integration if needed
- Create as needed:
  - modules under `pagermaid/web/auth/`
  - auth schemas

Constraints:

- The direct secret-as-credential pattern must be removed.
- Cookie settings must be explicit.
- Production assumptions must be documented.

Exit criteria:

- The admin UI no longer relies on `localStorage` tokens.
- Session behavior is explicit and testable.
- Auth is suitable for controlled network exposure behind HTTPS and reverse proxy.

### Milestone 4. Tests, Deployment, and Documentation

Status: `planned`

Goal:

- Make the refactored web stack maintainable and deployable.

Deliverables:

- `pytest` coverage for the refactored web app.
- `TestClient`-based tests for core route contracts and auth behavior.
- Development notes for Docker or Compose if relevant.
- Reverse proxy deployment guidance.
- CORS and HTTPS precondition documentation.
- Migration notes.

Suggested test focus:

- Settings loading.
- Auth/session behavior.
- Core admin route contracts.
- Disabled-by-default dangerous web operations.

Exit criteria:

- The web stack has focused automated coverage.
- Deployment expectations are explicit.
- Maintainers have a migration path for the refactor.

## Dangerous Operations Policy

These endpoints should not remain normal production-facing admin features:

- `shell`
- `eval`

Policy:

- Disabled by default.
- Treated as development-only.
- Removed from the default admin UI.
- If ever enabled, guarded by explicit configuration and stronger operational assumptions.

Other sensitive actions that require review during the refactor:

- update
- restart
- plugin install/remove

## Current Risks

- Import-time globals make partial migration tricky.
- Web and bot runtime concerns are currently intertwined.
- AMIS can hide backend contract problems if route modeling is deferred too long.
- Dangerous operations create unacceptable exposure if auth is not fixed early.
- Configuration work can sprawl if the web refactor accidentally turns into a full project config rewrite.

## Deferred Work

- Decide whether to remove AMIS after backend stabilization.
- Revisit final UI stack only after auth and backend contracts are stable.
- Consider a broader full-project settings refactor after the web boundary is clean.

## Progress Log

Use this section for short status updates instead of scattering temporary notes across the repo.

- `2026-04-05`: Reframed the web refactor into milestone structure with inventory-first sequencing.

## Exit Condition for the Refactor Track

The web refactor track can be considered successful when:

- The current behavior was documented before major refactor changes.
- The app is created through an explicit app factory.
- Web settings are typed and testable.
- Admin auth is suitable for network exposure behind HTTPS and reverse proxy.
- `shell` and `eval` are disabled by default in the web UI.
- Core web routes have stable and testable contracts.
- The backend is cleanly structured whether AMIS remains or is later replaced.
