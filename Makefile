.PHONY: help run-mcp run-api dev up down logs test install eval

help:
	@echo Targets:
	@echo   run-mcp  - run MCP locally on :8000
	@echo   run-api  - run API locally on :8080
	@echo   dev      - run docker compose using .env.dev
	@echo   up       - alias for dev
	@echo   down     - stop containers
	@echo   logs     - follow logs
	@echo   test     - run pytest

run-mcp:
	cd mcp && python -m uvicorn mcp.server:app --reload --port 8000

run-api:
	cd api && python -m uvicorn main:app --reload --port 8080

dev:
	docker-compose --env-file .env.dev up --build

up: dev

down:
	docker-compose down -v

logs:
	docker-compose logs -f api mcp ui

test:
	python -m pip install -U pip
	pip install -r mcp/requirements.txt
	pip install pytest
	pytest -q

install:
	pip install -r mcp/requirements.txt
	pip install -r api/requirements.txt
	pip install -r requirements-dev.txt


eval:
	python -m eval.run_eval

