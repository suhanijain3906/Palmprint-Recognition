# Architecture

## Goals

The platform supports reproducible palmprint research workflows:

1. Store an uploaded image without altering the original.
2. Run documented, deterministic processing algorithms.
3. Record every operation as a job with its parameters and measured output.
4. Compare images and evaluate scores with transparent metrics.
5. Export a PDF report that states exactly what was measured.

It deliberately does not claim identity verification accuracy. No trained
recognition model is bundled, and every similarity score is labelled as an
uncalibrated index rather than a probability.

## Services

```
Browser
  |
  |  HTTP / JSON, multipart uploads
  v
frontend (React + TypeScript + Vite)
  |
  |  /api/v1/*  (same origin in production, Vite proxy in development)
  v
backend (FastAPI, SQLAlchemy, Alembic)
  |        \
  |         \  metadata-only database (SQLite dev / PostgreSQL prod)
  |          \
  |           \  object storage (local filesystem or S3-compatible)
  |
  |  internal HTTP + multipart, optional X-Service-Token
  v
ml-service (FastAPI, OpenCV, scikit-image, NumPy)
  |
  \  artifact files (ROI crops, enhanced images, landmark overlays)
```

### Frontend

- React 18, TypeScript, React Router, TanStack Query, Tailwind CSS.
- Talks only to the backend. It never knows the ML service URL.
- Uses one API client with a normalized error shape and typed response models.
- Pages: dashboard, upload, processing, quality, landmarks, recognition,
  comparison, experiments, datasets, reports, about.

### Backend

- Validates uploads against their actual content (magic bytes and decoder),
  computes SHA-256, stores the original through a storage adapter.
- Persists image metadata, jobs, experiments, experiment results and reports.
- Delegates all processing to the ML service and maps upstream failures to
  `502`, `503` or `504` with a stable error envelope.
- Generates PDF reports locally with ReportLab from persisted job data only.
- Supports demo mode (no login) and JWT authentication.

### ML service

- Stateless with respect to the database. Only the backend calls it.
- Owns all computer vision logic and writes generated artifacts to disk.
- Exposes a machine-readable algorithm catalogue at `/api/v1/algorithms`.
- Keeps the original image untouched; every output is a separate artifact.

## Request flow: ROI extraction

1. Browser posts `image_id` and parameters to `POST /api/v1/processing/roi`.
2. Backend loads image metadata and the original bytes from storage.
3. Backend forwards the bytes to `POST /api/v1/roi/extract` on the ML service.
4. ML decodes, validates, runs the selected algorithm and writes the crop as
   an artifact.
5. Backend downloads the artifact by ID, stores it in its own storage and
   creates a `ProcessingJob` row with parameters, metrics and warnings.
6. Browser receives the normalized result plus a backend download URL.

The two-step artifact transfer keeps the ML service storage-agnostic: it does
not need credentials for the backend's S3 bucket.

## Failure handling

- ML timeout: backend returns `504 upstream_timeout`.
- ML unreachable: `503 ml_service_unavailable`.
- ML returns an algorithm error: `422` or `502` with the upstream code.
- Database or storage problems: `500 internal_error` with a generic message;
  details stay in server logs.
- Uploads are limited by size and pixel count before decoding.

## Design decisions

- **Separate ML service.** Enables independent scaling and keeps heavy
  CV dependencies out of the API image.
- **Metadata-only database.** Binary data lives in object storage; the
  database is cheap to back up and query.
- **Job records for everything.** Reproducibility and auditability matter
  more than saving a few rows.
- **Deterministic classical algorithms.** There is no hidden model and no
  invented accuracy number. A trained model can be added through an explicit
  loader contract, but it is not present by default.
- **Storage adapter interface.** Local filesystem for development,
  S3-compatible storage for production, selected by configuration.

## Non-goals

- Liveness or presentation-attack detection.
- Forensic identification or law-enforcement use.
- Medical diagnosis.
- Benchmarks against restricted datasets that cannot be redistributed.

See `SECURITY.md` for the threat model and `ML_PIPELINE.md` for algorithm
details and limitations.
