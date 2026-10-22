# Shared API contracts

The backend and the frontend exchange JSON documents generated from Pydantic
models. This directory holds the parts of the contract that must stay stable
across services and clients.

## Error envelope

Every backend error and every ML service error uses:

```json
{
  "status": "error",
  "error": {
    "code": "machine_readable_code",
    "message": "Human readable explanation.",
    "details": {}
  }
}
```

Schema: [`error-envelope.schema.json`](error-envelope.schema.json).

Rules:

- `code` is stable and safe for programmatic branching.
- `message` may change and is shown to users.
- `details` is an object; never include secrets, stack traces or tokens.
- Successful responses use their resource schema, not this envelope.

## Pagination

List endpoints driven by `Page[T]` return:

```json
{
  "items": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 0,
    "total_pages": 0
  }
}
```

Schema: [`page.schema.json`](page.schema.json).

## Identifiers and timestamps

- IDs are 32-character lowercase hex strings.
- Timestamps are ISO 8601 with a UTC offset.
- Field names are `snake_case`.

## OpenAPI snapshots

Generate snapshots from the running code, never by hand:

```bash
cd backend
python ../scripts/export_openapi.py --app app.main:app \
  --output ../shared/api-contracts/backend.openapi.json

cd ../ml-service
python ../scripts/export_openapi.py --app app.main:app \
  --output ../shared/api-contracts/ml-service.openapi.json
```

Use each service's own virtual environment because their dependency sets
differ. Commit updated snapshots with the code change so reviewers can see
contract changes in the diff.
