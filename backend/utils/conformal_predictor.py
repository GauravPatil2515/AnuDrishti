#!/usr/bin/env python3
"""
Conformal Prediction Module (Phase 1 — Robustness & Trust)
==========================================================

Split conformal prediction for regression endpoints (Clearance, IC50) and
classification probability sets for Tox21-style endpoints, with a
distribution-free (1 - alpha) coverage guarantee (Vovk et al., Papadopoulos
et al.) — BUT ONLY once calibrated with real held-out data via
``calibrate_regression()`` / ``calibrate_classification()``.

DEFAULT_Q_HAT values shipped below are APPROXIMATE PLACEHOLDER ESTIMATES,
not computed from real calibration data. Until you call the calibrate_*
methods with a real held-out dataset (replacing these defaults), treat all
intervals/prediction sets as indicative only — they are NOT statistically
guaranteed. The framework code itself is correct; only the default q_hat
values need real calibration.
"""

import hashlib
import json
import os
import numpy as np
from typing import Dict, List, Optional, Tuple, Any

# ─────────────────────────────────────────────────────────────────────────────
# Default non-conformity quantiles (95% nominal coverage, alpha=0.05).
# ⚠️ DEFAULT Q_HAT values — APPROXIMATE ESTIMATES. Not computed from real
# calibration data. Call calibrate_classification() or calibrate_regression()
# with a real held-out dataset to replace these with valid,
# coverage-guaranteed values. Until then, treat confidence intervals as
# indicative only, not statistically guaranteed.
# Version-locked: bump CONFORMAL_CALIBRATION_VERSION when re-calibrating.
# ─────────────────────────────────────────────────────────────────────────────
CONFORMAL_CALIBRATION_VERSION = "v1.0.0"

DEFAULT_Q_HAT = {
    # classification endpoints (probability space, non-conformity = |1 - p(y)|)
    "tox21": 0.31,
    "bbbp": 0.24,
    "bace": 0.27,
    "clintox": 0.33,
    # nitrobenzene / nitro-toxicophore alias keys (same placeholder caveat)
    "nitrobenzene": 0.38,
    "ntox": 0.38,
    # regression endpoints (response space, non-conformity = |y - y_hat|)
    "clearance": 0.42,   # log mL/min/kg residual scale
    "ic50": 0.55,        # log IC50 (uM) residual scale
    "herg_ic50": 0.58,
}

# Endpoint alias map so callers can pass any naming variant
_ENDPOINT_ALIASES = {
    "tox21": "tox21", "tox": "tox21", "nr-ar": "tox21", "nr-ahr": "tox21",
    "sr-are": "tox21", "sr-p53": "tox21", "sr-mmp": "tox21", "sr-hse": "tox21",
    "sr-atad5": "tox21", "nr-er": "tox21", "nr-er-lbd": "tox21",
    "nr-ar-lbd": "tox21", "nr-aromatase": "tox21", "nr-ppar-gamma": "tox21",
    "bbbp": "bbbp", "bbb": "bbbp", "blood_brain_barrier": "bbbp",
    "bace": "bace", "bace1": "bace",
    "clintox": "clintox", "clin_tox": "clintox", "fda_approved": "clintox",
    "ct_tox": "clintox",
    # nitrobenzene / nitro-toxicophore aliases
    "nitrobenzene": "nitrobenzene", "nitro": "nitrobenzene", "nitrotox": "nitrobenzene",
    "ci_tox": "nitrobenzene", "ci_tox21": "nitrobenzene", "cnp": "nitrobenzene",
    "clearance": "clearance", "clint": "clearance",
    "ic50": "ic50", "herg": "herg_ic50", "herg_ic50": "herg_ic50",
}


def _canonical_endpoint(endpoint: str) -> str:
    return _ENDPOINT_ALIASES.get(str(endpoint).strip().lower(), str(endpoint).strip().lower())


class ConformalPredictor:
    """
    Split conformal prediction wrapper.

    Regression: prediction intervals (lower, point, upper) with finite-sample
    corrected (1-alpha) coverage, calibrated on held-out residuals.

    Classification: (1-alpha) coverage *prediction sets* from probability
    non-conformity scores 1 - p(true_class).

    Runs out-of-the-box using DEFAULT_Q_HAT placeholder estimates; call
    ``calibrate_*()`` with real held-out data to obtain valid,
    coverage-guaranteed intervals. Check ``prediction_set(...)['q_hat_source']``
    to know whether an interval came from live calibration or a default.
    """

    def __init__(self, alpha: float = 0.05, q_hat_overrides: Optional[Dict[str, float]] = None):
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must be in (0, 1)")
        self.alpha = float(alpha)
        self.q_hat: Dict[str, float] = dict(DEFAULT_Q_HAT)
        if q_hat_overrides:
            self.q_hat.update({k: float(v) for k, v in q_hat_overrides.items()})
        self._calibrated_endpoints: set = set()
        self.calibration_version = CONFORMAL_CALIBRATION_VERSION

    # ── Regression (split conformal) ─────────────────────────────────────────
    def calibrate_regression(self, y_calib, preds_calib, endpoint: str = "clearance") -> float:
        """Calibrate q_hat from held-out absolute residuals (response space)."""
        y = np.asarray(y_calib, dtype=float)
        p = np.asarray(preds_calib, dtype=float)
        if y.shape != p.shape or y.size == 0:
            raise ValueError("y_calib and preds_calib must be same-shape, non-empty")
        residuals = np.abs(y - p)
        n = residuals.size
        # finite-sample corrected (1 - alpha) quantile
        q_level = min(1.0, np.ceil((n + 1) * (1 - self.alpha)) / n)
        q = float(np.quantile(residuals, q_level))
        key = _canonical_endpoint(endpoint)
        self.q_hat[key] = q
        self._calibrated_endpoints.add(key)
        return q

    def predict_interval(
        self, point_pred: float, endpoint: str = "clearance"
    ) -> Tuple[float, float, float]:
        """Return (lower_bound, point_pred, upper_bound) with (1-alpha) coverage."""
        key = _canonical_endpoint(endpoint)
        q = self.q_hat.get(key)
        if q is None:
            # conservative fallback: widest default
            q = max(DEFAULT_Q_HAT.values())
        p = float(point_pred)
        return (p - q, p, p + q)

    # ── Classification (probability coverage sets) ───────────────────────────
    def calibrate_classification(self, y_calib, probs_calib, endpoint: str = "tox21") -> float:
        """
        Calibrate classification q_hat from held-out data.

        y_calib: true labels (0/1) or list thereof
        probs_calib: predicted probability of the POSITIVE class
        Non-conformity score: 1 - p(true class).
        """
        y = np.asarray(y_calib).astype(int)
        p = np.asarray(probs_calib, dtype=float)
        if y.shape != p.shape or y.size == 0:
            raise ValueError("y_calib and probs_calib must be same-shape, non-empty")
        p_true = np.where(y == 1, p, 1.0 - p)
        scores = 1.0 - p_true
        n = scores.size
        q_level = min(1.0, np.ceil((n + 1) * (1 - self.alpha)) / n)
        q = float(np.quantile(scores, q_level))
        key = _canonical_endpoint(endpoint)
        self.q_hat[key] = q
        self._calibrated_endpoints.add(key)
        return q

    def prediction_set(self, prob: float, endpoint: str = "tox21") -> Dict[str, Any]:
        """
        Return the (1-alpha) coverage prediction set for a binary endpoint.

        A class label c is in the set iff its non-conformity score
        (1 - p(c)) <= q_hat, i.e. p(c) >= 1 - q_hat.
        """
        key = _canonical_endpoint(endpoint)
        q = self.q_hat.get(key, max(DEFAULT_Q_HAT.values()))
        p = float(np.clip(float(prob), 0.0, 1.0))
        threshold = 1.0 - q
        members = []
        if p >= threshold:
            members.append(1)
        if (1.0 - p) >= threshold:
            members.append(0)
        members.sort()
        live_calibrated = key in self._calibrated_endpoints
        return {
            "set": members,
            "size": len(members),
            "threshold": round(threshold, 4),
            "q_hat": round(q, 4),
            # nominal design coverage of the conformal method
            "coverage": round(1.0 - self.alpha, 2),
            "q_hat_source": "live_calibration" if live_calibrated else "default_estimate",
            # the coverage guarantee holds ONLY for live-calibrated endpoints;
            # default q_hat values are placeholder estimates
            "coverage_guaranteed": live_calibrated,
            "ambiguous": len(members) == 2,  # both classes covered -> abstain-worthy
        }

    # ── Introspection / audit ─────────────────────────────────────────────────
    def calibration_hash(self) -> str:
        """sha256 of the active calibration table (21 CFR Part 11 traceability)."""
        payload = json.dumps(
            {"version": self.calibration_version, "alpha": self.alpha,
             "q_hat": {k: self.q_hat[k] for k in sorted(self.q_hat)}},
            sort_keys=True,
        )
        return "sha256_" + hashlib.sha256(payload.encode()).hexdigest()[:16]

    def load_calibration_file(self, path: Optional[str] = None) -> bool:
        """Load calibrated q_hat map from results/calibration/coverage_stats.json if present."""
        if path is None:
            here = os.path.dirname(os.path.abspath(__file__))
            repo_root = os.path.abspath(os.path.join(here, "..", ".."))
            path = os.path.join(repo_root, "results", "calibration", "coverage_stats.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                calib_map = data.get("calibrated_q_hat_map")
                if calib_map and isinstance(calib_map, dict):
                    for ep, q in calib_map.items():
                        canon = _canonical_endpoint(ep)
                        self.q_hat[canon] = float(q)
                        self._calibrated_endpoints.add(canon)
                    return True
            except Exception:
                pass
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": self.alpha,
            "coverage": round(1.0 - self.alpha, 2),
            "calibration_version": self.calibration_version,
            "calibration_hash": self.calibration_hash(),
            "q_hat": {k: round(v, 4) for k, v in sorted(self.q_hat.items())},
            "live_calibrated_endpoints": sorted(self._calibrated_endpoints),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT: Optional["ConformalPredictor"] = None


def get_default_predictor(alpha: float = 0.05) -> ConformalPredictor:
    """Module-level singleton for route integration.

    Ships with DEFAULT_Q_HAT placeholder estimates; automatically detects
    and loads results/calibration/coverage_stats.json if present on disk
    to restore data-driven coverage guarantees.
    """
    global _DEFAULT
    if _DEFAULT is None or abs(_DEFAULT.alpha - alpha) > 1e-9:
        _DEFAULT = ConformalPredictor(alpha=alpha)
        _DEFAULT.load_calibration_file()
    return _DEFAULT


# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 3: Mondrian Scaffold-Stratified Conformal Predictor
# ─────────────────────────────────────────────────────────────────────────────
# Mondrian CP (Vovk et al., 2005) groups calibration residuals into equivalence
# classes (here: Bemis-Murcko scaffold clusters) and computes a *per-class*
# q_hat. Novel chemotypes — which share no scaffold with calibration data —
# get their own wide singleton interval, preventing under-coverage on OOD
# scaffolds. This is the standard approach for chemistry-aware conformal CP.
# ─────────────────────────────────────────────────────────────────────────────

def _bemis_murcko_scaffold(smiles: str) -> str:
    """Extract the Bemis-Murcko scaffold from a SMILES string.

    Falls back to a truncated fingerprint if the molecule cannot be parsed.
    The scaffold is used as the Mondrian equivalence class key.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem.Scaffolds import MurckoScaffold
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return "UNPARSED"
        scaffold = MurckoScaffold.GetScaffoldForMol(mol)
        if scaffold is None or scaffold.GetNumAtoms() == 0:
            return "EMPTY_SCAFFOLD"
        return Chem.MolToSmiles(scaffold)
    except Exception:
        # Fallback: use first 8 chars of canonical SMILES as a pseudo-scaffold
        try:
            from rdkit import Chem
            mol = Chem.MolFromSmiles(smiles)
            if mol:
                return Chem.MolToSmiles(mol)[:8]
        except Exception:
            pass
        return "FALLBACK_" + str(hash(smiles))[:8]


class MondrianConformalPredictor:
    """
    Mondrian (scaffold-stratified) split conformal predictor.

    Partitions calibration data into equivalence classes keyed by Bemis-Murcko
    scaffold, then computes a per-scaffold q_hat. At prediction time, the
    appropriate per-class interval is used; for scaffolds unseen during
    calibration, a conservative *global* q_hat (max over all classes) is applied
    so coverage is never under-conservative on novel chemotypes.

    Inherits the conformal CI API shape (conformal_ci_low/high) so it can be
    dropped in as a superset of ConformalPredictor.

    Reference:
        Vovk, Gammerman & Shafer — "Algorithmic Learning in a Random World"
        (2005). Mondrian Prediction.
    """

    RULESET_VERSION = "v3.0.0"

    def __init__(self, alpha: float = 0.05):
        if not 0.0 < alpha < 1.0:
            raise ValueError("alpha must be in (0, 1)")
        self.alpha = float(alpha)
        # q_hat per scaffold equivalence class
        self._q_hat_by_scaffold: Dict[str, float] = {}
        # Fallback global q_hat for unseen scaffolds (max over all classes).
        # ⚠️ Placeholder DEFAULT_Q_HAT estimate until calibrate() is run.
        self._global_q_hat: float = max(DEFAULT_Q_HAT.values())
        # Calibration metadata
        self._scaffold_stats: Dict[str, Dict[str, Any]] = {}
        self._calibrated = False
        self.calibration_version = CONFORMAL_CALIBRATION_VERSION

    def calibrate(
        self,
        smiles_list: List[str],
        y_calib,
        preds_calib,
        endpoint: str = "tox21"
    ) -> Dict[str, float]:
        """
        Calibrate per-scaffold q_hat values from held-out residuals.

        Args:
            smiles_list: SMILES strings of calibration molecules
            y_calib: true labels / values
            preds_calib: predicted probabilities / values
            endpoint: endpoint name for reporting

        Returns:
            Dict mapping scaffold SMILES -> q_hat for that class
        """
        import numpy as np
        y = np.asarray(y_calib, dtype=float)
        p = np.asarray(preds_calib, dtype=float)
        if y.shape != p.shape or y.size == 0:
            raise ValueError("y_calib and preds_calib must be same-shape, non-empty")
        if len(smiles_list) != y.size:
            raise ValueError("smiles_list length must match y_calib length")

        residuals = np.abs(y - p)
        n = residuals.size
        q_level = min(1.0, np.ceil((n + 1) * (1 - self.alpha)) / n)

        # Group residuals by scaffold
        scaffold_residuals: Dict[str, List[float]] = {}
        for smi, res in zip(smiles_list, residuals):
            scaffold = _bemis_murcko_scaffold(smi)
            scaffold_residuals.setdefault(scaffold, []).append(float(res))

        # Compute per-scaffold q_hat
        self._q_hat_by_scaffold = {}
        self._scaffold_stats = {}
        for scaffold, res_list in scaffold_residuals.items():
            res_arr = np.asarray(res_list, dtype=float)
            q = float(np.quantile(res_arr, q_level))
            self._q_hat_by_scaffold[scaffold] = q
            self._scaffold_stats[scaffold] = {
                "n": len(res_list),
                "mean_residual": float(np.mean(res_arr)),
                "q_hat": q,
            }

        # Global q_hat = max over all scaffold q_hats (conservative for unseen)
        if self._q_hat_by_scaffold:
            self._global_q_hat = max(self._q_hat_by_scaffold.values())

        self._calibrated = True
        self._endpoint = endpoint
        return dict(self._q_hat_by_scaffold)

    def predict_interval(
        self,
        point_pred: float,
        smiles: str,
        endpoint: str = "tox21"
    ) -> Tuple[float, float, float]:
        """
        Return (lower, point, upper) interval using scaffold-aware q_hat.

        For scaffolds seen during calibration: use per-scaffold q_hat.
        For novel scaffolds: use conservative global q_hat (max class width).
        """
        scaffold = _bemis_murcko_scaffold(smiles)
        key = _canonical_endpoint(endpoint)

        if scaffold in self._q_hat_by_scaffold:
            q = self._q_hat_by_scaffold[scaffold]
            scaffold_status = "calibrated"
        else:
            # OOD scaffold — use conservative global q_hat
            q = self._global_q_hat
            scaffold_status = "ood_unseen"

        p = float(point_pred)
        ci_low = round(p - q, 4)
        ci_high = round(p + q, 4)
        return (ci_low, p, ci_high)

    def prediction_set(
        self,
        prob: float,
        smiles: str,
        endpoint: str = "tox21"
    ) -> Dict[str, Any]:
        """Mondrian classification prediction set (per-scaffold q_hat)."""
        scaffold = _bemis_murcko_scaffold(smiles)
        key = _canonical_endpoint(endpoint)

        if scaffold in self._q_hat_by_scaffold:
            q = self._q_hat_by_scaffold[scaffold]
            scaffold_status = "calibrated"
        else:
            q = self._global_q_hat
            scaffold_status = "ood_unseen"

        p = float(np.clip(float(prob), 0.0, 1.0))
        threshold = 1.0 - q
        members = []
        if p >= threshold:
            members.append(1)
        if (1.0 - p) >= threshold:
            members.append(0)
        members.sort()
        return {
            "set": members,
            "size": len(members),
            "threshold": round(threshold, 4),
            "q_hat": round(q, 4),
            "coverage": round(1.0 - self.alpha, 2),
            "ambiguous": len(members) == 2,
            "scaffold": scaffold[:20] + "..." if len(scaffold) > 20 else scaffold,
            "scaffold_status": scaffold_status,
            "global_q_hat": round(self._global_q_hat, 4),
        }

    def calibration_hash(self) -> str:
        """SHA-256 of the scaffold-stratified calibration table."""
        payload = json.dumps({
            "version": self.calibration_version,
            "alpha": self.alpha,
            "q_hat_by_scaffold": {k: self._q_hat_by_scaffold[k]
                                  for k in sorted(self._q_hat_by_scaffold)},
            "global_q_hat": self._global_q_hat,
            "scaffold_stats": {k: self._scaffold_stats[k]
                               for k in sorted(self._scaffold_stats)},
        }, sort_keys=True)
        return "sha256_mondrian_" + hashlib.sha256(payload.encode()).hexdigest()[:16]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha": self.alpha,
            "coverage": round(1.0 - self.alpha, 2),
            "calibration_version": self.calibration_version,
            "calibration_hash": self.calibration_hash(),
            "n_scaffolds": len(self._q_hat_by_scaffold),
            "global_q_hat": round(self._global_q_hat, 4),
            "scaffold_q_hat": {k: round(v, 4)
                               for k, v in sorted(self._q_hat_by_scaffold.items())},
            "scaffold_stats": self._scaffold_stats,
            "calibrated": self._calibrated,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Mondrian singleton
# ─────────────────────────────────────────────────────────────────────────────
_MONDR: Optional["MondrianConformalPredictor"] = None


def get_default_mondrian_predictor(alpha: float = 0.05) -> MondrianConformalPredictor:
    """Module-level singleton for scaffold-stratified conformal prediction."""
    global _MONDR
    if _MONDR is None or abs(_MONDR.alpha - alpha) > 1e-9:
        _MONDR = MondrianConformalPredictor(alpha=alpha)
    return _MONDR


# ─────────────────────────────────────────────────────────────────────────────
# Self-test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    rng = np.random.default_rng(42)
    cp = ConformalPredictor()
    # synthetic calibration: residuals ~ N(0, 0.2)
    y = rng.normal(0, 1, 500)
    preds = y + rng.normal(0, 0.2, 500)
    q = cp.calibrate_regression(y, preds, "clearance")
    lo, pt, hi = cp.predict_interval(2.0, "clearance")
    print(f"calibrated q_hat={q:.3f}  interval for 2.0: [{lo:.3f}, {hi:.3f}]")
    # coverage check on fresh data
    y2 = rng.normal(0, 1, 5000)
    p2 = y2 + rng.normal(0, 0.2, 5000)
    covered = np.mean([(lo_i <= y_i <= hi_i) for y_i, (lo_i, _, hi_i) in
                       zip(y2, [cp.predict_interval(pp, "clearance") for pp in p2])])
    print(f"empirical coverage: {covered:.3f} (target >= 0.95)")
    ps = cp.prediction_set(0.8, "tox21")
    print(f"tox21 prediction set for p=0.8: {ps['set']} ambiguous={ps['ambiguous']}")
    print(f"calibration hash: {cp.calibration_hash()}")
