"""Image enhancement algorithms."""

from . import clahe, filtering, histogram_equalization

ENHANCEMENT_ALGORITHMS = {
    histogram_equalization.ALGORITHM_NAME: histogram_equalization,
    clahe.ALGORITHM_NAME: clahe,
    filtering.ALGORITHM_NAME: filtering,
}


def describe_algorithms() -> list[dict[str, object]]:
    """Return the machine readable description of every enhancement algorithm."""
    return [module.describe() for module in ENHANCEMENT_ALGORITHMS.values()]


__all__ = [
    "ENHANCEMENT_ALGORITHMS",
    "clahe",
    "describe_algorithms",
    "filtering",
    "histogram_equalization",
]
