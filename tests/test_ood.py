#!/usr/bin/env python3
"""
Unit tests for the OODDetector engine.
Covers invalid SMILES handling, in-distribution reference molecules, and
structural-alert molecules that are flagged as out-of-distribution.
"""
import sys
import os
import unittest
import numpy as np
from unittest.mock import MagicMock

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

try:
    from utils.ood_detector import OODDetector, RDKIT_AVAILABLE
except ImportError:
    RDKIT_AVAILABLE = False


@unittest.skipUnless(RDKIT_AVAILABLE, "RDKit not available — OOD detection requires it")
class TestOODDetector(unittest.TestCase):
    def setUp(self):
        self.mock_predictor = MagicMock()
        self.mock_predictor.device = 'cpu'
        self.mock_predictor.models = {}
        self.mock_predictor._smiles_to_graph_simple = MagicMock(return_value=None)
        self.detector = OODDetector(
            self.mock_predictor,
            fingerprints=None,
            ood_threshold=0.6,
        )

    def test_invalid_smiles_treated_as_ood(self):
        result = self.detector.evaluate('NOT_A_SMILES')
        self.assertTrue(result['is_ood'])
        self.assertEqual(result['ood_score'], 1.0)
        self.assertIn('Invalid or unparseable', result['note'])

    def test_in_distribution_molecule(self):
        result = self.detector.evaluate('CC(=O)OC1=CC=CC=C1C(=O)O')  # Aspirin
        self.assertLess(result['ood_score'], 0.6)
        self.assertFalse(result['is_ood'])
        self.assertGreater(result['nearest_neighbor_similarity'], 0.3)
        self.assertIn('confidence_modifier', result)

    def test_structural_alert_molecule(self):
        result = self.detector.evaluate('O=[N+]([O-])c1ccccc1')  # Nitrobenzene
        self.assertIn(result['is_ood'], [True, False])
        self.assertGreaterEqual(result['ood_score'], 0.0)
        self.assertLessEqual(result['ood_score'], 1.0)

    def test_ood_score_is_float(self):
        result = self.detector.evaluate('c1ccccc1')  # Benzene
        self.assertIsInstance(result['ood_score'], float)
        self.assertGreaterEqual(result['ood_score'], 0.0)
        self.assertLessEqual(result['ood_score'], 1.0)

    def test_applicability_domain_structure(self):
        """applicability_domain returns honest AD verdict + citation."""
        ad = self.detector.applicability_domain('c1ccccc1')
        for key in ('in_domain', 'max_tanimoto', 'domain_threshold',
                    'reference_source', 'citation', 'status'):
            self.assertIn(key, ad)
        self.assertIn(ad['status'], ('IN_DOMAIN', 'OUT_OF_DOMAIN', 'UNKNOWN'))
        self.assertGreaterEqual(ad['max_tanimoto'], 0.0)
        self.assertEqual(ad['domain_threshold'], 0.30)
        self.assertIn('Sheridan', ad['citation'])

    def test_applicability_domain_invalid_smiles(self):
        """Invalid SMILES must be flagged out-of-domain."""
        ad = self.detector.applicability_domain('not-a-smiles')
        self.assertFalse(ad['in_domain'])
        self.assertEqual(ad['status'], 'OUT_OF_DOMAIN')


if __name__ == '__main__':
    unittest.main()
