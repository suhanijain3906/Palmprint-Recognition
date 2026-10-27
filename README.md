# Palmprint Research Platform

An open, self-hosted platform for reproducible palmprint image processing and
biometric research. It ships with transparent classical computer-vision
pipelines, a metadata-only database, auditable job records and PDF reports.

**Scientific scope:** this repository contains **no trained recognition model**
and bundles **no biometric dataset**. Similarity scores are explicitly labelled
as uncalibrated indices, not probabilities or identity decisions. Accuracy,
EER or identification claims are never fabricated.

## Features

- Upload with content-based validation, SHA-256 checksums and duplicate-safe
  storage.
- ROI proposal, CLAHE / histogram equalisation / filtering enhancement.
- Quality assessment with measured indicators and explicit caveats.
- ORB and AKAZE feature extraction, landmark overlays and feature matching.
- PSNR / SSIM comparison and biometric metric evaluation (ROC, AUC, FAR, FRR,
  EER).
- Reproducible experiments with stored parameters, results and durations.
- PDF reports generated entirely from persisted measurements.
- Demo mode or JWT authentication with an HttpOnly browser session cookie.
- Local filesystem or S3-compatible storage.
- Separate ML service with an optional shared service token.

## Architecture

```
React SPA  ->  FastAPI backend  ->  ML service (OpenCV)
                   |     |
                   |     +--> PostgreSQL / SQLite (metadata only)
                   +--------> local storage or S3 (images, artifacts, PDFs)
```

The browser talks only to the backend. The backend is the only client of the
ML service. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Quick start

### Option A: three local processes

```powershell
# Terminal 1
cd ml-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

```powershell
# Terminal 2
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
$env:AUTO_CREATE_SCHEMA = "true"
python -m uvicorn app.main:app --reload --port 8000
```

```powershell
# Terminal 3
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

On macOS/Linux replace the activation command with
`source .venv/bin/activate` and prefix the backend command with
`AUTO_CREATE_SCHEMA=true`.

Generate a safe synthetic sample:

```bash
python scripts/generate_sample_data.py --count 4
```

### Option B: Docker development stack

```bash
docker compose up --build
```

Frontend `http://localhost:3000`, backend `http://localhost:8000`,
ML service `http://localhost:8001`. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Tests

| Suite | Command | Status |
| --- | --- | --- |
| Backend | `cd backend && python -m pytest -q` | 38 tests |
| ML service | `cd ml-service && python -m pytest -q` | 96 tests |
| Frontend unit | `cd frontend && npm test` | 28 tests |
| Frontend lint/typecheck/build | `npm run lint && npm run typecheck && npm run build` | clean |
| E2E | `cd frontend && npm run test:e2e` | 2 tests |
| HTTP smoke | `python scripts/smoke_test.py` | 16 checks |

Playwright needs the service interpreters:

```powershell
cd frontend
$env:PYTHON_BACKEND = "..\backend\.venv\Scripts\python.exe"
$env:PYTHON_ML = "..\ml-service\.venv\Scripts\python.exe"
npx playwright install chromium
npm run test:e2e
```

Full testing instructions: [docs/TESTING.md](docs/TESTING.md).

## Operational scripts

| Script | Purpose |
| --- | --- |
| `scripts/generate_sample_data.py` | Deterministic synthetic PNG samples |
| `scripts/check_environment.py` | Toolchain and dependency pre-flight |
| `scripts/smoke_test.py` | End-to-end HTTP verification including PDF |
| `scripts/export_openapi.py` | Write an OpenAPI snapshot |

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [API reference](docs/API.md)
- [Database schema](docs/DATABASE.md)
- [ML pipeline and limitations](docs/ML_PIPELINE.md)
- [Testing](docs/TESTING.md)
- [Security and biometric ethics](docs/SECURITY.md)
- [Deployment](docs/DEPLOYMENT.md)
- [Shared contracts](shared/api-contracts/README.md)

## Configuration

Copy `.env.example` to `.env` and review every value. The most important
production settings are `SECRET_KEY`, `POSTGRES_PASSWORD`,
`ML_SERVICE_API_KEY`, `ALLOWED_ORIGINS`, `AUTH_ENABLED` and
`ALLOW_REGISTRATION`.

Never run demo mode (`AUTH_ENABLED=false`) on the public internet: all
visitors share one account.

The backend applies Alembic migrations automatically at startup
(`AUTO_MIGRATE=true`). On Render it also falls back to the deployed ML URL when
`ML_SERVICE_URL` is not set. The provided deployment is described by
[`render.yaml`](render.yaml):

- Backend: <https://palmprint-recognition.onrender.com>
- ML service: <https://palmprint-recognition-1.onrender.com>
- Smoke test: `python scripts/smoke_test.py --backend https://palmprint-recognition.onrender.com --ml https://palmprint-recognition-1.onrender.com`

## Project layout

```
backend/      FastAPI API, SQLAlchemy models, Alembic migrations, PDF reports
ml-service/   FastAPI computer-vision service and algorithm catalogue
frontend/     React + TypeScript SPA, unit tests and Playwright E2E
docs/         Architecture, API, database, ML, testing, security, deployment
shared/       Error-envelope and pagination contracts
scripts/      Fixtures, environment checks, smoke test, OpenAPI export
```

## Known limitations

- No trained identity model, no liveness detection, no forensic use.
- ROI is a contour-based region proposal, not anatomical segmentation.
- Quality and similarity scores are unvalidated heuristics.
- Docker configuration is reviewed but was not executed in the development
  environment because Docker was unavailable there.
- No built-in rate limiting; use a reverse or identity-aware proxy.

## License

MIT. See [LICENSE](LICENSE).
