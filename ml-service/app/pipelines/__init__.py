"""Processing pipelines of the ML service."""

from .comparison_pipeline import ComparisonOutcome, compare_images
from .enhancement_pipeline import EnhancementResult, apply_enhancement
from .feature_pipeline import FeatureExtractionOutcome, extract, match
from .quality_pipeline import analyze_quality
from .roi_pipeline import extract_roi

__all__ = [
    "ComparisonOutcome",
    "EnhancementResult",
    "FeatureExtractionOutcome",
    "analyze_quality",
    "apply_enhancement",
    "compare_images",
    "extract",
    "extract_roi",
    "match",
]
