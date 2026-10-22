"""Processing endpoints of the ML service.

Every endpoint accepts ``multipart/form-data`` uploads.  Output images are
returned as *artifact references* rather than inline base64 payloads; the
backend downloads them through :func:`get_artifact` and re-hosts them.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from ..config import settings
from ..features.feature_matching import draw_matches
from ..landmarks.detector import detect_feature_points, landmark_model_status
from ..landmarks.visualization import draw_landmarks
from ..pipelines.comparison_pipeline import compare_images
from ..pipelines.enhancement_pipeline import apply_enhancement
from ..pipelines.feature_pipeline import extract as extract_features_pipeline
from ..pipelines.quality_pipeline import analyze_quality
from ..pipelines.roi_pipeline import extract_roi
from ..recognition.classical_matcher import ClassicalMatcher
from ..recognition.model_loader import discover_models
from ..utils.artifacts import ArtifactStore
from ..utils.errors import MLServiceError
from ..utils.image_io import encode_png, to_bgr
from ..utils.validation import validate_payload
from .schemas import (
    AlgorithmInfo,
    ArtifactRef,
    ComparisonResultResponse,
    EnhancementResultResponse,
    EvaluationRequest,
    EvaluationResultResponse,
    FeatureResultResponse,
    LandmarkResultResponse,
    QualityResultResponse,
    RecognitionResultResponse,
    ROIResultResponse,
    ValidationResult,
)

router = APIRouter(tags=["processing"])

artifact_store = ArtifactStore(
    settings.artifact_dir,
    retention_hours=settings.artifact_retention_hours,
    max_bytes=settings.artifact_max_bytes,
)


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
async def _read_upload(upload: UploadFile) -> bytes:
    data = await upload.read()
    if not data:
        raise MLServiceError(
            f"The uploaded file '{upload.filename or 'unnamed'}' is empty.",
            code="empty_upload",
            status_code=400,
        )
    return data


def _decode(upload: UploadFile, data: bytes) -> tuple[np.ndarray, dict[str, Any]]:
    decoded, report = validate_payload(
        data,
        filename=upload.filename,
        declared_content_type=upload.content_type,
        max_bytes=settings.max_upload_bytes,
        max_pixels=settings.max_pixels,
        max_dimension=settings.max_dimension,
    )
    return decoded.image, report.to_dict()


def _artifact(data: bytes, kind: str) -> ArtifactRef:
    stored = artifact_store.put(data, media_type="image/png", kind=kind)
    return ArtifactRef(
        id=stored.artifact_id,
        kind=kind,
        media_type=stored.media_type,
        size_bytes=stored.size_bytes,
        download_path=f"{settings.api_prefix}/artifacts/{stored.artifact_id}",
    )


def _int_form(value: str | None, default: int, *, minimum: int, maximum: int) -> int:
    if value is None or value == "":
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise MLServiceError(
            f"'{value}' is not a valid integer.", code="invalid_parameter", status_code=422
        ) from exc
    if not minimum <= parsed <= maximum:
        raise MLServiceError(
            f"The value {parsed} is outside the allowed range [{minimum}, {maximum}].",
            code="invalid_parameter",
            status_code=422,
        )
    return parsed


def _float_form(value: str | None, default: float, *, minimum: float, maximum: float) -> float:
    if value is None or value == "":
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise MLServiceError(
            f"'{value}' is not a valid number.", code="invalid_parameter", status_code=422
        ) from exc
    if not minimum <= parsed <= maximum:
        raise MLServiceError(
            f"The value {parsed} is outside the allowed range [{minimum}, {maximum}].",
            code="invalid_parameter",
            status_code=422,
        )
    return parsed


# --------------------------------------------------------------------------
# endpoints
# --------------------------------------------------------------------------
@router.post("/validate", response_model=ValidationResult, summary="Validate an uploaded image")
async def validate_image(file: UploadFile = File(...)) -> ValidationResult:
    """Decode the upload and report what was actually detected."""
    started = time.perf_counter()
    data = await _read_upload(file)
    image, report = _decode(file, data)

    return ValidationResult(
        algorithm=AlgorithmInfo(
            name="image_validation",
            version="1.0.0",
            description="Magic byte sniffing, dual decoding and dimensional checks.",
        ),
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
        metrics={
            "width": int(image.shape[1]),
            "height": int(image.shape[0]),
            "size_bytes": len(data),
        },
        validation=report,
        warnings=list(report.get("warnings", [])),
        limitations=[
            "Validation confirms that the payload is a decodable raster image; "
            "it cannot confirm that the image actually depicts a palm.",
        ],
    )


@router.post(
    "/roi/extract", response_model=ROIResultResponse, summary="Extract a region of interest"
)
async def extract_roi_endpoint(
    file: UploadFile = File(...),
    algorithm: str = Form("classical_contour_roi"),
    median_ksize: str | None = Form(None),
    morph_kernel: str | None = Form(None),
) -> ROIResultResponse:
    """Run the ROI extraction pipeline and return the cropped region."""
    started = time.perf_counter()
    data = await _read_upload(file)
    image, report = _decode(file, data)

    parameters: dict[str, Any] = {}
    if median_ksize not in (None, ""):
        parameters["median_ksize"] = _int_form(median_ksize, 5, minimum=3, maximum=31)
    if morph_kernel not in (None, ""):
        parameters["morph_kernel"] = _int_form(morph_kernel, 7, minimum=3, maximum=31)

    result = extract_roi(image, algorithm=algorithm, parameters=parameters)
    artifact = _artifact(encode_png(to_bgr(result.image)), "roi")

    return ROIResultResponse(
        algorithm=AlgorithmInfo(
            name=result.method,
            version=str(result.metrics.get("algorithm_version", "1.0.0")),
            anatomical=False,
            description=(
                "Approximate palm-region proposal based on contour segmentation. "
                "This is not an anatomical palm detector."
            ),
        ),
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
        metrics=dict(result.metrics),
        artifacts=[artifact],
        warnings=list(report.get("warnings", [])) + list(result.warnings),
        limitations=[
            "The extracted region is an approximate proposal, not an anatomically "
            "validated palm ROI.",
            "No trained palm detector is bundled with this deployment.",
        ],
        roi={
            "bbox": {
                "x": result.x,
                "y": result.y,
                "width": result.width,
                "height": result.height,
            },
            "confidence": result.confidence,
            "is_approximate": result.is_approximate,
            "method": result.method,
        },
    )


@router.post(
    "/enhancement/apply",
    response_model=EnhancementResultResponse,
    summary="Apply an enhancement algorithm",
)
async def apply_enhancement_endpoint(
    file: UploadFile = File(...),
    algorithm: str = Form("clahe"),
    clip_limit: str | None = Form(None),
    tile_grid_size: str | None = Form(None),
    filter: str | None = Form(None),
    kernel_size: str | None = Form(None),
    sigma: str | None = Form(None),
    amount: str | None = Form(None),
    radius: str | None = Form(None),
    color_space: str | None = Form(None),
) -> EnhancementResultResponse:
    """Enhance an image.  The original is never modified."""
    started = time.perf_counter()
    data = await _read_upload(file)
    image, report = _decode(file, data)

    parameters: dict[str, Any] = {}
    if clip_limit not in (None, ""):
        parameters["clip_limit"] = _float_form(clip_limit, 2.0, minimum=0.1, maximum=40.0)
    if tile_grid_size not in (None, ""):
        parameters["tile_grid_size"] = _int_form(tile_grid_size, 8, minimum=1, maximum=32)
    if filter not in (None, ""):
        parameters["filter"] = filter
    if kernel_size not in (None, ""):
        parameters["kernel_size"] = _int_form(kernel_size, 5, minimum=3, maximum=31)
    if sigma not in (None, ""):
        parameters["sigma"] = _float_form(sigma, 0.0, minimum=0.0, maximum=10.0)
    if amount not in (None, ""):
        parameters["amount"] = _float_form(amount, 1.0, minimum=0.0, maximum=5.0)
    if radius not in (None, ""):
        parameters["radius"] = _int_form(radius, 3, minimum=1, maximum=15)
    if color_space not in (None, ""):
        parameters["color_space"] = color_space

    result = apply_enhancement(image, algorithm=algorithm, parameters=parameters)
    artifact = _artifact(encode_png(to_bgr(result.image)), "enhanced")

    return EnhancementResultResponse(
        algorithm=AlgorithmInfo(
            name=result.algorithm,
            version=result.version,
            anatomical=False,
            description=f"Enhancement algorithm '{result.algorithm}'.",
        ),
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
        metrics=result.metadata(),
        artifacts=[artifact],
        warnings=list(report.get("warnings", [])) + list(result.warnings),
        limitations=list(result.limitations),
        enhancement=result.metadata(),
    )


@router.post(
    "/quality/analyze", response_model=QualityResultResponse, summary="Assess image quality"
)
async def analyze_quality_endpoint(file: UploadFile = File(...)) -> QualityResultResponse:
    """Compute brightness, contrast, sharpness and the experimental combined score."""
    started = time.perf_counter()
    data = await _read_upload(file)
    image, report = _decode(file, data)

    quality = analyze_quality(image)

    return QualityResultResponse(
        algorithm=AlgorithmInfo(
            name="quality_report",
            version="1.0.0",
            anatomical=False,
            description="Brightness, contrast, sharpness and an experimental combined score.",
        ),
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
        metrics={
            "combined_score": quality["combined_score"],
            "sub_scores": quality["sub_scores"],
        },
        warnings=list(report.get("warnings", [])) + list(quality["warnings"]),
        limitations=list(quality["limitations"]),
        quality=quality,
    )


@router.post(
    "/features/extract", response_model=FeatureResultResponse, summary="Extract image features"
)
async def extract_features_endpoint(
    file: UploadFile = File(...),
    detector: str = Form("orb"),
    n_features: str | None = Form(None),
    edge_threshold: str | None = Form(None),
) -> FeatureResultResponse:
    """Extract keypoints and descriptors with a classical detector."""
    started = time.perf_counter()
    data = await _read_upload(file)
    image, report = _decode(file, data)

    outcome = extract_features_pipeline(
        image,
        detector=detector,
        n_features=_int_form(n_features, settings.default_orb_features, minimum=16, maximum=20000),
        edge_threshold=_int_form(edge_threshold, 31, minimum=1, maximum=100),
    )

    return FeatureResultResponse(
        algorithm=AlgorithmInfo(
            name=f"{outcome.features.detector}_features",
            version="1.0.0",
            anatomical=False,
            description="Generic classical keypoint detector (not palmprint specific).",
        ),
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
        metrics=outcome.metadata(),
        warnings=list(report.get("warnings", [])) + list(outcome.features.warnings),
        limitations=[
            "Generic corner/keypoint detectors do not model the oriented line "
            "structure of palm ridges.",
            "Descriptor suitability must be established on the target dataset.",
        ],
        features=outcome.metadata(),
    )


@router.post(
    "/recognition/compare", response_model=RecognitionResultResponse, summary="Compare two images"
)
async def recognize_endpoint(
    image_a: UploadFile = File(...),
    image_b: UploadFile = File(...),
    detector: str = Form("orb"),
    lowe_ratio: str | None = Form(None),
    n_features: str | None = Form(None),
) -> RecognitionResultResponse:
    """Experimental similarity comparison of two palmprint images.

    The response states explicitly whether a trained model was used.  When no
    trained model is installed the similarity score is an uncalibrated
    heuristic index and *not* a probability of identity.
    """
    started = time.perf_counter()

    data_a = await _read_upload(image_a)
    data_b = await _read_upload(image_b)
    first, report_a = _decode(image_a, data_a)
    second, report_b = _decode(image_b, data_b)

    trained = discover_models(settings.model_dir)
    matcher = ClassicalMatcher(
        detector=detector,
        n_features=_int_form(n_features, settings.default_orb_features, minimum=16, maximum=20000),
        lowe_ratio=_float_form(lowe_ratio, settings.default_lowe_ratio, minimum=0.01, maximum=0.99),
    )
    result = matcher.compare(first, second)

    artifacts: list[ArtifactRef] = []
    if result.available and result.details.get("good_matches", 0) > 0:
        try:
            features_a = extract_features_pipeline(
                first, detector=detector, n_features=matcher.n_features
            ).features
            features_b = extract_features_pipeline(
                second, detector=detector, n_features=matcher.n_features
            ).features
            from ..features.feature_matching import match_descriptors

            matches = match_descriptors(
                features_a,
                features_b,
                lowe_ratio=matcher.lowe_ratio,
                cross_check=matcher.cross_check,
            )
            visualisation = draw_matches(
                to_bgr(first), features_a, to_bgr(second), features_b, matches
            )
            artifacts.append(_artifact(encode_png(visualisation), "feature_matches"))
        except Exception as exc:  # pragma: no cover - visualisation is best effort
            result.warnings.append(f"The match visualisation could not be rendered: {exc}")

    warnings = (
        list(report_a.get("warnings", []))
        + list(report_b.get("warnings", []))
        + list(result.warnings)
    )
    warnings.append(
        "No trained recognition model is installed in this deployment; the score "
        "is an experimental, uncalibrated similarity index."
        if not trained.available
        else "A trained model is installed; the classical matcher was used for this request."
    )

    return RecognitionResultResponse(
        algorithm=AlgorithmInfo(
            name=result.matcher_name,
            version=result.matcher_version,
            anatomical=False,
            description="Classical descriptor matching based experimental comparison.",
        ),
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
        metrics=result.details,
        artifacts=artifacts,
        warnings=warnings,
        limitations=list(result.limitations) + [trained.message],
        recognition={**result.summary(), "trained_model_available": trained.available},
    )


@router.post(
    "/landmarks/visualize",
    response_model=LandmarkResultResponse,
    summary="Visualise detected feature points",
)
async def visualize_landmarks_endpoint(
    file: UploadFile = File(...),
    detector: str = Form("orb"),
    max_points: str | None = Form(None),
) -> LandmarkResultResponse:
    """Render an overlay of the detected feature points.

    The response distinguishes generic feature points from anatomical palm
    landmarks; only the former can be produced by the bundled algorithms.
    """
    started = time.perf_counter()
    data = await _read_upload(file)
    image, report = _decode(file, data)

    status = landmark_model_status(settings.model_dir)
    landmarks = detect_feature_points(
        image,
        detector=detector,
        max_points=_int_form(max_points, 300, minimum=1, maximum=2000),
    )
    overlay = draw_landmarks(image, landmarks)
    artifact = _artifact(encode_png(to_bgr(overlay)), "landmark_overlay")

    warnings = list(report.get("warnings", [])) + list(landmarks.warnings)
    warnings.append(status["message"])

    return LandmarkResultResponse(
        algorithm=AlgorithmInfo(
            name=landmarks.method,
            version="1.0.0",
            anatomical=False,
            description=(
                "Generic classical feature points. They are NOT anatomical palm "
                "landmarks (no trained landmark model is installed)."
            ),
        ),
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
        metrics={"point_count": landmarks.count},
        artifacts=[artifact],
        warnings=warnings,
        limitations=[
            "ORB/AKAZE keypoints are generic interest points and carry no anatomical meaning.",
            "Anatomical palm landmarks require a trained landmark model that "
            "must be installed by the researcher.",
        ],
        landmarks={
            **landmarks.summary(),
            "anatomical_landmark_model": status,
        },
    )


@router.post(
    "/images/compare", response_model=ComparisonResultResponse, summary="Compare two images"
)
async def compare_images_endpoint(
    image_a: UploadFile = File(...),
    image_b: UploadFile = File(...),
) -> ComparisonResultResponse:
    """Side-by-side comparison artefacts: difference image, PSNR and SSIM."""
    started = time.perf_counter()

    data_a = await _read_upload(image_a)
    data_b = await _read_upload(image_b)
    first, report_a = _decode(image_a, data_a)
    second, report_b = _decode(image_b, data_b)

    outcome = compare_images(first, second)
    artifact = _artifact(encode_png(to_bgr(outcome.difference_image)), "difference")

    warnings = (
        list(report_a.get("warnings", []))
        + list(report_b.get("warnings", []))
        + list(outcome.warnings)
    )

    return ComparisonResultResponse(
        algorithm=AlgorithmInfo(
            name="image_difference",
            version="1.0.0",
            anatomical=False,
            description="Absolute difference image with PSNR and SSIM metrics.",
        ),
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
        metrics=outcome.metrics,
        artifacts=[artifact],
        warnings=warnings,
        limitations=list(outcome.limitations),
        comparison={
            "psnr_db": outcome.psnr,
            "ssim": outcome.ssim,
            "aligned": outcome.aligned,
            "resized": outcome.resized,
            **outcome.metrics,
        },
    )


@router.post(
    "/evaluation/run", response_model=EvaluationResultResponse, summary="Run a biometric evaluation"
)
async def run_evaluation(request: EvaluationRequest) -> EvaluationResultResponse:
    """Compute ROC/AUC/FAR/FRR/EER from labelled comparison scores."""
    started = time.perf_counter()

    if len(request.scores) != len(request.labels):
        raise MLServiceError(
            "scores and labels must have the same length.",
            code="invalid_evaluation_request",
            status_code=422,
            details={"scores": len(request.scores), "labels": len(request.labels)},
        )

    from ..evaluation.metrics import evaluate_scores

    try:
        result = evaluate_scores(request.scores, request.labels, thresholds=request.thresholds)
    except ValueError as exc:
        raise MLServiceError(str(exc), code="invalid_evaluation_request", status_code=422) from exc

    return EvaluationResultResponse(
        algorithm=AlgorithmInfo(
            name="biometric_evaluation",
            version="1.0.0",
            anatomical=False,
            description="ROC/AUC/FAR/FRR/EER from labelled comparison scores.",
        ),
        processing_time_ms=round((time.perf_counter() - started) * 1000, 3),
        metrics={
            "auc": result.auc,
            "eer": result.eer.get("eer"),
            "counts": result.counts,
        },
        warnings=list(result.warnings),
        limitations=list(result.limitations),
        evaluation=result.to_dict(),
    )


@router.get("/algorithms", summary="Catalogue of available algorithms")
async def list_algorithms() -> dict[str, Any]:
    """Describe every algorithm the service can run and its limitations."""
    from ..algorithms.enhancement import describe_algorithms
    from ..algorithms.roi import ROI_ALGORITHMS, get_roi_algorithm
    from ..features.classical_features import describe as describe_features

    roi_entries = []
    for name in sorted(ROI_ALGORITHMS):
        instance = get_roi_algorithm(name)
        roi_entries.append(
            {
                "name": instance.name,
                "type": "roi",
                "description": instance.description,
                "parameters": {},
                "limitations": list(instance.limitations),
            }
        )

    enhancement_entries = describe_algorithms()
    for entry in enhancement_entries:
        entry["type"] = "enhancement"

    feature_entries = describe_features()
    for entry in feature_entries:
        entry["type"] = "feature"

    trained = discover_models(settings.model_dir)

    return {
        "roi": roi_entries,
        "enhancement": enhancement_entries,
        "feature": feature_entries,
        "recognition": {
            "name": ClassicalMatcher.name,
            "type": "recognition",
            "description": "Untrained descriptor-matching comparison pipeline.",
            "parameters": {
                "detector": {"type": "enum", "values": ["orb", "akaze"], "default": "orb"},
                "lowe_ratio": {"type": "float", "default": 0.75, "range": [0.01, 0.99]},
            },
            "limitations": list(ClassicalMatcher.limitations()),
        },
        "trained_models": trained.to_dict(),
    }


@router.get("/artifacts/{artifact_id}", summary="Download a generated artefact")
async def get_artifact(artifact_id: str) -> Response:
    """Return a previously generated output image."""
    from ..utils.errors import ArtifactNotFoundError

    try:
        artifact = artifact_store.get(artifact_id)
    except ArtifactNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message) from exc

    data = artifact.path.read_bytes()
    return Response(
        content=data,
        media_type=artifact.media_type,
        headers={"Content-Disposition": f'inline; filename="{artifact.artifact_id}.png"'},
    )


__all__ = ["artifact_store", "router"]
