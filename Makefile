# Makefile — Convenience commands for Python Confidence Coach.
#
# FIRST TIME SETUP:
#   make setup          ← installs all dependencies
#   make db-start       ← starts PostgreSQL in Docker
#   make db-migrate     ← creates all tables
#
# DAILY DEVELOPMENT:
#   make dev            ← opens 3 terminal instructions (run each in a separate tab)
#
# Run each service in a separate terminal:
#   make mcp            ← starts the MCP server  (port 8001)
#   make api            ← starts the FastAPI backend (port 8000)
#   make web            ← starts the React frontend (port 5173)

.PHONY: setup db-start db-stop db-migrate dev mcp api web lint typecheck clean

# ── Setup ─────────────────────────────────────────────────────────────────────

setup: setup-backend setup-mcp setup-frontend
	@echo ""
	@echo "✓ All dependencies installed."
	@echo ""
	@echo "NEXT STEPS:"
	@echo "  1. Edit backend/.env  — add your ANTHROPIC_API_KEY and SECRET_KEY"
	@echo "  2. Edit mcp-server/.env — add your ANTHROPIC_API_KEY"
	@echo "  3. make db-start      — start PostgreSQL"
	@echo "  4. make db-migrate    — create tables"
	@echo "  5. In 3 separate terminals: make mcp | make api | make web"

setup-backend:
	@echo "→ Installing backend dependencies..."
	cd backend && pip install -e ".[dev]"

setup-mcp:
	@echo "→ Installing MCP server dependencies..."
	cd mcp-server && pip install -e "."

setup-frontend:
	@echo "→ Installing frontend dependencies..."
	cd frontend && npm install

# ── Database ──────────────────────────────────────────────────────────────────

db-start:
	@echo "→ Starting PostgreSQL..."
	docker compose up -d postgres
	@echo "✓ PostgreSQL running on localhost:5432"
	@echo "  pgAdmin available at http://localhost:5050 (after: docker compose up -d pgadmin)"

db-stop:
	docker compose down

db-migrate:
	@echo "→ Running Alembic migrations..."
	cd backend && alembic upgrade head
	@echo "✓ Database schema is up to date."

db-shell:
	docker exec -it coach_postgres psql -U coach -d confidence_coach

# ── Development servers ───────────────────────────────────────────────────────

mcp:
	@echo "→ Starting MCP server on port 8001..."
	cd mcp-server && python server.py

api:
	@echo "→ Starting FastAPI backend on port 8000..."
	cd backend && uvicorn app.main:app --reload --port 8000

web:
	@echo "→ Starting React frontend on port 5173..."
	cd frontend && npm run dev

dev:
	@echo ""
	@echo "Run each of these in a separate terminal tab:"
	@echo ""
	@echo "  Terminal 1 (MCP server):     make mcp"
	@echo "  Terminal 2 (FastAPI backend): make api"
	@echo "  Terminal 3 (React frontend):  make web"
	@echo ""
	@echo "Then open: http://localhost:5173"

# ── Code quality ──────────────────────────────────────────────────────────────

lint:
	cd backend && ruff check . --fix
	cd mcp-server && ruff check . --fix

typecheck:
	cd backend && mypy app/
	cd frontend && npm run typecheck

# ── Utilities ─────────────────────────────────────────────────────────────────

secret-key:
	@python3 -c "import secrets; print(secrets.token_hex(32))"

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null; true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null; true
	find . -name "*.pyc" -delete 2>/dev/null; true
