# Backend API

FastAPI service that owns authentication, image metadata, processing jobs,
experiments, comparisons and PDF reports. It never performs computer vision
itself: every image operation is delegated to the ML service over HTTP.

Run from this directory:

```bash
python -m uvicorn app.main:app --reload --port 8000
```

Apply migrations before starting in a persistent environment:

```bash
alembic upgrade head
```

Configure through environment variables or a `.env` file. See
`../.env.example` and `../docs/DEPLOYMENT.md`.
