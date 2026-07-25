# Notebooks

Exploratory analysis lives here, cleanly separated from application code.

Rules of the road:

- Connect to Postgres read-only with the same URL as the app:
  `postgresql://pf:pf@localhost:5432/problemfinder`.
- Never import from `problemfinder`; notebooks consume the database, not the codebase.
- Anything a notebook proves useful enough to keep becomes a query service or an
  enrichment pass, with tests, in `backend/`.
