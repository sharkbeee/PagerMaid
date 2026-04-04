# PagerMaid Roadmap

This document is the maintainer-facing roadmap for PagerMaid. It is a living document, not a release checklist. Detailed work should live in issues and milestones; this file should stay focused on direction, priorities, and scope.

## Goals

- Keep PagerMaid usable and maintainable for existing operators.
- Stabilize the core runtime before adding more features.
- Make plugin development easier, safer, and better documented.
- Reduce maintenance risk from fragile dependencies and implicit behavior.
- Improve contributor onboarding so the project is not dependent on one maintainer.

## Guiding Principles

- Stability over feature count.
- Backward compatibility where it is practical and low-risk.
- Explicit interfaces over hidden global state.
- Safer reload, update, and plugin management flows.
- Documentation should be updated alongside code changes that affect behavior.

## Current Focus

- Web/admin refactor and hardening as the first priority.
- Runtime reliability and reload safety.
- Dependency and environment cleanup.
- Clearer plugin lifecycle and plugin API boundaries.
- Better maintainer and contributor documentation.

## Near Term

### 1. Refactor and Harden the Web Module

The current `pagermaid/web` module should be treated as the highest-priority refactor area.
The goal is not a cosmetic rewrite. The goal is to bring the web/admin surface in line with
modern FastAPI and Pydantic practices, reduce security risk, and make the web stack testable
and maintainable.

Primary problems to address:

- Replace direct web-module dependence on the monolithic import-time config with a typed web settings boundary, without introducing a second independent config system.
- Introduce a proper FastAPI app factory and lifespan-based startup/shutdown flow.
- Reduce or remove module-level mutable globals in auth, login state, and service wiring.
- Redesign authentication so it does not rely on `localStorage`, direct secret reuse, or weak cookie defaults.
- Replace raw `dict` request/response handling with typed Pydantic models and explicit HTTP status semantics.
- Disable dangerous web operations such as `shell` and `eval` by default and keep them out of the normal network-exposed admin surface.
- Tighten other sensitive admin operations such as update, restart, and plugin installation/removal.
- Fix invalid or overly broad CORS defaults and clarify the intended deployment model for the admin UI.
- Move HTML/template handling toward standard FastAPI patterns with reusable templates and mounted static assets.
- Separate web UI concerns from bot/process control so routes do not directly manage global runtime state.
- Add focused tests for auth, settings loading, route contracts, and critical admin workflows.

Expected outcomes:

- The web app can be created and tested independently of full bot startup.
- Web settings are explicit, typed, and easier to validate while still sourcing values from the existing config path during early migration.
- Route contracts are documented by models instead of implicit response shapes.
- Admin authentication is safer and easier to reason about.
- The admin panel is designed to be exposed safely on a network behind HTTPS and a reverse proxy.
- `shell` and `eval` are disabled in the web UI by default and treated as development-only capabilities.
- The codebase is ready for a later decision to keep or replace the current AMIS-based UI.

Suggested implementation order:

1. Introduce a typed web settings adapter and an app factory.
2. Refactor auth and session handling for safe network exposure.
3. Disable `shell` and `eval` in the web admin by default and isolate other sensitive actions behind clearer boundaries.
4. Add request/response models and standardized error handling.
5. Rework templates/static assets and clean up UI integration while keeping AMIS temporarily.
6. Add tests, deployment guidance, and migration notes.

### 2. Stabilize the Core Runtime

- Audit startup, shutdown, and reload behavior.
- Reduce reliance on fragile global mutable state.
- Improve error reporting around plugin loading and command execution.
- Add smoke tests for boot, plugin load, reload, and shutdown.

### 3. Make the Project Easier to Maintain

- Define a supported Python version policy.
- Audit third-party and forked dependencies.
- Simplify local development and deployment instructions.
- Add CI for linting, basic tests, and packaging validation.

### 4. Improve the Plugin Story

- Document the plugin lifecycle more clearly.
- Keep the current plugin model working while improving the internal structure.
- Standardize plugin metadata, help text, and load diagnostics.
- Provide a minimal example plugin and plugin development template.

## Mid Term

### 5. Formalize the Runtime Architecture

- Introduce clearer runtime boundaries for config, services, hooks, and plugin registration.
- Reduce import-time side effects and hidden initialization.
- Move toward a more explicit registry-based internal design.
- Improve separation between built-in modules and external plugins.

### 6. Safer Operations and Upgrade Paths

- Redesign self-update behavior to avoid destructive defaults.
- Improve backup and restore workflows for config, session, and plugin state.
- Make remote plugin install and update behavior more transparent and auditable.
- Establish a clearer release process and changelog discipline.

### 7. Web and Admin Improvements

- Review the current web/admin surface for security and maintainability.
- Improve authentication, configuration handling, and operator feedback.
- Clarify which management tasks belong in chat commands and which belong in the web UI.

## Longer Term

### 8. Ecosystem and Contributor Growth

- Publish contributor guidelines for code changes, plugin contributions, and reviews.
- Maintain a compatibility policy for community plugins.
- Curate example plugins and best practices for common use cases.
- Build enough project structure that maintenance can be shared across contributors.

## Non-Goals

- Chasing feature parity with every other userbot project.
- Adding major new subsystems before the core runtime is stable.
- Making broad breaking changes without a migration path.
- Turning this roadmap into a duplicate issue tracker.

## How to Use This Roadmap

- Keep this file high-level.
- Track concrete implementation work in issues.
- Group issues into milestones by release or theme.
- Update this document when priorities change, not for every small task.

## Suggested Milestone Themes

- `Core Stabilization`
- `Plugin API and Docs`
- `Operations and Release Process`
- `Web/Admin Hardening`

## Exit Criteria for the Current Phase

The current phase can be considered successful when:

- PagerMaid starts cleanly in a documented development environment.
- Built-in modules and external plugins load with predictable diagnostics.
- Reload behavior is reliable enough for daily development use.
- Core maintenance tasks are documented and repeatable.
- New contributors can understand the architecture without reverse-engineering the whole project.
