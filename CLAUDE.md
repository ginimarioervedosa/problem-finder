# problem-finder

## Project Overview

A local, single-user research tool that ingests public complaint, regulatory, forum and
review data into one normalised schema, so problem themes affecting high earners and
HNW individuals can be ranked, filtered, trended, and drilled to the original evidence.
No multi-tenancy, no auth, no deployment. Optimise for clarity, reproducibility, and
ease of adding new data sources, never for scale.

## Key Directories

| Path | Purpose |
|---|---|
| `backend/src/problemfinder/domain/` | Pure Pydantic models. No I/O, no framework imports. |
| `backend/src/problemfinder/sources/` | Source protocol, registry, shared HTTP client; one adapter package per source under `adapters/`. |
| `backend/src/problemfinder/persistence/` | ORM rows, domain mapping, repositories, Alembic migrations. |
| `backend/src/problemfinder/ingestion/` | Source-agnostic pipeline: compliance gate, write-once archive, dedupe-on-store. |
| `backend/src/problemfinder/enrichment/` | Derived attributes: pure rule passes, the taxonomy loader, the versioned runner. |
| `backend/src/problemfinder/queries/` | Read services backing the API. |
| `backend/src/problemfinder/api/` | Thin FastAPI routers. No business logic. |
| `backend/src/problemfinder/cli/` | Typer CLI (`pf`); every operation runs from here. |
| `backend/tests/` | Mirrors `src/problemfinder` exactly; `tests/support/` holds builders and stubs. |
| `frontend/src/routes/` | TanStack Router file-based routes; routes compose features. |
| `frontend/src/features/` | Feature slices; features never import other features. |
| `frontend/src/components/`, `api/`, `lib/` | Shared layer. `api/schema.d.ts` is generated, never edited. |
| `data/archive/` | Immutable content-addressed raw payloads. Never modify or delete. |
| `notebooks/` | Exploratory analysis; reads the database, never imports the app. |

## Non-Negotiable Constraints

These are acceptance criteria, mechanically enforced where possible.

1. **One concept per file.** One public class/function/component per file as the default;
   tightly coupled small value objects may co-locate with their owner.
2. **File length: 150 soft, 250 hard.** Enforced by `scripts/check_file_length.py` and
   ESLint `max-lines`. A file near the ceiling is doing too much: split it.
3. **No duplicated logic.** jscpd fails the build on clones. Shared behaviour lives in one
   named module and is imported; never copy between adapters or between backend and frontend.
4. **No `utils.py`, no `helpers.ts`.** Utility code is grouped by domain concept with a real
   name (`identity.py`, `format.ts`). The single exception is `frontend/src/lib/utils.ts`,
   which is shadcn's vendored `cn` helper.
5. **Single source of truth for types.** Pydantic domain models are canonical. API types
   flow Pydantic -> OpenAPI -> `openapi-typescript`; regenerate with `make openapi` after
   any API-visible model change and commit the diff (CI fails on drift). The ORM is kept in
   lockstep by `tests/persistence/test_mapping_parity.py`.
6. **Types everywhere.** `mypy --strict` and TS `strict` are on. No `Any`/`any` without a
   written justification comment on the line.
7. **Adding a source touches nothing in core.** One new package under `sources/adapters/`
   plus one entry in `backend/config/sources.toml`. import-linter fails anything else.
8. **Every raw payload is archived immutably before parsing.** The pipeline order
   (fetch -> archive -> parse) is a tested invariant. Reparsing history must never need a refetch.
9. **The compliance gate is code, not judgement.** Every adapter declares a `SourcePolicy`
   (method, robots status, terms review date, rate limit, identifying user agent).
   `ingestion/compliance.py` refuses non-compliant adapters; there is no override flag.
10. **Derived attributes are disposable.** Enrichment is versioned and recomputable from
    stored signals with one command. Never make raw ingestion depend on enrichment.

## Layering Contract

Dependencies point inwards only. Enforced by import-linter (backend) and
eslint-plugin-boundaries (frontend); the TOML source of truth is in `backend/pyproject.toml`.

```
cli, worker  ->  api  ->  queries, ingestion, enrichment  ->  sources, persistence  ->  domain
```

- Modules on the same tier are mutually independent (sources never import persistence,
  and ingestion never imports enrichment: raw collection cannot depend on opinions).
- Enrichment's runner (`enrichment/run.py`) orchestrates persistence like ingestion
  does, but the rules themselves (`passes/`, `taxonomy.py`, `ruleset.py`, `derive.py`)
  are pure over domain models; a dedicated import-linter contract enforces it.
- ML lives only in `enrichment/ml/`, behind the `ml` uv extras group and lazy
  imports: the core install carries zero ML dependencies, an import-linter contract
  forbids direct ML imports anywhere else, and `tests/enrichment/test_zero_ml_core.py`
  proves core entry points never load them. CI installs without extras.
- `domain` imports nothing but the standard library and pydantic.
- `httpx`, `selectolax`, and Playwright exist only inside `sources/`; the rest of the
  codebase never knows how a source is fetched.
- Adapters never import each other.
- Frontend: `routes -> features -> shared`; features never import sibling features; server
  state lives in TanStack Query only, never in Zustand.

## Naming Conventions

- Source keys are snake_case and double as registry keys, config entries, and
  `source_key` on every signal: `fos_complaints`, `fos_decisions`, `reddit`.
- Adapter packages expose `adapter.py` (protocol implementation), with `discover.py`,
  `parser.py`, `normalise.py` alongside as needed.
- ORM classes end in `Row` (`SignalRow`); domain models never do.
- External IDs are stable within a source's namespace: `h1-2025:<firm-slug>:<category-slug>`.
- Signal ids are UUIDv5 of `(source_key, external_id)` via `domain/identity.py`; never
  mint signal ids any other way.
- Tests mirror source paths exactly; shared test infrastructure lives in `tests/support/`.

## Command Reference

| Command | Does |
|---|---|
| `make up` / `make down` | Start/stop Postgres 17 in Docker |
| `make install` | uv sync + npm install + pre-commit hooks |
| `make migrate` | `alembic upgrade head` |
| `make ingest SOURCE=<key>` | Run one source through the pipeline |
| `make dev` | API on :8000 and Vite on :5173 together |
| `make openapi` | Export openapi.json and regenerate `schema.d.ts` |
| `make check` | Every quality gate (backend, frontend, shared) |
| `make test` | Test suites only |
| `cd backend && uv run pf ingest list` | Show registered sources, method, enablement |
| `cd backend && uv run pf ingest run <key> --full` | Ingest ignoring the saved cursor for one run |
| `cd backend && uv run pf reparse <key>` | Replay a source's archive through parse + normalise, no refetch |
| `cd backend && uv run pf enrich run` | Compute derived attributes for signals that have none |
| `cd backend && uv run pf enrich run --recompute` | Rebuild every derived attribute (idempotent; writes only changes) |
| `cd backend && uv sync --extra ml` | Install the optional ML extras (sentence-transformers, scikit-learn) |
| `cd backend && uv run pf ml cluster` | Embed verbatims, cluster, propose candidate themes (needs ml extras) |
| `cd backend && uv run pf ml suggestions` | List theme suggestions and review state |
| `cd backend && uv run pf ml accept <cluster> [--theme <name>]` | Map a proposed cluster onto a theme |
| `cd backend && uv run pf ml reject <cluster>` | Retire a proposed cluster |
| `cd backend && uv run pf serve worker` | Cron-scheduled ingests from sources.toml, one run at a time |
| `cd backend && uv run pf db revision -m "..."` | Autogenerate a migration |

Database tests need `make up` first; they fail loudly, never skip silently.

Ingestion is incremental by default: each source's resume point lives in the
`cursors` table and discovery starts from it. Per-source knobs (the fos_decisions
date window, Reddit subreddits) live in an `options` table in `sources.toml`, read
only by the owning adapter. Reddit needs `PF_REDDIT_CLIENT_ID` and
`PF_REDDIT_CLIENT_SECRET` in `.env` and stays disabled until they exist.

## Behavioural Foundation

1. **Don't assume. Surface tradeoffs.** Ambiguous request: ask. Hidden decision: name it.
2. **Minimum work that solves the problem.** No speculative abstraction; today's problem
   at today's complexity.
3. **Touch only what's asked.** Surgical changes; leave pre-existing oddities alone.
4. **Define done before starting; verify before declaring finished.** `make check` green
   plus the phase's acceptance criteria.
5. **Plan phase by phase.** Never cross a phase boundary without a review pause. Always ask
   before destructive or irreversible operations, including migrations that drop data.

## Absolute Rules

- Never commit secrets or credentials. `.env` stays untracked.
- Never force-push `main`. Never self-merge a PR. Conventional Commits throughout.
- Never write to `data/archive/` except through `ingestion/archive.py`.
- Never edit generated files (`schema.d.ts`, `routeTree.gen.ts`, `openapi.json`) by hand.
- If a source's terms prohibit automated collection and no API exists, it becomes
  manual-import-only. A smaller lawful corpus beats a larger risky one.

## Skills

| Skill | Use for |
|---|---|
| `.claude/skills/new-source-adapter/` | Scaffolding a new data source adapter |
| `.claude/skills/new-dashboard-view/` | Scaffolding a new frontend view |
| `.claude/skills/add-migration/` | Adding an Alembic migration safely |

## Issue Tracker

Notion Issue/Feature Log (personal space):
https://app.notion.com/p/0a7d1a95561f4d37bdafaac1f2818f28

At the start of any non-trivial task: query it for Open items, flag relevant ones,
set items In Progress when work begins, and Resolved only when the change is
committed and verified.
