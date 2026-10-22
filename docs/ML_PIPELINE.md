# ML / Computer Vision Pipeline

All image processing runs in the ML service. Every algorithm is classical,
deterministic and documented in code with an explicit list of limitations.
The service exposes the catalogue at `GET /api/v1/algorithms`.

## Image validation

1. Content-length and upload-size limits are enforced before decoding.
2. The file is decoded with OpenCV into a BGR array.
3. Pixel count and maximum dimensions are checked.
4. Media type is derived from the decoded content, never trusted from the
   client. PNG, JPEG, BMP, TIFF and WebP are accepted.
5. Corrupt or empty files produce a structured `400`/`415` error.

## ROI proposal

Algorithm: `classical_contour_roi` (versioned).

1. Convert to grayscale.
2. Blur to suppress sensor noise.
3. Segment the hand region with Otsu thresholding and morphological closing.
4. Find the largest external contour.
5. Return its bounding box, coverage ratio and a cropped artifact.

Limitations:

- This is a **region proposal**, not anatomical landmark detection.
- It can select a forearm or background object when the hand is not
  dominant in the frame.
- It makes no attempt to align rotation or perspective.
- It is not suitable for contactless verification without additional
  segmentation work.

## Enhancement

| Algorithm | Description | Key parameters |
| --- | --- | --- |
| `clahe` | Contrast-limited adaptive histogram equalisation on the L channel | `clip_limit` 0.1-40 (2.0), `tile_grid_size` 1-32 (8) |
| `histogram_equalization` | Global equalisation in LAB or per channel | `color_space` `lab` or `per_channel` |
| `filtering` | Median, Gaussian, bilateral or unsharp mask | `filter` `median`/`gaussian`/`bilateral`/`sharpen`, `kernel_size` 3-31, `sigma`, `amount`, `radius` |

Limitations:

- CLAHE amplifies noise as well as ridge contrast.
- Global equalisation can destroy local ridge information under uneven
  illumination.
- Sharpening creates halos and is not a substitute for correct focus.
- Enhancement does not create information that was not captured.

## Quality assessment

Measured indicators:

- **Brightness:** mean intensity, over-exposed and under-exposed percentages.
- **Contrast:** RMS contrast and Michelson contrast.
- **Sharpness:** variance of the Laplacian plus a blur flag.
- **Resolution:** width, height and megapixels.

A combined score in `[0, 100]` is included for convenience. It uses fixed
weights (`exposure` 0.30, `contrast` 0.30, `sharpness` 0.30, `resolution`
0.10) and is explicitly flagged as an **experimental, unvalidated heuristic**.
It is not a NFIQ-style certified metric and must not be used as a decision
threshold without a validation study.

## Feature extraction and landmarks

- Detectors: ORB and AKAZE.
- Outputs: keypoint count, coordinates, responses, sizes, angles and
  descriptors; optionally a landmark overlay artifact.
- These are generic computer-vision detectors, not palmprint-specific
  minutiae or crease detectors.

## Recognition / comparison

### Classical matcher

1. Extract ORB or AKAZE features from both images.
2. Match with Lowe's ratio test and optional cross-check.
3. Score = surviving matches divided by the size of the smaller descriptor
   set, clipped to `[0, 1]`.

The result is labelled `uncalibrated_similarity_index`. It is **not** a
probability, **not** a verification decision and **not** calibrated against a
genuine/impostor protocol. A high score on synthetic or repeated imagery can
be meaningless.

### Pixel comparison

- PSNR, SSIM and per-channel difference statistics.
- Useful for enhancement regression tests and artifact review.
- Not a biometric matcher.

## Evaluation metrics

`POST /api/v1/evaluation/run` accepts genuine/impostor scores and labels and
returns:

- ROC curve points and AUC.
- FAR and FRR at requested thresholds.
- Equal Error Rate (EER) with the caveat that EER is only an estimate for the
  supplied scores.
- Confusion matrix at a threshold (classification view).

Insufficient or single-class data returns an explicit message instead of a
fabricated number.

## Trained models

The repository ships **without** trained weights. `app/recognition/model_loader.py`
defines `TrainedModelAdapter` and `register_trained_model`. If weights are
present but no implementation is registered, `/health` and the recognition
endpoint report the model as unavailable. The platform never invents a
prediction.

To integrate a model:

1. Train it on an authorised dataset outside this repository.
2. Subclass `TrainedModelAdapter` and implement `load()` and `embed()`.
3. Register it with `@register_trained_model("model_name")`.
4. Place the weights in `ML_MODEL_DIR` with a supported suffix.
5. Add calibration and evaluation code before exposing a threshold.

## Artifacts

- Written under `ML_ARTIFACT_DIR` with random IDs.
- Retention defaults to 24 hours (`ML_ARTIFACT_RETENTION_HOURS`).
- Downloads require the service token when configured.
- The backend copies artifacts it needs into its own storage, so the ML
  service remains stateless from the platform's perspective.

## Reproducibility

Every response records the algorithm name, version and exact parameters.
Given the same input bytes, parameters and library versions, the classical
pipelines are deterministic. Report the versions from `/health` alongside any
experimental result.
