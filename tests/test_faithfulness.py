#!/usr/bin/env python3
"""
Unit tests for the Faithfulness Validator engine.
"""
import sys
import os
import unittest
import numpy as np
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from models.faithfulness_validator import FaithfulnessValidator, ValidationResult

class TestFaithfulnessValidator(unittest.TestCase):
    def setUp(self):
        # Mock model and counterfactual generator
        self.mock_model = MagicMock()
        self.mock_cf_generator = MagicMock()
        
        self.validator = FaithfulnessValidator(
            model=self.mock_model,
            counterfactual_generator=self.mock_cf_generator,
            faithfulness_threshold=0.6,
            causal_drop_threshold=0.1,
            attention_threshold=0.1
        )

    def test_grounding_passed(self):
        # Mock explanation where attention meets threshold
        explanation = {
            'identified_toxicophores': [
                {
                    'name': 'nitro',
                    'smarts_pattern': '[N+](=O)[O-]',
                    'atom_indices': [0, 1, 2],
                    'importance': 0.8
                }
            ]
        }
        # Attention on all 3 atoms is 0.6 (avg 0.6 >= adaptive cutoff kappa/N = 0.5)
        attention_weights = np.array([0.6, 0.6, 0.6, 0.05])
        
        result = self.validator.test_grounding(explanation, attention_weights)
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.grounded_claims, 1)

    def test_grounding_failed(self):
        # Mock explanation where attention is below threshold
        explanation = {
            'identified_toxicophores': [
                {
                    'name': 'nitro',
                    'smarts_pattern': '[N+](=O)[O-]',
                    'atom_indices': [0, 1, 2],
                    'importance': 0.8
                }
            ]
        }
        # Attention is 0.05 (avg 0.05 < threshold 0.1)
        attention_weights = np.array([0.05, 0.05, 0.05, 0.05])
        
        result = self.validator.test_grounding(explanation, attention_weights)
        self.assertEqual(result.score, 0.0)
        self.assertEqual(result.grounded_claims, 0)

    def test_causal_consistency(self):
        explanation = {
            'identified_toxicophores': [
                {
                    'name': 'nitro',
                    'smarts_pattern': '[N+](=O)[O-]',
                    'atom_indices': [0, 1, 2],
                    'importance': 0.8
                }
            ]
        }
        
        # Mock generator returning a counterfactual
        mock_cf = MagicMock()
        mock_cf.modified_smiles = 'CCO'
        self.mock_cf_generator.generate_for_claimed_toxicophore.return_value = mock_cf
        
        # Mock _predict_smiles to return prediction with drop
        self.validator._predict_smiles = MagicMock(return_value=0.2)
        
        # original prediction is 0.5. drop is 0.5 - 0.2 = 0.3 >= causal_drop_threshold (0.1)
        result = self.validator.test_causal_consistency(
            explanation, 'SMILES', original_prediction=0.5
        )
        
        self.assertEqual(result.score, 1.0)
        self.assertEqual(result.passed_claims, 1)
        
        # original prediction is 0.5. prediction returns 0.45. drop is 0.05 < 0.1
        self.validator._predict_smiles.return_value = 0.45
        result2 = self.validator.test_causal_consistency(
            explanation, 'SMILES', original_prediction=0.5
        )
        self.assertEqual(result2.score, 0.0)
        self.assertEqual(result2.passed_claims, 0)

    def test_complete_validation(self):
        # Combined test
        explanation = {
            'identified_toxicophores': [
                {
                    'name': 'nitro',
                    'smarts_pattern': '[N+](=O)[O-]',
                    'atom_indices': [0, 1, 2],
                    'importance': 0.8
                }
            ]
        }
        
        # Setup causal consistency pass
        mock_cf = MagicMock()
        mock_cf.modified_smiles = 'CCO'
        self.mock_cf_generator.generate_for_claimed_toxicophore.return_value = mock_cf
        self.validator._predict_smiles = MagicMock(return_value=0.2)
        
        # Setup counterfactual sensitivity (will return 0.5 if not implemented/simplified)
        self.mock_cf_generator.generate_counterfactuals.return_value = []
        
        # Setup grounding pass
        attention_weights = np.array([0.15, 0.15, 0.15, 0.05])
        
        # Run validate
        score = self.validator.validate(
            explanation=explanation,
            smiles='SMILES',
            original_prediction=0.5,
            attention_weights=attention_weights,
            run_counterfactual_test=True
        )
        
        self.assertTrue(score.overall_score > 0.0)
        print(f"Overall Faithfulness score: {score.overall_score:.4f}")

if __name__ == '__main__':
    unittest.main()
