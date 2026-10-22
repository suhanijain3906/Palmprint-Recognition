#!/usr/bin/env python3
"""End-to-end smoke test against running backend and ML services.

This script talks to the public backend API exactly like the frontend does.
It uploads two procedurally generated images, runs the processing pipelines,
an experiment, a recognition and a comparison, then generates and downloads a
PDF report.

It deliberately does **not** import the application modules: it verifies the
deployed HTTP contract instead of internal functions.

Usage:
    python scripts/smoke_test.py
    python scripts/smoke_test.py --backend http://localhost:8000
    python scripts/smoke_test.py --ml http://localhost:8001 --require-roi

Exit code 0 means every required check passed.
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
import zlib

try:
    import httpx
except ImportError:  # pragma: no cover - environment dependent
    print("httpx is required. Install it with: pip install httpx", file=sys.stderr)
    raise SystemExit(1)


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data))
        + kind
        + data
        + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    )


def synthetic_png(width: int = 256, height: int = 320, *, seed: int = 1) -> bytes:
    """Build a small RGB PNG without third party image libraries."""
    rows = bytearray()
    cx, cy = width / 2.0, height / 2.0
    for y in range(height):
        rows.append(0)  # filter type: none
        for x in range(width):
            dx, dy = x - cx, y - cy
            radius = math.sqrt(dx * dx + dy * dy)
            inside = (dx / (width * 0.38)) ** 2 + (dy / (height * 0.42)) ** 2 <= 1.0
            if inside:
                value = 110 + int(70 * (0.5 + 0.5 * math.sin(radius * 0.9 + seed)))
                r, g, b = (
                    min(255, value),
                    min(255, int(value * 0.9)),
                    min(255, int(value * 0.8)),
                )
            else:
                r = g = b = 24 + (x + y + seed) % 8
            rows.extend((r, g, b))

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", header)
        + _png_chunk(b"IDAT", zlib.compress(bytes(rows), 9))
        + _png_chunk(b"IEND", b"")
    )


class Smoke:
    def __init__(self, backend: str, ml: str, timeout: float) -> None:
        self.backend = backend.rstrip("/")
        self.ml = ml.rstrip("/")
        self.client = httpx.Client(timeout=timeout)
        self.checks: list[tuple[str, bool, str]] = []

    def record(self, name: str, ok: bool, detail: str = "") -> None:
        self.checks.append((name, ok, detail))
        print(
            f"[{'PASS' if ok else 'FAIL'}] {name}{(' - ' + detail) if detail else ''}"
        )

    def get(self, url: str):
        return self.client.get(url)

    def post(self, url: str, **kwargs):
        return self.client.post(url, **kwargs)

    def run(self, *, require_roi: bool) -> int:
        print(f"Backend: {self.backend}")
        print(f"ML service: {self.ml}\n")

        health = self.get(f"{self.backend}/health")
        self.record(
            "backend /health", health.status_code == 200, f"HTTP {health.status_code}"
        )
        if health.status_code == 200:
            ml_status = health.json().get("ml_service", {}).get("status")
            self.record("backend reports ML service", ml_status == "ok", str(ml_status))

        ready = self.get(f"{self.backend}/ready")
        self.record(
            "backend /ready", ready.status_code == 200, f"HTTP {ready.status_code}"
        )

        ml_health = self.get(f"{self.ml}/health")
        self.record(
            "ML service /health",
            ml_health.status_code == 200,
            f"HTTP {ml_health.status_code}",
        )

        images: list[str] = []
        for index, seed in enumerate((1, 7), start=1):
            payload = synthetic_png(seed=seed)
            response = self.post(
                f"{self.backend}/api/v1/images/upload",
                files={"file": (f"synthetic_{index}.png", payload, "image/png")},
                data={"label": "synthetic", "subject_id": f"SYN-{index:03d}"},
            )
            ok = response.status_code == 201
            detail = f"HTTP {response.status_code}"
            if ok:
                body = response.json()
                image_id = body["image"]["id"]
                images.append(image_id)
                detail = f"id={image_id[:8]} {body['image']['width']}x{body['image']['height']}"
            else:
                detail += f" {response.text[:160]}"
            self.record(f"upload image {index}", ok, detail)
            if not ok:
                return self._finish()

        if len(images) < 2:
            return self._finish()

        roi = self.post(
            f"{self.backend}/api/v1/processing/roi", json={"image_id": images[0]}
        )
        roi_detail = f"HTTP {roi.status_code}"
        if roi.status_code == 200:
            body = roi.json()
            roi_detail += f", {len(body.get('artifacts', []))} artifact(s)"
        elif roi.status_code == 422:
            roi_detail += " (no reliable palm region found - documented failure mode)"
        self.record(
            "ROI extraction", roi.status_code == 200 or not require_roi, roi_detail
        )
        if require_roi and roi.status_code != 200:
            self.record("ROI required by --require-roi", False, roi_detail)

        enhancement = self.post(
            f"{self.backend}/api/v1/processing/enhancement",
            json={
                "image_id": images[0],
                "algorithm": "clahe",
                "parameters": {"clip_limit": 2.0},
            },
        )
        self.record(
            "CLAHE enhancement",
            enhancement.status_code == 200
            and bool(enhancement.json().get("artifacts")),
            f"HTTP {enhancement.status_code}",
        )

        quality = self.post(
            f"{self.backend}/api/v1/processing/quality", json={"image_id": images[0]}
        )
        quality_ok = quality.status_code == 200
        quality_job = quality.json().get("job_id") if quality_ok else None
        quality_score = None
        if quality_ok:
            quality_score = quality.json().get("result", {}).get("combined_score")
        self.record(
            "quality assessment",
            quality_ok and quality_score is not None,
            f"combined_score={quality_score}",
        )

        recognition = self.post(
            f"{self.backend}/api/v1/recognition/compare",
            json={"image_a_id": images[0], "image_b_id": images[1]},
        )
        recognition_ok = recognition.status_code == 200
        rec_body = recognition.json() if recognition_ok else {}
        self.record(
            "experimental recognition",
            recognition_ok
            and rec_body.get("is_trained_model") is False
            and rec_body.get("similarity_score") is not None,
            f"score={rec_body.get('similarity_score')} kind={rec_body.get('score_kind')}",
        )

        comparison = self.post(
            f"{self.backend}/api/v1/comparison",
            json={"image_a_id": images[0], "image_b_id": images[1]},
        )
        comparison_ok = comparison.status_code == 200
        cmp_body = comparison.json() if comparison_ok else {}
        self.record(
            "image comparison (PSNR/SSIM)",
            comparison_ok and cmp_body.get("psnr_db") is not None,
            f"PSNR={cmp_body.get('psnr_db')} SSIM={cmp_body.get('ssim')}",
        )

        experiment = self.post(
            f"{self.backend}/api/v1/experiments",
            json={
                "name": "Smoke test quality experiment",
                "description": "Created by scripts/smoke_test.py",
                "operation": "quality",
                "algorithm": "quality_report",
                "parameters": {},
                "image_ids": images,
            },
        )
        experiment_ok = experiment.status_code == 200
        exp_body = experiment.json() if experiment_ok else {}
        self.record(
            "experiment run",
            experiment_ok
            and exp_body.get("status") == "completed"
            and bool(exp_body.get("results")),
            f"status={exp_body.get('status')} results={len(exp_body.get('results', []))}",
        )

        if quality_job:
            report = self.post(
                f"{self.backend}/api/v1/reports",
                json={
                    "title": "Smoke test report",
                    "report_type": "processing",
                    "job_ids": [quality_job],
                    "include_images": False,
                },
            )
            report_ok = report.status_code == 201
            report_body = report.json() if report_ok else {}
            self.record(
                "PDF report generation",
                report_ok,
                f"status={report_body.get('status')}",
            )
            if report_ok and report_body.get("download_url"):
                download = self.get(f"{self.backend}{report_body['download_url']}")
                self.record(
                    "PDF report download",
                    download.status_code == 200
                    and download.content.startswith(b"%PDF"),
                    f"{len(download.content)} bytes",
                )

        listing = self.get(f"{self.backend}/api/v1/images")
        self.record(
            "image listing",
            listing.status_code == 200
            and listing.json().get("meta", {}).get("total", 0) >= 2,
            f"HTTP {listing.status_code}",
        )

        datasets = self.get(f"{self.backend}/api/v1/datasets")
        self.record(
            "dataset catalogue",
            datasets.status_code == 200 and bool(datasets.json()),
            f"HTTP {datasets.status_code}",
        )

        return self._finish()

    def _finish(self) -> int:
        failures = [name for name, ok, _ in self.checks if not ok]
        print("\n" + "=" * 60)
        print(f"{len(self.checks) - len(failures)}/{len(self.checks)} checks passed")
        if failures:
            print("Failed checks: " + ", ".join(failures))
            return 1
        print("Smoke test passed.")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--backend", default="http://localhost:8000")
    parser.add_argument("--ml", default="http://localhost:8001")
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument(
        "--require-roi",
        action="store_true",
        help="treat a failed ROI extraction as a failure instead of a warning",
    )
    args = parser.parse_args()

    smoke = Smoke(args.backend, args.ml, args.timeout)
    try:
        return smoke.run(require_roi=args.require_roi)
    except httpx.HTTPError as exc:
        print(f"\nFAIL: a service could not be reached: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
