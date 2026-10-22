"""Tests for the biometric evaluation metrics."""

from __future__ import annotations

import pytest

from app.evaluation.confusion_matrix import confusion_matrix
from app.evaluation.metrics import (
    auc_score,
    equal_error_rate,
    evaluate_scores,
    false_rates,
    roc_curve,
)
from app.evaluation.roc import roc_points


def test_perfect_separation_has_auc_one() -> None:
    scores = [0.9, 0.85, 0.8, 0.2, 0.15, 0.1]
    labels = [1, 1, 1, 0, 0, 0]
    assert auc_score(scores, labels) == pytest.approx(1.0)


def test_random_separation_has_auc_around_half() -> None:
    scores = [0.5, 0.5, 0.5, 0.5]
    labels = [1, 1, 0, 0]
    assert 0.0 <= auc_score(scores, labels) <= 1.0


def test_roc_curve_points_are_monotonic() -> None:
    curve = roc_curve([0.9, 0.8, 0.4, 0.1], [1, 1, 0, 0])
    assert curve["tpr"][0] == 0.0
    assert curve["tpr"][-1] == 1.0
    assert curve["fpr"][0] == 0.0
    assert curve["fpr"][-1] == 1.0


def test_roc_points_helper() -> None:
    points = roc_points([0.9, 0.4, 0.1], [1, 0, 0])
    assert len(points) >= 2
    assert {"fpr", "tpr", "threshold"} <= set(points[0])


def test_false_rates_at_threshold() -> None:
    scores = [0.9, 0.8, 0.3, 0.2]
    labels = [1, 1, 0, 0]
    rates = false_rates(scores, labels, thresholds=[0.5])
    assert rates["points"][0]["far"] == 0.0
    assert rates["points"][0]["frr"] == 0.0


def test_equal_error_rate_is_between_zero_and_one() -> None:
    result = equal_error_rate([0.9, 0.8, 0.4, 0.3, 0.2, 0.1], [1, 1, 1, 0, 0, 0])
    assert result["eer"] is not None
    assert 0.0 <= result["eer"] <= 1.0


def test_evaluate_scores_requires_matching_lengths() -> None:
    with pytest.raises(ValueError):
        evaluate_scores([0.5], [1, 0])


def test_evaluate_scores_rejects_invalid_labels() -> None:
    with pytest.raises(ValueError):
        evaluate_scores([0.5, 0.6], [1, 5])


def test_evaluate_scores_warns_when_a_class_is_missing() -> None:
    result = evaluate_scores([0.5, 0.6], [1, 1])
    assert any(
        "one class" in warning or "Both genuine and impostor" in warning
        for warning in result.warnings
    )
    assert result.counts["num_impostor"] == 0


def test_evaluate_scores_returns_full_payload() -> None:
    result = evaluate_scores([0.9, 0.8, 0.3, 0.2], [1, 1, 0, 0])
    payload = result.to_dict()
    assert payload["auc"] == pytest.approx(1.0)
    assert payload["counts"]["num_comparisons"] == 4
    assert payload["warnings"]


def test_confusion_matrix_counts() -> None:
    matrix = confusion_matrix([0.9, 0.8, 0.3, 0.2], [1, 1, 0, 0], threshold=0.5)
    assert matrix["matrix"]["true_positive"] == 2
    assert matrix["matrix"]["true_negative"] == 2
    assert matrix["accuracy"] == 1.0
