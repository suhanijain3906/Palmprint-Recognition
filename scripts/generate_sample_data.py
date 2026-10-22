#!/usr/bin/env python3
"""Generate deterministic synthetic palm-like images for demos and tests.

The generated images are **not** biometric samples. They are procedural
textures that let you exercise the pipeline without downloading or
redistributing a restricted palmprint dataset.

Usage
-----
    python scripts/generate_sample_data.py --count 4
    python scripts/generate_sample_data.py --e2e-fixture

Requires NumPy and Pillow (both are installed by the ML service requirements).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

try:
    import numpy as np
    from PIL import Image
except ImportError as exc:  # pragma: no cover - user environment dependent
    print(
        "NumPy and Pillow are required. Install them with:\n"
        "  pip install numpy Pillow\n"
        f"Original error: {exc}",
        file=sys.stderr,
    )
    raise SystemExit(1) from exc


def synthetic_palm(width: int, height: int, *, seed: int) -> np.ndarray:
    """Create a synthetic palm-like RGB image (no real biometric data)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    cx, cy = width / 2.0, height / 2.0

    background = 25 + rng.normal(0, 4, (height, width, 3))
    ellipse = ((xx - cx) / (width * 0.37)) ** 2 + ((yy - cy) / (height * 0.42)) ** 2
    mask = np.clip((1.0 - ellipse) * 6.0, 0.0, 1.0)

    radial = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    angular = np.arctan2(yy - cy, xx - cx)
    ridges = 0.5 + 0.5 * np.sin(radial * 1.5 + angular * 0.8)
    creases = 0.5 + 0.5 * np.sin(angular * 9.0 + radial * 0.05)
    texture = 95 + 70 * ridges + 25 * creases + rng.normal(0, 3, (height, width))
    palm = np.stack([texture * 1.02, texture * 0.92, texture * 0.82], axis=-1)

    alpha = mask[..., None]
    image = np.clip(palm * alpha + background * (1.0 - alpha), 0, 255)
    return image.astype(np.uint8)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=4, help="number of samples")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/samples"),
        help="output directory for the samples",
    )
    parser.add_argument("--width", type=int, default=384)
    parser.add_argument("--height", type=int, default=448)
    parser.add_argument("--seed", type=int, default=2024)
    parser.add_argument(
        "--e2e-fixture",
        action="store_true",
        help="also write frontend/e2e/fixtures/synthetic_palm.png",
    )
    args = parser.parse_args()

    if args.count < 1:
        parser.error("--count must be at least 1")

    args.output.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index in range(args.count):
        image = synthetic_palm(args.width, args.height, seed=args.seed + index)
        target = args.output / f"synthetic_palm_{index + 1:03d}.png"
        Image.fromarray(image).save(target, format="PNG")
        written.append(target)

    if args.e2e_fixture:
        fixture = (
            Path(__file__).resolve().parent.parent / "frontend" / "e2e" / "fixtures"
        )
        fixture.mkdir(parents=True, exist_ok=True)
        target = fixture / "synthetic_palm.png"
        Image.fromarray(synthetic_palm(384, 448, seed=args.seed)).save(
            target, format="PNG"
        )
        written.append(target)

    for path in written:
        print(f"wrote {path}")
    print(
        "\nThese are procedurally generated textures, not real palmprints. "
        "They are safe to redistribute."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
