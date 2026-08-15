#!/usr/bin/env python3
"""
TriageEngine — Integrated Risk Triage for PharmaGuard AI
=========================================================

Combines multiple evidence streams into a single, auditable risk decision:

    Safety Risk Score = w1 * Toxicity
                      + w2 * ADMET failures
                      + w3 * Prediction uncertainty
                      + w4 * OOD risk
                      + w5 * Explanation unreliability

and maps the result to a triage category:

    GREEN  → Low concern / Candidate
    YELLOW → Review needed / Medium risk
    RED    → High concern / High toxicity

The engine deliberately does NOT collapse everything into a single opaque
number for the UI; it returns the component contributions so the frontend can
show a transparent, multi-dimensional risk picture.

Author: PharmaGuard AI Team
"""

import logging
import numpy as np
from typing import Dict, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('TriageEngine')


# Endpoint groupings (consistent with the rest of the platform)
TOXICITY_ENDPOINTS = ['tox21', 'clintox']
ADMET_ENDPOINTS = ['bbbp', 'caco2', 'clearance', 'hlm_clint']


class TriageEngine:
    """Compute a unified safety risk score and triage category."""

    def __init__(
        self,
        w_toxicity: float = 0.40,
        w_admet: float = 0.20,
        w_uncertainty: float = 0.15,
        w_ood: float = 0.15,
        w_explanation: float = 0.10,
        green_threshold: float = 0.30,
        red_threshold: float = 0.50
    ):
        """
        Args:
            w_*: component weights (auto-normalized in ``triage``).
            green_threshold / red_threshold: score cutoffs for triage category.
        """
        self.w_toxicity = w_toxicity
        self.w_admet = w_admet
        self.w_uncertainty = w_uncertainty
        self.w_ood = w_ood
        self.w_explanation = w_explanation
        self.green_threshold = green_threshold
        self.red_threshold = red_threshold

    # ─────────────────────────────────────────────────────────────────────
    # Component extractors
    # ─────────────────────────────────────────────────────────────────────
    def _extract_toxicity(self, prediction_result: Dict[str, Any]) -> float:
        """Max endpoint toxicity probability (0-1)."""
        probs = []
        preds = (prediction_result.get('predictions') or
                 prediction_result.get('tox21') or {})
        if isinstance(preds, dict):
            for v in preds.values():
                if isinstance(v, dict) and 'probability' in v:
                    probs.append(float(v['probability']))
        if 'summary' in prediction_result:
            avg = prediction_result['summary'].get('average_toxicity_probability')
            if avg is not None:
                probs.append(float(avg))
        return float(max(probs)) if probs else 0.0

    def _extract_admet_failure(self, prediction_result: Dict[str, Any]) -> float:
        """Fraction of ADMET endpoints in an unfavourable regime (0-1).

        BBBP: high penetration flagged as a (distribution) risk for tox.
        Caco-2 / Clearance / HLM: poor/very-high values flagged.
        """
        failures = 0
        total = 0
        preds = prediction_result.get('predictions', {})
        if not isinstance(preds, dict):
            return 0.0
        for ep, v in preds.items():
            if ep not in ADMET_ENDPOINTS or not isinstance(v, dict):
                continue
            total += 1
            prob = v.get('probability')
            if prob is None:
                continue
            prob = float(prob)
            if ep == 'bbbp':
                # High BBB penetration => higher CNS exposure risk
                if prob > 0.7:
                    failures += 1
            elif ep in ('caco2', 'clearance', 'hlm_clint'):
                # Poor absorption or extreme clearance
                if prob < 0.3 or prob > 0.85:
                    failures += 1
        return failures / total if total else 0.0

    def _extract_uncertainty(self, prediction_result: Dict[str, Any],
                             ood: Optional[Dict[str, Any]]) -> float:
        """Prediction uncertainty proxy (0-1).

        Combines distance-from-decision-boundary (max prob near 0.5 is most
        uncertain) with OOD risk.
        """
        tox = self._extract_toxicity(prediction_result)
        # Closeness to 0.5 => max aleatoric ambiguity
        boundary_unc = 1.0 - abs(tox - 0.5) * 2.0
        boundary_unc = float(np.clip(boundary_unc, 0.0, 1.0))
        ood_risk = 0.0
        if isinstance(ood, dict):
            ood_risk = float(ood.get('ood_score', 0.0))
        return float(np.clip(0.5 * boundary_unc + 0.5 * ood_risk, 0.0, 1.0))

    def _extract_ood(self, ood: Optional[Dict[str, Any]]) -> float:
        if isinstance(ood, dict):
            return float(ood.get('ood_score', 0.0))
        return 0.0

    def _extract_explanation_unreliability(
        self, explanation: Optional[Dict[str, Any]]
    ) -> float:
        """1 - faithfulness score (0 = fully reliable, 1 = rejected)."""
        if not isinstance(explanation, dict):
            return 0.0
        score = explanation.get('faithfulness_score')
        if score is None:
            return 0.0
        return float(np.clip(1.0 - float(score), 0.0, 1.0))

    # ─────────────────────────────────────────────────────────────────────
    # Main entry
    # ─────────────────────────────────────────────────────────────────────
    def triage(
        self,
        prediction_result: Dict[str, Any],
        ood: Optional[Dict[str, Any]] = None,
        toxicity_override: Optional[float] = None,
        explanation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Return a structured triage decision.

        Returns keys: category, risk_score, components, recommendation,
        disclaimer.
        """
        tox = (toxicity_override
               if toxicity_override is not None
               else self._extract_toxicity(prediction_result))
        admet = self._extract_admet_failure(prediction_result)
        uncertainty = self._extract_uncertainty(prediction_result, ood)
        ood_risk = self._extract_ood(ood)
        exp_unrel = self._extract_explanation_unreliability(explanation)

        weights = {
            'toxicity': self.w_toxicity,
            'admet': self.w_admet,
            'uncertainty': self.w_uncertainty,
            'ood': self.w_ood,
            'explanation': self.w_explanation
        }
        wsum = sum(weights.values())

        # Weighted average of all five evidence streams (transparent components).
        weighted_avg = (
            weights['toxicity'] * tox +
            weights['admet'] * admet +
            weights['uncertainty'] * uncertainty +
            weights['ood'] * ood_risk +
            weights['explanation'] * exp_unrel
        ) / wsum

        # Aggravating-stream average (everything except raw toxicity): this lets
        # uncertainty / OOD / explanation unreliability push an otherwise
        # borderline molecule toward review without diluting the toxicity signal.
        agg_weights = {k: v for k, v in weights.items() if k != 'toxicity'}
        agg_sum = sum(agg_weights.values())
        aggravators = (
            agg_weights['admet'] * admet +
            agg_weights['uncertainty'] * uncertainty +
            agg_weights['ood'] * ood_risk +
            agg_weights['explanation'] * exp_unrel
        ) / agg_sum if agg_sum > 0 else 0.0

        # Final score: toxicity is the primary safety driver (0.6), with
        # aggravating evidence contributing the remaining 0.4. This guarantees
        # a highly toxic molecule is flagged RED even when other streams are
        # neutral, while non-toxic molecules stay GREEN.
        risk_score = float(np.clip(0.6 * tox + 0.4 * aggravators, 0.0, 1.0))

        if risk_score >= self.red_threshold:
            category = 'RED'
            recommendation = 'HIGH PRIORITY FOR EXPERT REVIEW'
        elif risk_score >= self.green_threshold:
            category = 'YELLOW'
            recommendation = 'REVIEW NEEDED — MEDIUM RISK'
        else:
            category = 'GREEN'
            recommendation = 'LOW CONCERN — CANDIDATE'

        return {
            'category': category,
            'risk_score': round(risk_score, 4),
            'components': {
                'toxicity': round(tox, 4),
                'admet_failure': round(admet, 4),
                'uncertainty': round(uncertainty, 4),
                'ood_risk': round(ood_risk, 4),
                'explanation_unreliability': round(exp_unrel, 4)
            },
            'weights': {k: round(v / wsum, 4) for k, v in weights.items()},
            'recommendation': recommendation,
            'disclaimer': ('Computational decision-support screening only. '
                           'Not a substitute for experimental toxicology, '
                           'clinical evaluation, or regulatory review.')
        }


if __name__ == "__main__":
    print("Testing TriageEngine...")
    print("=" * 60)
    eng = TriageEngine()
    pred = {
        'predictions': {'tox21': {'probability': 0.87}, 'bbbp': {'probability': 0.82}},
        'summary': {'average_toxicity_probability': 0.87}
    }
    ood = {'ood_score': 0.1, 'is_ood': False}
    print("High-toxicity example:", eng.triage(pred, ood))
    pred2 = {'predictions': {'tox21': {'probability': 0.12}}, 'summary': {}}
    print("Low-toxicity example:", eng.triage(pred2, {'ood_score': 0.05}))
    print("\n✅ TriageEngine ready!")
