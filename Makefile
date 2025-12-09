install:
	cd mcp && pip install -r requirements.txt
	cd api && pip install -r requirements.txt

# ------------------------------------
# ENVIRONMENT MANAGEMENT
# ------------------------------------

env-dev:
	copy .env.dev .env

env-prod:
	copy .env.prod .env



run-mcp:
	cd mcp && uvicorn server:app --reload --port 8000

run-api:
	cd api && uvicorn main:app --reload --port 8080

run-ui:
	cd ui && python -m http.server 5050

dev-local: env-dev
	@echo "Running API, MCP and UI locally (no docker)"
	@echo "Open three shells and run:"
	@echo "launch mcp (8000) :   make run-mcp"
	@echo "launch api (8080) :  make run-api"
	@echo "launch ui (5050) :   make run-ui"

prod:
    export $(shell type .env.prod | xargs) && \
    uvicorn api.main:app --host 0.0.0.0 --port 8080

# ------------------------
# LOCAL DEVELOPMENT
# ------------------------


# ------------------------------------
# DOCKER DEVELOPMENT
# ------------------------------------

dev: env-dev
	docker-compose up --build

down:
	docker-compose down

# ------------------------------------
# PRODUCTION BUILD (local)
# ------------------------------------

build-prod: env-prod
	docker-compose -f docker-compose.yml build


# ------------------------------------
# PRODUCTION RUN (local)
# ------------------------------------

run-prod: env-prod
	docker-compose -f docker-compose.yml up -d


# ------------------------------------
# LOGS
# ------------------------------------

logs:
	docker-compose logs -f