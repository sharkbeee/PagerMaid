# Core Runtime Stabilization Plan

This document tracks the focused stabilization work for PagerMaid's core runtime.
Keep `ROADMAP.md` high-level. Use this document to manage scope, status,
decisions, milestones, and residual risks.

## Goal

Make startup, shutdown, module and plugin loading, reload, hooks, and command
error handling predictable enough to operate and test without redesigning the
current singleton-based runtime architecture.

## Status

Status: `in_progress`

Baseline verification:

- `.venv/bin/pytest -q`
- 21 tests passed before stabilization work began.

## Current Decisions

- Preserve the current singleton services and operator-facing startup behavior.
- Continue running when an individual built-in module or external plugin fails
  to load, but report the failure clearly.
- Reject a reload request immediately when another reload is already running.
- Do not promise transactional reload rollback in this track.
- Deliver one focused commit at a time and pause for review after each commit.
- Maintain Python `>=3.8` compatibility.

## Current Runtime Audit

### Startup

The process starts through `python -m pagermaid`, which executes
`pagermaid/__main__.py`.

Current startup order:

1. Import configuration and construct global scheduler, bot, and web objects.
2. Mutate the bot parent directory and plugin import path.
3. Start the scheduler.
4. Start the web server when enabled.
5. Initialize the Telegram client through console or web login.
6. Import built-in modules and external plugins.
7. Run load-success and startup hooks.
8. Wait for bot disconnection or a shutdown signal.

Current concerns:

- Importing `pagermaid.__main__` starts the process immediately.
- Several services and mutable registries are created during module import.
- Failures during early startup are not covered by one complete cleanup path.
- Startup module and plugin failures are logged but not returned to the caller.

### Shutdown

Current shutdown can be requested by operating-system signals, Telegram
commands, web restart, cancellation, or direct process exit.

Current concerns:

- Shutdown behavior is split between `pagermaid.__main__`,
  `pagermaid.listener`, and web runtime control.
- Shutdown hooks are normally invoked from a command handler and require a
  Telegram message, so normal process shutdown does not reliably invoke them.
- Multiple shutdown requests can repeat cleanup work.
- Broad exception handling can treat cancellation as an ordinary runtime
  failure or swallow control-flow exceptions.

### Module and Plugin Loading

`load_all()` imports built-in modules followed by external plugins, refreshes
local plugin metadata, then runs load-success and startup hooks.

Current concerns:

- Individual failures are logged at info level without a reliable traceback.
- Failed external plugins are removed from the active plugin list, but callers
  receive no structured result.
- Callers cannot distinguish complete success from partial failure.

### Reload

`reload_all()` runs reload-pre hooks, clears live runtime state, reloads config
and module discovery, reloads built-in modules and external plugins, refreshes
plugin metadata, then runs load-success hooks.

Current concerns:

- Concurrent reload requests can mutate the same global state simultaneously.
- Live handlers, scheduler jobs, help data, permissions, and hooks are cleared
  before reload success is known.
- Partial failures can leave the process degraded while callers still report
  success.
- Imported plugin side effects cannot be reliably rolled back with the current
  architecture.

### Hooks and Command Errors

Hooks are stored in global sets and generally executed with `asyncio.gather`.
Command handling catches and reports errors from listener callbacks.

Current concerns:

- One failed hook can prevent useful reporting for other hook executions.
- Hook failure logs do not identify the failing callable with a traceback.
- Commands configured with `diagnostics=False` can return before a local error
  is logged.
- Broad `BaseException` catches can intercept cancellation, `SystemExit`, and
  other control-flow exceptions.

## Non-Goals

- Replacing singleton services with a runtime container.
- Introducing registry-based module, plugin, hook, or command registration.
- Providing transactional reload staging or rollback.
- Redesigning configuration, authentication, AMIS, or the public plugin API.
- Changing version numbers or preparing release notes.

These concerns remain part of the later runtime architecture and release work.

## Working Rules

- One milestone and one focused commit at a time.
- Run targeted tests, the full test suite, and `git diff --check` before every
  commit.
- Pause for review after every commit.
- Preserve current behavior with characterization tests before changing it.
- Do not mix unrelated cleanup into this track.
- Document limitations rather than implying guarantees the current
  architecture cannot provide.

## Milestones

### Milestone 0. Audit and Plan

Status: `done`

Deliverables:

- Document current startup, shutdown, load, reload, hook, and command-error
  flows.
- Record scope decisions, risks, non-goals, and acceptance criteria.
- Mark the roadmap item as in progress.

Exit criteria:

- The stabilization boundary is explicit.
- Later implementation work can be reviewed against documented behavior.

### Milestone 1. Runtime Characterization

Status: `done`

Deliverables:

- Characterization tests for initial module and plugin loading.
- Coverage for continuing after individual load failures.
- Coverage for failed external plugin removal.
- Coverage for current reload ordering and state clearing.
- Coverage for startup and reload hook invocation.

Exit criteria:

- Current runtime behavior is captured before production behavior changes.

### Milestone 2. Hook Isolation and Command Diagnostics

Status: `done`

Deliverables:

- Isolate individual hook failures.
- Report failed hook names and tracebacks.
- Return structured hook failure information.
- Always log command exceptions locally.
- Allow control-flow exceptions to propagate where required.

Exit criteria:

- One hook failure does not hide other hook outcomes.
- Command failures produce actionable local diagnostics.

### Milestone 3. Structured Load and Reload Results

Status: `done`

Deliverables:

- Internal startup and reload result types.
- Successful module and plugin lists.
- Failure stage, component, exception type, and message.
- Success, partial-failure, and busy statuses.
- Summary logging and caller-facing success checks.

Exit criteria:

- Callers can distinguish complete success from partial failure.
- Individual load failures remain non-fatal.

### Milestone 4. Serialized Reload

Status: `done`

Deliverables:

- A single reload lock.
- Immediate busy results for concurrent reload requests.
- Accurate Telegram and web responses for busy and partial-failure outcomes.
- Translated reload busy and partial-failure messages.

Exit criteria:

- Reload operations cannot run concurrently.
- Reload callers no longer claim unconditional success.

### Milestone 5. Centralized Process Lifecycle

Status: `done`

Deliverables:

- An import-safe `pagermaid.__main__` entrypoint.
- An explicit, idempotent shutdown-request coordinator.
- One startup cleanup boundary.
- Deterministic shutdown ordering.
- Process-level shutdown hook execution.
- Smoke tests for successful boot, startup failure, shutdown requests, repeated
  shutdown, and cleanup failures.

Exit criteria:

- Shutdown hooks run once during normal process shutdown.
- Started components are cleaned up after startup failure.
- Cancellation and process-control exceptions are not swallowed accidentally.

### Milestone 6. Closure

Status: `planned`

Deliverables:

- Record final behavior, verification, and residual risks.
- Update roadmap status only after all acceptance criteria pass.
- Leave transactional reload and registry architecture explicitly deferred.

Exit criteria:

- The stabilization acceptance criteria pass.
- Remaining architecture work has a clear boundary.

## Acceptance Criteria

- Existing operator startup behavior remains compatible.
- Individual built-in module or external plugin failures do not terminate the
  process.
- Reload requests cannot run concurrently.
- No caller reports reload success after a partial failure.
- Shutdown hooks run once during normal process shutdown.
- Startup failures clean up already-started components.
- Cancellation, `KeyboardInterrupt`, and `SystemExit` are not swallowed
  accidentally.
- Existing and new tests pass after every implementation commit.

## Residual Risks

- Reload still clears and rebuilds live global state before complete success is
  known.
- Arbitrary module and plugin import side effects cannot be rolled back.
- Global singleton services and registries remain coupled to import order.
- Some plugins may depend on undocumented reload or shutdown behavior.

These risks require the later registry-based runtime architecture rather than
incremental stabilization changes.
