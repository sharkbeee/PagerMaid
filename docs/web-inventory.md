# Web Inventory

This document records the current `pagermaid/web` surface before refactor work.
It is intended to describe what exists today, not what the refactor should look like.

## Overview

Current web assembly is centered in `pagermaid/web/__init__.py`:

- A `Web` singleton creates `FastAPI()` directly.
- API routers are registered from `pagermaid/web/api/__init__.py`.
- HTML routes are defined inline for `/`, `/admin`, and `/login`.
- AMIS page schemas are imported at module scope from `pagermaid/web/pages/*`.
- The server is started manually through `uvicorn.Server(...)` in `Web.start()`.

Current config and startup dependencies:

- Web enablement and bind settings come from `pagermaid.config.Config`.
- `WEB_ENABLE`, `WEB_HOST`, `WEB_PORT`, `WEB_SECRET_KEY`, and `WEB_ORIGINS` are read from the legacy config path.
- Startup is triggered from `pagermaid/__main__.py`.

## Entry Points

| Surface | Source | Current Role |
| --- | --- | --- |
| Web runtime wrapper | `pagermaid/web/__init__.py` | Creates app, registers routes/middleware, starts uvicorn server |
| API router assembly | `pagermaid/web/api/__init__.py` | Mounts all `/pagermaid/api/*` routes and `/web_login` HTML route |
| Main startup integration | `pagermaid/__main__.py` | Calls `web.start()` and coordinates bot/web login flow |
| Config source | `pagermaid/config.py` | Provides `WEB_ENABLE`, `WEB_SECRET_KEY`, `WEB_HOST`, `WEB_PORT`, `WEB_ORIGINS` |

## HTML Routes

| Path | Method | Source | Auth | Purpose | Notes |
| --- | --- | --- | --- | --- | --- |
| `/` | `GET` | `pagermaid/web/__init__.py` | No | Redirect to `/admin` | Simple redirect |
| `/admin` | `GET` | `pagermaid/web/__init__.py` | No server-side dependency | Render AMIS admin app | Client-side AMIS adaptor injects token header from `localStorage` |
| `/login` | `GET` | `pagermaid/web/__init__.py` | No | Render AMIS login page | Login form stores token in `localStorage` on success |
| `/web_login` | `GET` | `pagermaid/web/api/web_login.py` | No | Render QR login HTML page | Separate plain HTML page, not AMIS |

## API Routes

All routes below are mounted under the `/pagermaid/api` prefix.

| Path | Method | Source | Auth | Request Shape | Response Shape | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `/login` | `POST` | `web/api/login.py` | No | JSON body: `{"password": str|null}` | JSON `{status, msg, data{version, token}}` on success | Also sets `token_ck` cookie |
| `/web_login` | `GET` | `web/api/web_login.py` | Yes | none | JSON `{status, msg, content?}` | Starts or continues QR login flow |
| `/web_login` | `POST` | `web/api/web_login.py` | Yes | JSON body: `{"password": str}` | JSON `{status, msg, content?}` | Continues QR login with password |
| `/log` | `GET` | `web/api/status.py` | Yes | Query: `num` | text stream | Streams latest log lines from `data/pagermaid.log.txt` |
| `/run_eval` | `GET` | `web/api/status.py` | Yes | Query: `cmd` | text stream or `"无效命令"` | Dangerous: arbitrary Python evaluation |
| `/run_sh` | `GET` | `web/api/status.py` | Yes | Query: `cmd` | text stream or `"无效命令"` | Dangerous: arbitrary shell execution |
| `/status` | `GET` | `web/api/status.py` | Yes | none | JSON status object | Returns bot runtime status |
| `/bot_update` | `POST` | `web/api/bot_info.py` | Yes | none | JSON `{status, msg}` | Sensitive: updates PagerMaid |
| `/bot_restart` | `POST` | `web/api/bot_info.py` | Yes | none | empty JSON object | Sensitive: stops bot/web tasks |
| `/get_local_plugins` | `GET` | `web/api/plugin.py` | Yes | none | JSON `{status, msg, data{rows, total}}` | Reads local plugin list |
| `/set_local_plugin_status` | `POST` | `web/api/plugin.py` | Yes | JSON body: `{"plugin": str, "status": bool/int}` | JSON `{status, msg}` | Sensitive: enable/disable plugin and reload |
| `/remove_local_plugin` | `POST` | `web/api/plugin.py` | Yes | JSON body: `{"plugin": str}` | JSON `{status, msg}` | Sensitive: uninstall local plugin and reload |
| `/get_remote_plugins` | `GET` | `web/api/plugin.py` | Yes | none | JSON `{status, msg, data{rows, total}}` | Loads remote plugin metadata |
| `/set_remote_plugin_status` | `POST` | `web/api/plugin.py` | Yes | JSON body: `{"plugin": str, "status": bool/int}` | JSON `{status, msg}` | Sensitive: install/remove remote plugin and reload |
| `/command_alias` | `GET` | `web/api/command_alias.py` | Yes | none | JSON `{status, msg, data{items}}` | Reads alias list |
| `/command_alias` | `POST` | `web/api/command_alias.py` | Yes | JSON body: `{"items": [...]}` | JSON `{status, msg}` | Writes alias list |
| `/test_command_alias` | `GET` | `web/api/command_alias.py` | Yes | Query: `message` | JSON `{status, msg, data{new_msg}}` | Alias simulation endpoint |
| `/get_ignore_group_list` | `GET` | `web/api/ignore_groups.py` | Yes | none | JSON `{status, msg, data{groups}}` | Returns cached group list with ignore status |
| `/set_ignore_group_status` | `POST` | `web/api/ignore_groups.py` | Yes | JSON body: `{"id": int, "status": bool/int}` | JSON `{status, msg}` | Mutates ignore list |
| `/clear_ignore_group` | `POST` | `web/api/ignore_groups.py` | Yes | none | JSON `{status, msg}` | Clears ignore list |

## Current Authentication Behavior

Source: `pagermaid/web/api/utils.py`

- Protected endpoints use `authentication()` dependency.
- Auth accepts either:
  - `token` request header
  - `token_ck` cookie
- If `WEB_SECRET_KEY` is set, the dependency accepts:
  - a JWT signed with `WEB_SECRET_KEY`
  - or the raw `WEB_SECRET_KEY` itself as credential

Current UI behavior:

- `/login` AMIS page stores token in `localStorage`.
- `/admin` AMIS request adaptor reads token from `localStorage` and sends it as `token` header.
- `/login` also sets a `token_ck` cookie on successful login.

## Current Page to API Mapping

| Page / Route | Source | Current Backing APIs | Notes |
| --- | --- | --- | --- |
| Admin shell `/admin` | `web/pages/main.py` | Aggregates child pages below | AMIS app entrypoint |
| Login `/login` | `web/pages/login.py` | `POST /pagermaid/api/login` | On success stores token in `localStorage` and redirects to `/admin` |
| Home `/home` | `web/pages/home_page.py` | `GET /pagermaid/api/status`, `GET /pagermaid/api/log`, `GET /pagermaid/api/run_sh`, `GET /pagermaid/api/run_eval`, `POST /pagermaid/api/bot_update`, `POST /pagermaid/api/bot_restart` | Includes dangerous operations |
| Command alias `/bot_config/command_alias` | `web/pages/command_alias.py` | `GET /pagermaid/api/command_alias`, `POST /pagermaid/api/command_alias`, `GET /pagermaid/api/test_command_alias` | CRUD plus test helper |
| Ignore groups `/bot_config/ignore_groups` | `web/pages/ignore_groups.py` | `GET /pagermaid/api/get_ignore_group_list`, `POST /pagermaid/api/set_ignore_group_status` | `clear_ignore_group` exists but is not wired into current AMIS page |
| Local plugins `/plugins/local` | `web/pages/plugin_local_manage.py` | `GET /pagermaid/api/get_local_plugins`, `POST /pagermaid/api/set_local_plugin_status` | `remove_local_plugin` exists but is not wired into current AMIS page |
| Remote plugins `/plugins/remote` | `web/pages/plugin_remote_manage.py` | `GET /pagermaid/api/get_remote_plugins`, `POST /pagermaid/api/set_remote_plugin_status` | Installs or removes remote plugins |
| QR login `/web_login` | `web/api/web_login.py` + `web/html/web_login.html` | `GET /pagermaid/api/web_login`, `POST /pagermaid/api/web_login` | Plain HTML/JS page, separate from AMIS |

## Current Config Usage

Relevant fields currently read by web code:

| Config Field | Source | Current Use |
| --- | --- | --- |
| `Config.WEB_ENABLE` | `pagermaid/config.py` | Controls whether web server starts |
| `Config.WEB_SECRET_KEY` | `pagermaid/config.py` | Login secret and JWT signing key |
| `Config.WEB_HOST` | `pagermaid/config.py` | Uvicorn bind host |
| `Config.WEB_PORT` | `pagermaid/config.py` | Uvicorn bind port |
| `Config.WEB_ORIGINS` | `pagermaid/config.py` | CORS allow origins |
| `Config.WEB_LOGIN` | `pagermaid/config.py` | Alters startup/login flow in `__main__.py` |

## Current Global and Shared State

| State | Location | Current Role |
| --- | --- | --- |
| `web` singleton | `pagermaid/web/__init__.py` | Holds FastAPI app and uvicorn task handles |
| `web_login` singleton | `pagermaid/web/api/web_login.py` | Holds QR login state across requests |
| `plugin_manager` | `pagermaid/common/plugin.py` | Shared plugin state used by web mutation routes |
| `ignore_groups_manager` | `pagermaid/common/ignore.py` | Shared ignore group state |

## Dangerous or Sensitive Operations

| Endpoint | Current Exposure | Why It Is Sensitive |
| --- | --- | --- |
| `/pagermaid/api/run_sh` | Wired into home page | Arbitrary shell execution |
| `/pagermaid/api/run_eval` | Wired into home page | Arbitrary Python execution in-process |
| `/pagermaid/api/bot_update` | Wired into home page | Changes running installation |
| `/pagermaid/api/bot_restart` | Wired into home page | Stops bot/web tasks |
| `/pagermaid/api/set_local_plugin_status` | Wired into UI | Changes plugin state and reloads |
| `/pagermaid/api/remove_local_plugin` | Exists, not wired into UI | Removes plugin and reloads |
| `/pagermaid/api/set_remote_plugin_status` | Wired into UI | Installs/removes plugins and reloads |
| `/pagermaid/api/set_ignore_group_status` | Wired into UI | Changes runtime ignore behavior |
| `/pagermaid/api/clear_ignore_group` | Exists, not wired into UI | Clears ignore state |

## Current Risks

- App assembly, config use, and runtime control are coupled together.
- Auth currently mixes `localStorage`, cookie, JWT, and raw secret acceptance.
- Dangerous endpoints are part of the normal admin surface.
- Some mutation endpoints exist without being surfaced in the current UI.
- Route contracts are implicit and mostly untyped at the request/response level.
