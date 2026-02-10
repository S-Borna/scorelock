.PHONY: help up down logs build test lint migrate seed

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── Docker ─────────────────────────────────────────────────

up: ## Start all services
	docker compose up -d

up-dev: ## Start all services including dev tools (Redis UI)
	docker compose --profile dev up -d

up-all: ## Start everything including monitoring (Prometheus, Grafana)
	docker compose --profile dev --profile monitoring up -d

down: ## Stop all services
	docker compose down

build: ## Rebuild all images
	docker compose build --no-cache

logs: ## Tail logs for all services
	docker compose logs -f

logs-api: ## Tail backend API logs
	docker compose logs -f backend

logs-worker: ## Tail Celery worker logs
	docker compose logs -f celery-worker

# ── Backend ────────────────────────────────────────────────

shell: ## Open a shell in the backend container
	docker compose exec backend bash

test: ## Run backend tests
	docker compose exec backend python -m pytest tests/ -v

lint: ## Lint backend code
	docker compose exec backend ruff check .

format: ## Format backend code
	docker compose exec backend ruff format .

# ── Database ───────────────────────────────────────────────

db-shell: ## Open psql shell
	docker compose exec db psql -U scorelock -d scorelock

migrate: ## Run Alembic migrations
	docker compose exec backend alembic upgrade head

migrate-new: ## Create a new migration (usage: make migrate-new msg="add users table")
	docker compose exec backend alembic revision --autogenerate -m "$(msg)"

# ── Data Pipeline ──────────────────────────────────────────

fetch-fixtures: ## Manually trigger fixture fetch
	docker compose exec celery-worker celery -A app.core.celery_app call app.services.tasks.fetch_daily_fixtures

fetch-standings: ## Manually trigger standings update
	docker compose exec celery-worker celery -A app.core.celery_app call app.services.tasks.update_standings

run-predictions: ## Manually trigger ML predictions
	docker compose exec celery-worker celery -A app.core.celery_app call app.services.tasks.run_daily_predictions

# ── Monitoring ─────────────────────────────────────────────

urls: ## Show all service URLs
	@echo ""
	@echo "  API:        http://localhost:8000"
	@echo "  API Docs:   http://localhost:8000/docs"
	@echo "  Redis UI:   http://localhost:8001"
	@echo "  Prometheus: http://localhost:9090"
	@echo "  Grafana:    http://localhost:3001"
	@echo ""
