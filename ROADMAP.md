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

- Runtime reliability and reload safety.
- Dependency and environment cleanup.
- Clearer plugin lifecycle and plugin API boundaries.
- Better maintainer and contributor documentation.
- Recently completed: web/admin refactor and hardening.

Remaining web/admin work should now be handled as normal maintenance or mid-term follow-up,
not as a continuation of the completed web refactor track.

## Near Term

### 1. Completed: Refactor and Harden the Web Module

The focused `pagermaid/web` hardening/refactor track is closed when the core closure scope is met.
Remaining web/admin work should be tracked as normal maintenance or later roadmap work rather than
as blockers for this completed track.

Completed closure scope:

- Documented the current web API surface and page-to-API mapping.
- Introduced characterization coverage for the current web behavior.
- Established a typed web settings boundary without creating a second independent config system.
- Introduced a clearer FastAPI app assembly path.
- Improved the admin authentication/session baseline.
- Disabled dangerous web operations such as `shell` and `eval` by default.
- Clarified deployment and compatibility expectations for the web/admin surface.

Deferred web/admin follow-up:

- Remove or replace AMIS if it no longer serves the project.
- Further harden plugin mutation, update, restart, and other sensitive admin endpoints.
- Expand web test coverage beyond the refactor closure baseline.
- Improve deployment documentation and operator guidance.
- Continue separating web routes from runtime/process control where it materially reduces risk.
- Improve web/admin UX and operator feedback as part of broader admin maintenance.

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
- Track low-risk web/admin cleanup, extra tests, and documentation fixes as normal maintenance.

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
- Revisit larger web/admin follow-ups such as AMIS removal, UI redesign, and deeper admin hardening after core runtime work is more stable.

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
