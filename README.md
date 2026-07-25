# problem-finder

A local, single-user research tool that ingests public complaint, regulatory, forum and
review data into one normalised schema, so problem themes affecting high earners and
high-net-worth individuals can be ranked, filtered, trended, and drilled down to the
original evidence. It runs entirely on this machine: no auth, no deployment, no scale.

## Setup

Prerequisites: Docker Desktop, [uv](https://docs.astral.sh/uv/), Node 22+, make.

```bash
make install   # backend deps (uv), frontend deps (npm), git hooks
make up        # Postgres 17 in Docker
make migrate   # apply the schema
make ingest SOURCE=fos_complaints   # first real data (a few minutes, politely rate-limited)
make dev       # API on :8000, UI on http://localhost:5173
```

`make check` runs every quality gate: ruff, mypy --strict, import-linter, pytest,
tsc, eslint, vitest, file-length ceilings, and jscpd duplication. Database tests
need `make up` first.

## How it works

Every source implements one `Source` protocol (`discover`, `fetch`, `parse`,
`normalise`) and declares a `SourcePolicy` (collection method, robots status, terms
review date, rate limit, identifying user agent). A compliance gate refuses
non-compliant adapters in code. The pipeline archives every raw payload immutably
(content-addressed, write-once) *before* parsing, so parsers can be improved and
history reparsed without ever refetching. Signals are one of two kinds: `verbatim`
(one person's words) or `aggregate` (a published statistic). Types flow from Pydantic
domain models through OpenAPI into generated TypeScript; nothing is hand-maintained
twice.

The layering contract (enforced by import-linter and eslint-plugin-boundaries):

```
cli, worker -> api -> queries, ingestion -> sources, persistence, enrichment -> domain
```

## Add a data source in under five minutes

1. **Check compliance first.** Read the source's robots.txt and terms. Prefer an
   official API or bulk download. If automated collection is prohibited and there is
   no API, stop: the source is manual-import-only.

2. **Create the adapter package** `backend/src/problemfinder/sources/adapters/<key>/`
   with an `adapter.py`:

   ```python
   @register
   class MySource:
       key: ClassVar[str] = "my_source"
       version: ClassVar[int] = 1
       policy: ClassVar[SourcePolicy] = SourcePolicy(
           method=IngestionMethod.OFFICIAL_API,
           robots_status=RobotsStatus.NOT_APPLICABLE,
           terms_reviewed=date.today(),          # the date YOU read the terms
           terms_notes="where the terms live and what they permit",
           rate_limit=RateLimit(requests=1, per_seconds=2.0),
           user_agent="problem-finder/0.1 (single-user research tool; contact: you@example.org)",
       )
   ```

   Implement `discover` (yield `WorkItem`s), `fetch` (one `RawDocument` per item;
   `sources.fetch.fetch_one` covers the plain-GET case), `parse` (pure: bytes to
   `ParsedRecord`s), `normalise` (record + provenance to a `VerbatimSignal` or
   `AggregateSignal`), and `cursor_after`. Signal ids come from
   `domain.identity.signal_id_for`; every HTTP call goes through
   `sources.http.client_for`.

3. **Add one config entry** in `backend/config/sources.toml`:

   ```toml
   [sources.my_source]
   enabled = true
   schedule = "0 7 * * *"
   ```

4. **Add tests** under `backend/tests/sources/adapters/<key>/` with a real trimmed
   fixture: parser correctness, a hypothesis garbage-bytes property test, and
   registration.

5. **Run it**: `make ingest SOURCE=my_source`, then `make check`.

Nothing in core changes; import-linter fails the build if an adapter reaches outside
its package. The `.claude/skills/new-source-adapter` skill automates this scaffold.

## Layout

| Path | What lives there |
|---|---|
| `backend/src/problemfinder/` | Layered Python backend (see CLAUDE.md for the contract) |
| `frontend/src/` | React 19 + TanStack, feature-sliced, generated API types |
| `data/archive/` | Immutable content-addressed raw payloads (gitignored) |
| `notebooks/` | Exploratory analysis, reads the database only |
| `.claude/skills/` | Scaffolding skills for adapters, views, migrations |

## Exploring the data

The UI at `localhost:5173` gives ranked volumes by category, filterable by free-text
search (Postgres full-text over titles and bodies, with phrase and `-exclusion`
syntax), firm, category, kind and period, with drill-through to each signal's
provenance (archived payload hash, ingestion run, link to the original). The Trends
view draws monthly volumes as lines per category, firm, or source; the Runs view
shows the ingestion ledger (counts, durations, errors) for every pipeline execution.
Notebooks can connect read-only to `postgresql://pf:pf@localhost:5432/problemfinder`.

## Keeping data fresh

Ingestion is incremental: every source persists a resume cursor, so a rerun fetches
only what is new (`--full` ignores the cursor for one run). Transient HTTP failures
retry with exponential backoff inside the shared client. To run on a schedule:

```bash
cd backend && uv run pf serve worker   # cron expressions live in sources.toml
```

The worker shells the same `pf ingest run` command a human would use and runs one
ingest at a time, so sources sharing a host never fetch concurrently.

The Reddit source uses the official Data API and needs OAuth credentials in `.env`
(`PF_REDDIT_CLIENT_ID`, `PF_REDDIT_CLIENT_SECRET`, from a script app created at
reddit.com/prefs/apps); it stays disabled in `sources.toml` until they exist.
Subreddits are configured there too.

## Reparsing history

Parsers are disposable by design. After improving one, bump the adapter's `version`
and replay the archive; nothing is refetched:

```bash
cd backend && uv run pf reparse fos_complaints
```

Signal identities are stable (UUIDv5 of source and external id), so regenerated
signals overwrite in place.
