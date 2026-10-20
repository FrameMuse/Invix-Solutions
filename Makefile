.PHONY: up down scale scale-down logs seed lint test build

up:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

down:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml down

scale:
	docker compose up -d --build --scale api=2 --scale bot=2 --scale web=2

scale-down:
	docker compose down

logs:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml logs -f api web bot

seed:
	@set -a; if [ -f .env ]; then . ./.env; fi; set +a; API_URL=http://localhost:18000 uv run --with httpx python scripts/seed.py

lint:
	cd apps/api && uv run ruff check .
	cd apps/bot && uv run ruff check .
	cd apps/web && bun run lint

test:
	cd apps/api && uv run pytest

build:
	cd apps/web && bun run build
