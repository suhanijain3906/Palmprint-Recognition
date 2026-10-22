# Testing

## Suites

| Suite | Location | Count | What it covers |
| --- | --- | --- | --- |
| Backend | `backend/tests` | 38 | API, storage, ML delegation, reports, access control |
| ML service | `ml-service/tests` | 96 | Algorithms, metrics, validation, token auth, API contract |
| Frontend unit | `frontend/tests` | 28 | API client, services, pages, layout |
| Frontend E2E | `frontend/e2e` | 2 | Upload -> process -> enhancement, quality caveats |

Counts reflect the current repository state; add tests with every feature.

## Python

Use the project virtual environments (no global `pip` is required).

```powershell
# Backend
& backend\.venv\Scripts\python.exe -m pytest -q

# ML service
& ml-service\.venv\Scripts\python.exe -m pytest -q
```

```bash
cd backend && python -m pytest -q
cd ml-service && python -m pytest -q
```

The tests generate **synthetic** palm-like images locally. No real biometric
data is downloaded or required.

## Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

## End-to-end

Playwright starts the real ML service, backend and Vite dev server.

```powershell
cd frontend
$env:PYTHON_BACKEND = "..\backend\.venv\Scripts\python.exe"
$env:PYTHON_ML = "..\ml-service\.venv\Scripts\python.exe"
npx playwright install chromium
npm run test:e2e
```

```bash
cd frontend
PYTHON=python npx playwright install --with-deps chromium
PYTHON=python npm run test:e2e
```

If `PYTHON_BACKEND` and `PYTHON_ML` are not set, both services use the
`PYTHON` interpreter (or `python` on PATH). That interpreter must have both
sets of dependencies installed, which is how CI runs it.

The E2E run creates `backend/data/e2e.db` and `backend/data/e2e-storage`.
Both are gitignored and safe to delete.

## Smoke test

The smoke test exercises the deployed HTTP contract exactly like the
frontend, including PDF generation and download.

```bash
# With backend on :8000 and ML on :8001
python scripts/smoke_test.py

# Require ROI extraction to succeed (stricter)
python scripts/smoke_test.py --require-roi
```

Expected output ends with `16/16 checks passed` for the default suite.

## Synthetic fixtures

```bash
python scripts/generate_sample_data.py --count 4
python scripts/generate_sample_data.py --count 1 --e2e-fixture
```

These are procedural textures, not biometric samples, and are safe to
redistribute.

## Environment pre-flight

```bash
python scripts/check_environment.py
python scripts/check_environment.py --strict   # Docker required
```

## Linting and formatting

```powershell
& backend\.venv\Scripts\ruff.exe check backend ml-service scripts
& backend\.venv\Scripts\ruff.exe format --check backend ml-service scripts
```

```bash
ruff check backend ml-service scripts
ruff format --check backend ml-service scripts
```

The project uses Ruff 0.17.1 (already installed in the backend virtual
environment on Windows). Configuration lives in `backend/pyproject.toml` and
`ml-service/pyproject.toml`.

## Continuous integration

`.github/workflows/ci.yml` runs five jobs on Python 3.12 / Node 20:

1. Python lint and formatting (Ruff).
2. Backend pytest.
3. ML service pytest.
4. Frontend lint, typecheck, build and unit tests.
5. Playwright E2E with the three real services.

The E2E job installs both Python requirement sets into one environment so the
shared `PYTHON` variable works.
