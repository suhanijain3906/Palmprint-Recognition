# Deployment

## Prerequisites

- Python 3.11+ (3.12 recommended; the images use 3.12).
- Node.js 20+ and npm.
- Docker Engine 24+ with Compose v2 for container deployment.
- PostgreSQL 16 for production (the compose file provides it).
- Optional: S3-compatible object storage for images and artifacts.

## Local development without Docker

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt -r requirements-dev.txt
$env:AUTO_CREATE_SCHEMA = "true"   # or run: alembic upgrade head
python -m uvicorn app.main:app --reload --port 8000
```

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
AUTO_CREATE_SCHEMA=true python -m uvicorn app.main:app --reload --port 8000
```

### ML service

```powershell
cd ml-service
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8001
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/api` to `http://localhost:8000`.

### Verify

```bash
python scripts/check_environment.py
python scripts/smoke_test.py
```

## Docker: development stack

```bash
docker compose up --build
```

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000` (bound to localhost)
- ML service: `http://localhost:8001` (bound to localhost)
- PostgreSQL: `localhost:5432` (bound to localhost)

The backend runs `alembic upgrade head` before starting. Demo mode is enabled
and the database password is a development value only.

## Docker: production stack

### 1. Create the environment file

```bash
cp .env.example .env
```

Set at minimum:

```dotenv
POSTGRES_DB=palmprint
POSTGRES_USER=palmprint
POSTGRES_PASSWORD=<random>
SECRET_KEY=<random>
ML_SERVICE_API_KEY=<random>
ALLOWED_ORIGINS=https://palm.example.org
AUTH_ENABLED=true
ALLOW_REGISTRATION=true
DEMO_MODE=false
```

Generate random values:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### 2. Start

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

### 3. Provision accounts

1. Browse to the deployment and register the first researcher account.
2. Set `ALLOW_REGISTRATION=false` in `.env`.
3. Restart the backend:

```bash
docker compose -f docker-compose.prod.yml up -d --force-recreate backend
```

### 4. TLS and access control

The frontend container serves plain HTTP on port 80. Place it behind a
reverse proxy or identity-aware proxy that:

- terminates TLS with a valid certificate;
- forwards to `http://<host>:80`;
- sets `X-Forwarded-Proto` and `X-Forwarded-For`;
- optionally enforces SSO or IP allowlists;
- provides rate limiting.

Example nginx location:

```nginx
location / {
    proxy_pass http://127.0.0.1:80;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    client_max_body_size 12m;
}
```

Set `ALLOWED_ORIGINS` to the public HTTPS origin.

## Render (managed deployment)

The repository ships a [`render.yaml`](../render.yaml) blueprint with three
services:

| Service | URL |
| --- | --- |
| Backend API | `https://palmprint-recognition.onrender.com` |
| ML service | `https://palmprint-recognition-1.onrender.com` |
| Frontend | created by the blueprint as `palmprint-frontend` |

The blueprint sets `ML_SERVICE_URL` for the backend, builds the frontend with
`VITE_API_BASE_URL=https://palmprint-recognition.onrender.com/api/v1` and uses
the SPA rewrite `/* -> /index.html`.

The backend applies its Alembic migrations at startup (`AUTO_MIGRATE=true`).
If the database is empty it creates the schema directly, so an existing service
that only runs `uvicorn app.main:app` becomes usable again after the next
deploy. When upgrading an existing Render service, confirm these variables in
the dashboard:

```dotenv
ML_SERVICE_URL=https://palmprint-recognition-1.onrender.com
ML_SERVICE_TIMEOUT=120.0
ALLOWED_ORIGINS=*
ALLOW_CREDENTIALS=true
AUTO_MIGRATE=true
```

`ALLOWED_ORIGINS=*` is honoured only while `AUTH_ENABLED=false`. Once accounts
are enabled, list the exact frontend origins instead.

Render's free filesystem is ephemeral. SQLite and local storage are reset on
redeploy/restart. Use managed PostgreSQL (`DATABASE_URL`) and S3-compatible
storage (`STORAGE_BACKEND=s3`) for durable data.

Verify a deployment with:

```bash
python scripts/smoke_test.py \
  --backend https://palmprint-recognition.onrender.com \
  --ml https://palmprint-recognition-1.onrender.com
```

## Configuration reference

| Variable | Default | Notes |
| --- | --- | --- |
| `ENVIRONMENT` | `development` | `production` enables strict checks |
| `DATABASE_URL` | SQLite file | `postgres://`/`postgresql://` are normalised to `psycopg` |
| `AUTO_MIGRATE` | `true` | Apply Alembic migrations at startup |
| `AUTO_CREATE_SCHEMA` | `false` | Tests/demos only |
| `SECRET_KEY` | insecure default | Required in production |
| `AUTH_ENABLED` | `false` | `true` for accounts |
| `ALLOW_REGISTRATION` | `true` | Disable after provisioning |
| `DEMO_MODE` | `true` | Shared account when auth is off |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `720` | JWT lifetime |
| `ALLOWED_ORIGINS` | `*` | `*`, comma separated or JSON array; `*` only without auth |
| `STORAGE_BACKEND` | `local` | `local` or `s3` |
| `STORAGE_ROOT` | `./data/storage` | Local storage path |
| `S3_*` | empty | Bucket, endpoint, region, keys, path style |
| `MAX_UPLOAD_BYTES` | `12582912` | 12 MiB |
| `MAX_IMAGE_PIXELS` | `40000000` | Decoding limit |
| `RETENTION_DAYS` | `30` | Cleanup policy input |
| `ML_SERVICE_URL` | `http://localhost:8001` | Render falls back to the deployed ML URL |
| `ML_SERVICE_TIMEOUT` | `120.0` | Seconds |
| `ML_SERVICE_API_KEY` | empty | Shared service token |
| `ML_ARTIFACT_DIR` | `./data/artifacts` | ML artifact path |
| `ML_ARTIFACT_RETENTION_HOURS` | `24` | ML artifact expiry |
| `ML_MODEL_DIR` | `./models` | Trained weight directory |
| `VITE_API_BASE_URL` | `/api/v1` | Frontend build-time |

## Migrations

The container command is:

```sh
alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000
```

For a manual migration:

```bash
docker compose -f docker-compose.prod.yml run --rm backend alembic upgrade head
docker compose -f docker-compose.prod.yml run --rm backend alembic current
```

Take a database backup before upgrading.

## Health checks and monitoring

- `GET /health` (backend): database, storage and ML status.
- `GET /ready` (backend): database readiness.
- `GET /health` (ML): uptime, algorithm catalogue, trained-model status.
- `GET /health` (frontend): nginx serves the SPA.

Monitor at least:

- HTTP 5xx rate and latency.
- ML timeout and unavailable counts (`502`/`503`/`504`).
- Disk usage for storage and database growth.
- Container restart counts.
- Failed login attempts at the proxy layer.

## Scaling

- The backend is stateless apart from storage and the database. Run multiple
  replicas behind the proxy.
- The ML service is CPU-bound. Scale it horizontally and increase worker
  count according to CPU and memory.
- Use shared object storage (S3) when running more than one backend replica.
- PostgreSQL: use managed backups, connection pooling and monitoring.
- Set `ML_SERVICE_TIMEOUT` above the p99 processing time of the largest
  expected image.

## Backups and restore

```bash
docker compose -f docker-compose.prod.yml exec postgres \
  pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > backup.sql
```

Restore into a new database, then start the backend and verify `/health` and
a sample upload. Back up the storage bucket or volume in the same window.

## Upgrade and rollback

```bash
git fetch --tags
git checkout <tag>
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

Rollback:

```bash
git checkout <previous-tag>
docker compose -f docker-compose.prod.yml up -d --build
```

If a migration is not backward compatible, restore the database backup
instead of downgrading blindly.

## Verification checklist

After deployment:

1. `docker compose -f docker-compose.prod.yml exec backend curl -fsS http://localhost:8000/health`
   returns `{"status":"ok"}`.
2. The frontend loads and the demo/auth mode is correct.
3. Log in (authenticated mode) or confirm the demo banner.
4. Upload a synthetic sample.
5. Run ROI, CLAHE, quality and feature extraction.
6. Generate and download a PDF report.
7. Confirm the ML port and database are not reachable from the internet.
8. Confirm uploaded files survive a backend restart (storage volume/S3).
9. Check logs for secret leakage.

## Troubleshooting

| Symptom | Likely cause |
| --- | --- |
| `503 ml_service_unavailable` | Wrong `ML_SERVICE_URL` or ML container down |
| `504 upstream_timeout` | Large image or slow algorithm; raise timeout |
| `401` on every API call | Auth enabled but no session; log in again |
| Login works, images fail | Reverse proxy strips the `access_token` cookie |
| `413` on upload | nginx `client_max_body_size` or backend limit |
| Reports fail | Storage permissions or missing ReportLab dependency |
| Migration errors | Schema drift; restore backup and re-run migrations |
| ML 401 | `ML_SERVICE_API_KEY` differs between backend and ML service |

## Verification status of this repository

The following were executed successfully during development on Windows 11
with Python 3.14 and Node 24:

- Backend pytest suite.
- ML service pytest suite.
- Frontend lint, typecheck, unit tests and production build.
- Playwright E2E against the three real services.
- HTTP smoke test (16/16 checks) including PDF generation and download.

Docker images and Compose were **not** built or started because the Docker
daemon was unavailable in that environment. Treat the Dockerfiles and compose
files as reviewed but unexecuted until you run the build on your host.
