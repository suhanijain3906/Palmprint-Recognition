# API Reference

Interactive documentation is served by the running backend:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`
- ReDoc: `http://localhost:8000/redoc`

The ML service exposes its own docs at `http://localhost:8001/docs`.

## Conventions

- Public backend prefix: `/api/v1` (except `/health` and `/ready`).
- Internal ML prefix: `/api/v1` (except `/health`).
- JSON field names use `snake_case`.
- Timestamps are ISO 8601 UTC.
- IDs are 32-character random hex strings.
- Pagination uses `page` (1-based) and `page_size` (1-100); responses contain
  `items` and `meta` (`page`, `page_size`, `total`, `total_pages`).

### Error envelope

Every backend error has the same shape:

```json
{
  "error": {
    "code": "validation_error",
    "message": "The request could not be processed.",
    "details": {"field": "reason"}
  }
}
```

| HTTP | Typical code | Meaning |
| --- | --- | --- |
| 400 | `invalid_request`, `empty_upload` | Malformed request or empty file |
| 401 | `unauthorized`, `invalid_credentials` | Missing or invalid credentials |
| 403 | `forbidden` | Authenticated but not allowed |
| 404 | `not_found` | Unknown image, experiment or report |
| 409 | `conflict` | Duplicate or incompatible state |
| 413 | `file_too_large` | Upload exceeds the configured limit |
| 415 | `unsupported_media_type` | Content is not a supported image |
| 422 | `validation_error`, `algorithm_error` | Invalid parameters or algorithm failure |
| 502 | `ml_service_error` | ML service returned an invalid response |
| 503 | `ml_service_unavailable` | ML service is not reachable |
| 504 | `upstream_timeout` | ML service exceeded the timeout |

## Authentication

Mode is reported by `GET /api/v1/auth/mode`.

- `AUTH_ENABLED=false`: every request is attributed to the shared demo
  account. All objects are still scoped to that owner.
- `AUTH_ENABLED=true`: log in with `POST /api/v1/auth/login` (JSON `email`,
  `password`). The response contains a bearer token for API clients and the
  backend also sets an HttpOnly `access_token` cookie for the browser.
  Send `Authorization: Bearer <token>` from non-browser clients.
- `POST /api/v1/auth/logout` clears the cookie.
- `POST /api/v1/auth/register` is available while
  `ALLOW_REGISTRATION=true`.
- `GET /api/v1/auth/me` returns the current account.

## Images

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/images` | List images (paginated, optional `include_deleted`) |
| POST | `/api/v1/images/upload` | Upload an image (multipart `file`, optional metadata) |
| GET | `/api/v1/images/{id}` | Image metadata |
| GET | `/api/v1/images/{id}/file` | Download the stored original |
| GET | `/api/v1/images/{id}/jobs` | Processing history for an image |
| PATCH | `/api/v1/images/{id}` | Update label, subject ID or notes |
| DELETE | `/api/v1/images/{id}` | Soft-delete metadata and remove the stored file |

Upload limits default to 12 MB and 40 megapixels. Decoding, not the file
extension or the client-provided MIME type, determines acceptance.

## Processing

All processing endpoints accept JSON with `image_id` and `parameters`.

| Method | Path | Operation |
| --- | --- | --- |
| POST | `/api/v1/processing/roi` | `classical_contour_roi` region proposal |
| POST | `/api/v1/processing/enhancement` | `clahe`, `histogram_equalization`, `filtering` |
| POST | `/api/v1/processing/quality` | Brightness, contrast, sharpness report |
| POST | `/api/v1/processing/features` | ORB or AKAZE keypoints and descriptors |
| POST | `/api/v1/processing/landmarks` | Landmark overlay and keypoint list |

Each response includes the job ID, algorithm name and version, parameters,
metrics, warnings, duration and artifact download URLs.

## Recognition and comparison

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/recognition/compare` | Classical feature matching between two images |
| POST | `/api/v1/comparison` | PSNR, SSIM and difference statistics |

Recognition returns an **uncalibrated similarity index**. It is not a
probability, is not threshold-calibrated, and must not be presented as a
verification decision.

Example:

```bash
curl -X POST http://localhost:8000/api/v1/recognition/compare \
  -H "Content-Type: application/json" \
  -d '{"image_a_id":"<id>","image_b_id":"<id>","parameters":{"detector":"orb"}}'
```

## Experiments

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/v1/experiments` | Run an experiment over one or more images |
| GET | `/api/v1/experiments` | List experiments |
| GET | `/api/v1/experiments/{id}` | Experiment with results |
| GET | `/api/v1/experiments/{id}/summary` | Aggregated result summary |

Supported operations mirror the processing endpoints. Every run stores its
parameters, measured results, duration and status.

## Datasets

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/datasets` | Catalogue of known public palmprint benchmarks |
| GET | `/api/v1/datasets/{id}` | Benchmark metadata and citation notes |

The catalogue is descriptive. The platform does not download restricted
datasets automatically and does not bundle biometric data.

## Reports

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/api/v1/reports` | List generated reports |
| POST | `/api/v1/reports` | Generate a PDF for an experiment or job |
| GET | `/api/v1/reports/{id}` | Report metadata |
| GET | `/api/v1/reports/{id}/download` | Download the PDF |

## Health

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Backend, database, storage and ML status |
| GET | `/ready` | Readiness probe |

## Internal ML endpoints

The backend sends `X-Service-Token` when `ML_SERVICE_API_KEY` is configured.
The token is not a user credential and must never reach the browser.

| Method | Path |
| --- | --- |
| POST | `/api/v1/validate` |
| POST | `/api/v1/roi/extract` |
| POST | `/api/v1/enhancement/apply` |
| POST | `/api/v1/quality/analyze` |
| POST | `/api/v1/features/extract` |
| POST | `/api/v1/recognition/compare` |
| POST | `/api/v1/landmarks/visualize` |
| POST | `/api/v1/images/compare` |
| POST | `/api/v1/evaluation/run` |
| GET | `/api/v1/algorithms` |
| GET | `/api/v1/artifacts/{artifact_id}` |

Generate an OpenAPI snapshot:

```bash
cd backend
python ../scripts/export_openapi.py --app app.main:app --output ../shared/api-contracts/backend.openapi.json
cd ../ml-service
python ../scripts/export_openapi.py --app app.main:app --output ../shared/api-contracts/ml-service.openapi.json
```
