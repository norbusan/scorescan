COMPOSE ?= docker compose
SERVICES = backend worker frontend valkey

.DEFAULT_GOAL := help

.PHONY: help build up down restart logs ps shell-backend shell-worker shell-frontend \
        migrate superuser clean lint dev-backend dev-frontend test-preprocessing \
        lock sync rebuild-worker

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "Targets:\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

## ---- Docker Compose ----

build: ## Build all images
	$(COMPOSE) build

up: ## Start all services in the background
	$(COMPOSE) up -d
	@echo "Frontend: http://localhost:5173"
	@echo "API:      http://localhost:8000  (docs at /docs)"

down: ## Stop and remove all services
	$(COMPOSE) down

restart: ## Restart all services
	$(COMPOSE) restart

logs: ## Tail logs from all services
	$(COMPOSE) logs -f --tail=100

ps: ## Show service status
	$(COMPOSE) ps

rebuild-worker: ## Rebuild only the worker (e.g. after touching oemer/Audiveris layers)
	$(COMPOSE) build --no-cache worker
	$(COMPOSE) up -d worker

## ---- Shells ----

shell-backend: ## Open a shell in the running backend container
	$(COMPOSE) exec backend bash

shell-worker: ## Open a shell in the running worker container
	$(COMPOSE) exec worker bash

shell-frontend: ## Open a shell in the running frontend container
	$(COMPOSE) exec frontend sh

## ---- One-off admin tasks ----

migrate: ## Apply ad-hoc sqlite migration scripts against the running backend
	$(COMPOSE) exec backend python3 migrate_add_user_approval.py
	$(COMPOSE) exec backend python3 migrate_add_password_reset.py
	$(COMPOSE) exec backend python3 migrate_add_quality_warnings.py

superuser: ## Interactively create a superuser account
	$(COMPOSE) exec backend python3 create_superuser.py

## ---- Local (non-Docker) development ----

# These run against your host Python/Node; useful for tight inner loops.
# Still need valkey, which you can start with `make valkey-only`.

valkey-only: ## Start only valkey (for host-side dev)
	$(COMPOSE) up -d valkey

dev-backend: ## Run backend + worker on the host against dockerised valkey
	cd backend && uv sync
	cd backend && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 & \
	cd backend && uv run celery -A app.tasks.celery_app worker --loglevel=info

dev-frontend: ## Run the Vite dev server on the host
	cd frontend && npm install && npm run dev

test-preprocessing: ## Run the image preprocessing smoke test on the host
	cd backend && uv run python test_preprocessing.py

## ---- uv / dependency management ----

lock: ## Refresh backend/uv.lock
	cd backend && uv lock

sync: ## Install backend deps into a local .venv (includes oemer group)
	cd backend && uv sync --group oemer

## ---- Cleanup ----

clean: ## Remove built images and volumes (keeps storage/)
	$(COMPOSE) down --rmi local --volumes --remove-orphans

clean-all: ## Nuke images, volumes, AND local storage/ (DANGEROUS)
	$(COMPOSE) down --rmi local --volumes --remove-orphans
	rm -rf backend/storage/uploads/* backend/storage/musicxml/* backend/storage/pdf/*
