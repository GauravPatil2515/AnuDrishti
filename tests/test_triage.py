#!/usr/bin/env python3
"""
Unit tests for the TriageEngine.
Verifies GREEN / YELLOW / RED categorisation across low, medium, and high
toxicity scenarios, and checks that component extraction is transparent.
"""
import sys
import os
import unittest

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from utils.triage_engine import TriageEngine


class TestTriageEngine(unittest.TestCase):
    def setUp(self):
        self.engine = TriageEngine()

    def test_low_toxicity_green(self):
        pred = {
            'predictions': {
                'tox21': {'probability': 0.05},
                'bbbp': {'probability': 0.30},
            },
            'summary': {'average_toxicity_probability': 0.05},
        }
        result = self.engine.triage(pred, ood={'ood_score': 0.05, 'is_ood': False},
                                    explanation={'faithfulness_score': 0.95})
        self.assertEqual(result['category'], 'GREEN')

    def test_high_toxicity_red(self):
        pred = {
            'predictions': {
                'tox21': {'probability': 0.95},
                'bbbp': {'probability': 0.85},
            },
            'summary': {'average_toxicity_probability': 0.95},
        }
        result = self.engine.triage(pred, ood={'ood_score': 0.1, 'is_ood': False},
                                    explanation={'faithfulness_score': 0.88})
        self.assertEqual(result['category'], 'RED')
        self.assertGreaterEqual(result['risk_score'], 0.50)

    def test_medium_toxicity_yellow(self):
        pred = {
            'predictions': {
                'tox21': {'probability': 0.50},
            },
            'summary': {'average_toxicity_probability': 0.50},
        }
        result = self.engine.triage(pred, ood={'ood_score': 0.2, 'is_ood': False},
                                    explanation={'faithfulness_score': 0.70})
        self.assertEqual(result['category'], 'YELLOW')
        self.assertGreaterEqual(result['risk_score'], 0.30)
        self.assertLess(result['risk_score'], 0.50)

    def test_explanation_unreliability_pushes_red(self):
        """Even low toxicity can be flagged RED when explanation is rejected."""
        pred = {
            'predictions': {'tox21': {'probability': 0.20}},
            'summary': {'average_toxicity_probability': 0.20},
        }
        result = self.engine.triage(
            pred,
            ood={'ood_score': 0.05, 'is_ood': False},
            explanation={'faithfulness_score': 0.05},
        )
        self.assertLessEqual(result['components']['toxicity'], 0.2)
        self.assertGreaterEqual(result['components']['explanation_unreliability'], 0.9)

    def test_disclaimer_present(self):
        pred = {'predictions': {}, 'summary': {'average_toxicity_probability': 0.1}}
        result = self.engine.triage(pred, ood=None)
        self.assertIn('Computational decision-support', result['disclaimer'])


if __name__ == '__main__':
    unittest.main()
