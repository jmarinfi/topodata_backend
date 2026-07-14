---
name: run-topodata-backend
description: Run, start, build, test, and screenshot the TopoData Backend FastAPI server
---

# TopoData Backend - FastAPI Server

TopoData Backend is a RESTful API for topographic data management built with FastAPI, SQLAlchemy 2.0+, and SQLite. This skill launches the server and runs smoke tests against all major endpoints.

## Prerequisites

**System dependencies:**
```bash
# Install uv package manager if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**No additional OS packages required** - FastAPI runs on pure Python.

## Setup

```bash
# Install dependencies
uv sync

# Run database migrations (creates/updates SQLite database)
uv run alembic upgrade head
```

## Run (agent path)

**Launch the server and run smoke tests:**
```bash
bash .claude/skills/run-topodata-backend/driver.sh
```

**What the driver does:**
1. Starts the FastAPI server on `http://127.0.0.1:8000`
2. Runs comprehensive smoke tests:
   - Root endpoint
   - User registration
   - User login (JWT authentication)
   - Protected endpoints (projects list)
   - Project creation
   - User info retrieval
3. Keeps the server running for manual testing
4. Stops cleanly on Ctrl+C

**Test results appear in:**
- Console output with colored ✓/✗ indicators
- Server logs: `/tmp/topodata_driver.log`

**Interactive endpoints:**
- API: `http://127.0.0.1:8000`
- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI spec: `http://127.0.0.1:8000/openapi.json`

## Run (human path)

```bash
# Start development server with auto-reload
uv run fastapi dev main.py
```

**Note:** This opens a window and waits forever. Use the driver script for headless/automated testing.

## Gotchas

**Windows console encoding issues:**
- **Problem:** `fastapi dev` may fail with `UnicodeEncodeError` on Windows due to emoji characters (🚀) in FastAPI CLI output
- **Solution:** The driver script uses `uvicorn main:app` directly with `PYTHONIOENCODING=utf-8` set
- **Workaround for manual runs:** `set PYTHONIOENCODING=utf-8` before running `fastapi dev`

**Database initialization:**
- The server auto-creates `sqlite_database/` directory on startup if missing
- Migration files in `alembic/` directory must be applied with `uv run alembic upgrade head`
- Development database: `sqlite_database/dev.db`

**Authentication required:**
- Most endpoints require JWT bearer token
- Test user created by driver: `driver_test_user` / `testpass123`
- Token obtained from `/api/v1/auth/login` (requires username + email + password)

**Port conflicts:**
- Default port: `8000`
- Change in driver: edit `SERVER_PORT` variable
- Change manually: `uvicorn main:app --port 8080`

## Troubleshooting

**Error:** `uv: command not found`
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Error:** `sqlite_database/dev.db: database is locked`
```bash
# Another process is using the database
# Check for running uvicorn processes
ps aux | grep uvicorn
# Kill the process and retry
```

**Error:** `UnicodeEncodeError: 'charmap' codec can't encode character`
```bash
# Set encoding environment variable
export PYTHONIOENCODING=utf-8
# Or use uvicorn directly instead of fastapi dev
uv run uvicorn main:app
```

**Error:** `No module named 'alembic'`
```bash
# Ensure dependencies are installed
uv sync
```

**Error:** `Target database is not up to date`
```bash
# Apply pending migrations
uv run alembic upgrade head
```

**Server starts but tests fail:**
- Check server logs: `cat /tmp/topodata_driver.log`
- Verify database exists: `ls -la sqlite_database/dev.db`
- Test manually: `curl http://127.0.0.1:8000/`

## Test

```bash
# Run pytest test suite
uv run pytest

# Run specific test file
uv run pytest tests/bessel_tests.py
```

## API Endpoints (Quick Reference)

**Authentication:**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info (requires auth)

**Projects:**
- `GET /api/v1/projects/` - List all projects (requires auth)
- `POST /api/v1/projects/` - Create new project (requires auth)
- `GET /api/v1/projects/{id}` - Get project details (requires auth)

**Import Sessions:**
- `GET /api/v1/import_sessions/` - List import sessions (requires auth)
- `POST /api/v1/projects/{project_id}/import_gka` - Import GKA file (requires auth)

**Station Setups:**
- `GET /api/v1/station_setups/` - List station setups (requires auth)
- `POST /api/v1/station_setups/` - Create station setup (requires auth)

**Observations:**
- `GET /api/v1/raw_observations/` - List raw observations (requires auth)
- `GET /api/v1/bessel_observations/` - List processed observations (requires auth)
- `GET /api/v1/reference_coordinates/` - List reference coordinates (requires auth)
- `GET /api/v1/approximate_coordinates/` - List approximate coordinates (requires auth)
