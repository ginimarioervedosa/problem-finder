---
name: new-dashboard-view
description: Scaffold a new frontend view for problem-finder — a TanStack Router route composing feature slices over the typed API client. Use whenever the user wants a new page, dashboard view, chart view, or drill-down screen in the UI.
---

# New dashboard view

The frontend layering is `routes -> features -> shared`; eslint-plugin-boundaries
enforces it. Routes compose features; features never import each other; server state
lives in TanStack Query, client state (filters, view preferences) in Zustand.

## 1. Backend first, if the view needs new data

Add or extend a query service in `backend/src/problemfinder/queries/` plus a thin
router in `api/routers/`. Then regenerate the contract:

```bash
make openapi   # exports openapi.json and regenerates frontend/src/api/schema.d.ts
```

Commit both generated files; CI fails on drift. Never hand-edit `schema.d.ts`.

## 2. Feature slice

Create `frontend/src/features/<name>/` containing:

- `use<Name>Query.ts` — a TanStack Query hook over `@/api/client`. Derive param and
  response types from the generated schema (`operations[...]["parameters"]["query"]`),
  never hand-written interfaces.
- Presentational components taking data as props (testable without the network).
- Charts: build an `EChartsOption` and render through the shared `@/components/EChart`.
- shadcn primitives from `@/components/ui/*`; dates and numbers through `@/lib/format`.

## 3. Route

Add `frontend/src/routes/<name>.tsx` with `createFileRoute`. The route wires the
hooks to the components and owns view-local state (selection, pagination). Add a nav
link in `routes/__root.tsx`. The router plugin regenerates `routeTree.gen.ts` on the
next dev/build; commit it.

## 4. Tests and gates

- Vitest + RTL test per presentational component in `frontend/tests/` (render with
  canned props; assert content and interactions; no network).
- `make check` must stay green: TS strict, eslint (max-lines 250, complexity 10,
  boundaries), vitest, jscpd.

## 5. Verify in the browser

`make dev`, open the route, and check against known database counts before declaring done.
