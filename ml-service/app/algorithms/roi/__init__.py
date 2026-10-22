"""ROI extraction algorithms."""

from .base import ROIAlgorithm, ROIResult
from .classical_roi import ClassicalROIAlgorithm

#: Registry of available ROI algorithms keyed by their public name.
ROI_ALGORITHMS: dict[str, type[ROIAlgorithm]] = {
    ClassicalROIAlgorithm.name: ClassicalROIAlgorithm,
}


def get_roi_algorithm(name: str | None) -> ROIAlgorithm:
    """Instantiate an ROI algorithm by name (defaults to the classical one)."""
    key = (name or ClassicalROIAlgorithm.name).strip().lower()
    try:
        algorithm_class = ROI_ALGORITHMS[key]
    except KeyError as exc:
        raise KeyError(
            f"Unknown ROI algorithm '{key}'. Available: {sorted(ROI_ALGORITHMS)}"
        ) from exc
    return algorithm_class()


__all__ = [
    "ClassicalROIAlgorithm",
    "ROIAlgorithm",
    "ROIResult",
    "ROI_ALGORITHMS",
    "get_roi_algorithm",
]
