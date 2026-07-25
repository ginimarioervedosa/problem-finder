---
name: new-source-adapter
description: Scaffold a new data source adapter for problem-finder — compliance review first, then the adapter package, config entry, and fixture-backed tests. Use whenever the user wants to add, scaffold, or wire up a new data source, connector, or ingestion adapter.
---

# New source adapter

Adding a source means one new package plus one config entry. Core code never changes;
import-linter fails the build if it does.

## 1. Compliance review (blocking, do this before any code)

1. Fetch and read `robots.txt` for the source's host.
2. Find and read the site's terms of use / legal page.
3. Prefer an official API or bulk download over scraping. If terms prohibit automated
   collection and no API exists, STOP and report: the source is manual-import-only.
4. Record findings for the `SourcePolicy`: method, robots status, today's date as
   `terms_reviewed`, and a `terms_notes` string naming the pages read and what they permit.
   The gate in `ingestion/compliance.py` refuses: scraping without robots ALLOWED,
   robots DISALLOWED for any automated method, terms reviews older than 12 months,
   and anonymous user agents.

## 2. Scaffold the package

Create `backend/src/problemfinder/sources/adapters/<key>/` (snake_case key):

- `__init__.py` — one-paragraph docstring: what the source is, what one signal represents.
- `adapter.py` — `@register` class with `key`, `version = 1`, `policy`, and the five
  protocol methods. Copy the shape from `adapters/fos_complaints/adapter.py`.
  Plain one-GET fetches delegate to `sources.fetch.fetch_one`; the user agent is
  `sources.http.IDENTIFYING_USER_AGENT`; shared helpers live in `sources.page_base`
  (FOS `<base>` tag resolution) and `sources.record_fields` (typed field readers).
  Never copy helper code between adapters; promote it to a named shared module.
- `parser.py` — pure bytes -> `ParsedRecord`s. Raise `SourceParseError` for bad payloads,
  never anything else. Fold `work_item.request_hints` into record fields.
- `normalise.py` — `ParsedRecord` + `Provenance` -> `VerbatimSignal` or `AggregateSignal`.
  Signal id via `domain.identity.signal_id_for(key, external_id)`. `retrieved_at` is
  `provenance.fetched_at` (keeps normalise deterministic). Anything that doesn't
  generalise goes in `extras`, never dropped.
- `discover.py` — only if discovery is more than a few lines.

Rules: every HTTP call goes through `sources.http.client_for(key, policy)` (shared
rate limit and user agent). Never import another adapter. Files stay under 150 lines.

## 3. One config entry

Append to `backend/config/sources.toml`:

```toml
[sources.<key>]
enabled = true
schedule = "0 7 * * 1"
```

## 4. Tests

Mirror the package under `backend/tests/sources/adapters/<key>/`:

- A real, trimmed fixture file in `fixtures/` (never synthetic-only).
- Parser: exact assertions on known rows, plus a hypothesis property test that garbage
  bytes raise only `SourceParseError`.
- Normalise: field mapping, deterministic ids, extras carried.
- Adapter: registered under its key; policy passes `ingestion.compliance.check`.
- Discovery: respx-mocked pages if discovery fetches anything.

## 5. Verify

```bash
make ingest SOURCE=<key>   # real run; inspect the printed ledger and any errors
make check                 # every gate must stay green
```

Report the run counts (fetched/parsed/stored/deduplicated) and any error-ledger
entries before declaring the adapter done.
