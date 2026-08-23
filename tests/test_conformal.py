#!/usr/bin/env python3
"""Tests for the Split Conformal Prediction Engine (Phase 1)."""
import numpy as np
import pytest
from utils.conformal_predictor import (
    ConformalPredictor,
    get_default_predictor,
    DEFAULT_Q_HAT,
)


class TestConformalPredictor:
    def setup_method(self):
        self.cp = ConformalPredictor(alpha=0.05)

    def test_regression_interval_covers_point(self):
        """predict_interval should bracket the point prediction."""
        lo, pt, hi = self.cp.predict_interval(0.5, endpoint="ic50")
        assert lo < pt < hi
        assert pt == pytest.approx(0.5)

    def test_classification_prediction_set(self):
        """prediction_set should return a valid class membership set."""
        ps = self.cp.prediction_set(0.9, endpoint="tox21")
        assert ps["size"] >= 1
        assert 1 in ps["set"]  # high prob -> positive class in set
        assert ps["coverage"] == pytest.approx(0.95)

    def test_ambiguous_set_for_low_confidence(self):
        """When p is near 0.5 with wide q_hat, both classes may be in the set."""
        q = DEFAULT_Q_HAT["tox21"]
        threshold = 1.0 - q
        # p at the threshold boundary: p >= threshold → class 1 in set
        # 1-p = q >= threshold → only if q >= 1-q, i.e. q >= 0.5
        # With q=0.31, threshold=0.69, so p=0.69 gives class 1 only.
        # Test with a higher q_hat to get ambiguity:
        cp2 = ConformalPredictor(alpha=0.05, q_hat_overrides={"tox21": 0.6})
        ps = cp2.prediction_set(0.5, endpoint="tox21")
        assert ps["set"] == [0, 1]
        assert ps["ambiguous"] is True

    def test_default_q_hat_keys(self):
        """All 4 required datasets must have default q_hat placeholder estimates."""
        for ds in ("tox21", "bbbp", "bace", "clintox"):
            assert ds in DEFAULT_Q_HAT

    def test_nitrobenzene_default_q_hat(self):
        """Nitrobenzene toxicophore must have a default q_hat entry (placeholder estimate)."""
        assert "nitrobenzene" in DEFAULT_Q_HAT
        assert DEFAULT_Q_HAT["nitrobenzene"] == 0.38

    def test_prediction_set_reports_q_hat_source(self):
        """Default endpoints must be flagged as default estimates, not calibrated."""
        ps = self.cp.prediction_set(0.9, endpoint="tox21")
        assert ps["q_hat_source"] == "default_estimate"
        assert ps["coverage_guaranteed"] is False

    def test_live_calibration_upgrades_source(self):
        """After real calibration, q_hat_source must report live calibration."""
        rng = np.random.default_rng(0)
        y = rng.integers(0, 2, 200)
        probs = np.clip(y + rng.normal(0, 0.3, 200), 0.01, 0.99)
        self.cp.calibrate_classification(y, probs, endpoint="tox21")
        ps = self.cp.prediction_set(0.9, endpoint="tox21")
        assert ps["q_hat_source"] == "live_calibration"
        assert ps["coverage_guaranteed"] is True

    def test_endpoint_alias_resolution(self):
        """Aliases should resolve to canonical endpoint keys."""
        from utils.conformal_predictor import _canonical_endpoint
        assert _canonical_endpoint("nr-ar") == "tox21"
        assert _canonical_endpoint("BBB") == "bbbp"
        assert _canonical_endpoint("BACE1") == "bace"
        assert _canonical_endpoint("nitro") == "nitrobenzene"

    def test_calibration_hash_deterministic(self):
        """calibration_hash should be stable for the same config."""
        h1 = self.cp.calibration_hash()
        h2 = self.cp.calibration_hash()
        assert h1 == h2

    def test_default_predictor_singleton(self):
        """get_default_predictor should return a cached singleton."""
        p1 = get_default_predictor()
        p2 = get_default_predictor()
        assert p1 is p2

    def test_coverage_empirical(self):
        """Empirical coverage on synthetic data should be >= 0.90 (allowing slack)."""
        rng = np.random.default_rng(123)
        cp = ConformalPredictor(alpha=0.05)
        y = rng.normal(0, 1, 500)
        preds = y + rng.normal(0, 0.2, 500)
        cp.calibrate_regression(y, preds, "clearance")

        y2 = rng.normal(0, 1, 2000)
        p2 = y2 + rng.normal(0, 0.2, 2000)
        covered = sum(1 for yi, pi in zip(y2, p2) if (lo := cp.predict_interval(pi, "clearance")[0]) <= yi <= cp.predict_interval(pi, "clearance")[2])
        rate = covered / len(y2)
        assert rate >= 0.90  # allow some slack below 0.95
