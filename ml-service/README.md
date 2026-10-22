# ML / Computer Vision Service

FastAPI service that performs all image processing with classical OpenCV and
scikit-image algorithms: validation, ROI proposal, enhancement, quality
assessment, ORB/AKAZE feature extraction, landmark visualisation, similarity
comparison and biometric metric evaluation.

It is an internal service. In production it should be reachable only by the
backend and protected with `ML_SERVICE_API_KEY`.

Run from this directory:

```bash
python -m uvicorn app.main:app --reload --port 8001
```

There is no trained identity model in this repository. The `/health`
endpoint reports `trained_model_available: false` unless an operator installs
a compatible model. See `../docs/ML_PIPELINE.md`.
