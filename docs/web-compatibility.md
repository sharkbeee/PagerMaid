# Web Compatibility

This document defines the current compatibility baseline for the `pagermaid/web` refactor.
It is not a promise that every existing behavior is good. It is a record of what should remain stable during early refactor stages unless explicitly changed with migration notes.

## Compatibility Policy for Early Refactor Stages

During Milestone 1 and Milestone 2:

- Preserve current route paths where practical.
- Preserve current page navigation paths used by the AMIS admin app.
- Preserve current high-level response envelopes where the existing UI depends on them.
- Avoid mixing contract changes with app-factory/settings work unless required.

During Milestone 3 and later:

- Authentication transport and session behavior may change intentionally.
- Dangerous endpoints may be disabled or removed from the normal UI.
- Some routes may be marked deprecated if replacements are introduced cleanly.

## Must Keep Compatible for Early Stages

These surfaces are currently wired into the running UI or startup flow and should remain compatible through the early milestones unless the UI is updated in the same change.

| Surface | Why It Must Stay Compatible Early | Notes |
| --- | --- | --- |
| `/admin` | Main admin entrypoint | Rendered directly by current web app |
| `/login` | Main login entrypoint | Used by current AMIS admin flow |
| `/web_login` | QR login HTML entrypoint | Used for web-based login flow when enabled |
| `POST /pagermaid/api/login` | Current login form target | Current AMIS login expects `{status, msg, data{token}}` |
| `GET /pagermaid/api/status` | Home page status widget | Used by AMIS service component |
| `GET /pagermaid/api/log` | Home page log viewer | Used by AMIS log dialog |
| `GET /pagermaid/api/command_alias` | Alias page initial data | Used by AMIS form `initApi` |
| `POST /pagermaid/api/command_alias` | Alias save action | Used by AMIS form submission |
| `GET /pagermaid/api/test_command_alias` | Alias test form | Used by AMIS test form |
| `GET /pagermaid/api/get_ignore_group_list` | Ignore groups page data | Used by AMIS cards view |
| `POST /pagermaid/api/set_ignore_group_status` | Ignore groups toggle | Used by AMIS switch event |
| `GET /pagermaid/api/get_local_plugins` | Local plugin page data | Used by AMIS cards view |
| `POST /pagermaid/api/set_local_plugin_status` | Local plugin toggle | Used by AMIS switch event |
| `GET /pagermaid/api/get_remote_plugins` | Remote plugin page data | Used by AMIS cards view |
| `POST /pagermaid/api/set_remote_plugin_status` | Remote plugin toggle | Used by AMIS switch event |
| AMIS page URLs such as `/home`, `/bot_config/command_alias`, `/bot_config/ignore_groups`, `/plugins/local`, `/plugins/remote` | Current AMIS navigation tree depends on them | Internal to AMIS config but part of current UI shape |

## Can Change with Migration Notes

These surfaces or behaviors can change during the refactor, but the change should be deliberate and documented.

| Surface / Behavior | Why It Can Change | Migration Expectation |
| --- | --- | --- |
| Auth transport details | Current auth design is a refactor target | Update AMIS login/admin adaptors and document new flow |
| Cookie configuration | Current cookie behavior is weak and incomplete | Document new cookie semantics |
| `localStorage` token usage | Planned for removal | Update UI and auth docs together |
| Router/module layout | Internal implementation detail | No external migration needed if routes remain stable |
| Exact response model typing | Refactor target | Keep effective JSON shape stable where UI depends on it |
| `/pagermaid/api/web_login` flow details | Current QR login state model is unstable | Document changes if flow semantics shift |

## Can Be Deprecated

These routes should be treated as deprecation candidates rather than stable long-term admin features.

| Surface | Reason | Planned Direction |
| --- | --- | --- |
| `GET /pagermaid/api/run_sh` | Dangerous remote shell execution | Disable by default; development-only |
| `GET /pagermaid/api/run_eval` | Dangerous in-process code execution | Disable by default; development-only |

## Sensitive Internal Admin Endpoints

These endpoints exist today and may remain, but they should be treated as sensitive operations rather than normal low-risk admin actions.

| Endpoint | Current Status | Compatibility Guidance |
| --- | --- | --- |
| `POST /pagermaid/api/bot_update` | Wired into home page | Keep route during early milestones unless UI changes in same branch |
| `POST /pagermaid/api/bot_restart` | Wired into home page | Keep route during early milestones unless UI changes in same branch |
| `POST /pagermaid/api/set_local_plugin_status` | Wired into UI | Keep route, but review security boundary later |
| `POST /pagermaid/api/remove_local_plugin` | Exists but not wired into UI | Can change more freely if no UI depends on it |
| `POST /pagermaid/api/set_remote_plugin_status` | Wired into UI | Keep route, but review security boundary later |
| `POST /pagermaid/api/set_ignore_group_status` | Wired into UI | Keep route during early milestones |
| `POST /pagermaid/api/clear_ignore_group` | Exists but not wired into UI | Can change more freely if no UI depends on it |

## Existing Endpoints Not Clearly Used by Current UI

These should be treated carefully, but they appear less compatibility-sensitive because the current AMIS pages do not call them directly.

| Endpoint | Current Observation |
| --- | --- |
| `POST /pagermaid/api/remove_local_plugin` | Exists in API but not wired into current AMIS pages |
| `POST /pagermaid/api/clear_ignore_group` | Exists in API but not wired into current AMIS pages |

## Early-Stage Refactor Guidance

Milestone 0:

- Document current behavior.
- Add characterization coverage.
- Do not change behavior unless required to make tests possible.

Milestone 1:

- Introduce typed web settings boundary.
- Avoid contract changes to currently wired routes.

Milestone 2:

- Introduce app factory and router split.
- Preserve public route paths and AMIS-facing API contracts where possible.

Milestone 3:

- Intentionally change auth/session behavior with migration notes.
- Remove `localStorage` dependency.
- Deprecate or disable dangerous endpoints from the normal admin surface.
