.DEFAULT_GOAL := help

# --- environment --------------------------------------------------------------
up: ## Start Postgres in Docker and wait until healthy
	docker compose up -d --wait

down: ## Stop Postgres (the data volume survives)
	docker compose down

install: ## Install backend and frontend dependencies plus git hooks
	cd backend && uv sync
	cd frontend && npm install
	cd backend && uv run pre-commit install

# --- database -----------------------------------------------------------------
migrate: ## Apply database migrations
	cd backend && uv run alembic upgrade head

# --- ingestion ----------------------------------------------------------------
ingest: ## Ingest one source: make ingest SOURCE=fos_complaints
	cd backend && uv run pf ingest run $(SOURCE)

# --- development servers --------------------------------------------------------
api: ## Run the FastAPI server on :8000
	cd backend && uv run pf serve api

web: ## Run the Vite dev server on :5173
	cd frontend && npm run dev

dev: ## Run API and frontend together
	$(MAKE) -j2 api web

# --- type generation ------------------------------------------------------------
openapi: ## Export openapi.json and regenerate the frontend API types
	cd backend && uv run python ../scripts/export_openapi.py
	cd frontend && npm run generate:api

# --- quality gates ----------------------------------------------------------------
check: check-backend check-frontend check-shared ## All quality gates

check-backend: ## Backend gates: format, lint, types, layering, tests
	cd backend && uv run ruff format --check .
	cd backend && uv run ruff check .
	cd backend && uv run mypy src tests
	cd backend && uv run lint-imports
	cd backend && uv run pytest -q

check-frontend: ## Frontend gates: types, lint, tests
	cd frontend && npx tsc --noEmit
	cd frontend && npx eslint src tests
	cd frontend && npm run -s test -- --run

check-shared: ## Cross-cutting gates: file length ceilings, duplication
	python3 scripts/check_file_length.py
	frontend/node_modules/.bin/jscpd --config .jscpd.json

test: ## Backend and frontend test suites only
	cd backend && uv run pytest -q
	cd frontend && npm run -s test -- --run

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*##"}; {printf "  %-16s %s\n", $$1, $$2}'

.PHONY: up down install migrate ingest api web dev openapi check check-backend check-frontend check-shared test help
