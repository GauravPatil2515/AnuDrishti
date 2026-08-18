#!/usr/bin/env python3
"""
Integration-style tests for the PharmaGuard batch analysis and demo endpoints.
Uses Flask test client + stubbed module-level globals so CI runs without models.
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestPharmaGuardEndpoints(unittest.TestCase):
    """Test the demo endpoint without requiring model initialization."""

    def _make_test_app(self):
        import importlib
        import routes.pharmaguard as pg_mod
        importlib.reload(pg_mod)

        from flask import Flask
        app = Flask(__name__)
        app.register_blueprint(pg_mod.pharmaguard_bp, url_prefix='/api')

        # Set module-level globals that init_pharmaguard() would normally populate.
        pg_mod.predictor = MagicMock()
        pg_mod.predictor.is_loaded = True
        pg_mod.triage_engine = MagicMock()
        pg_mod.ood_detector = MagicMock()
        pg_mod.faithfulness_validator = MagicMock()
        pg_mod.cache = MagicMock()
        return app, pg_mod

    def test_demo_endpoint(self):
        app, _ = self._make_test_app()
        client = app.test_client()
        resp = client.get('/api/demo')
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertTrue(data['demo'])
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 2)

        paracetamol, nitrobenzene = data['results']
        self.assertEqual(paracetamol['smiles'], 'CC(=O)NC1=CC=C(C=C1)O')
        self.assertEqual(paracetamol['triage']['category'], 'GREEN')
        self.assertEqual(nitrobenzene['smiles'], 'O=[N+]([O-])c1ccccc1')
        self.assertEqual(nitrobenzene['triage']['category'], 'RED')

        for rec in data['results']:
            self.assertIn('explanation', rec)
            self.assertIn('faithfulness_score', rec['explanation'])
            self.assertIn('triage', rec)
            self.assertIn('ood', rec)
            self.assertIn('uncertainty', rec)

    def test_demo_does_not_flag_as_live(self):
        app, _ = self._make_test_app()
        client = app.test_client()
        resp = client.get('/api/demo')
        data = resp.get_json()
        for rec in data['results']:
            self.assertFalse(rec['explanation'].get('llm_generated', True))
            self.assertTrue(rec['explanation']['faithfulness_details']['demo'])

    def test_batch_analyze_structure(self):
        """Verify batch endpoint accepts a list and returns expected keys."""
        app, pg_mod = self._make_test_app()
        client = app.test_client()

        with patch.object(pg_mod, '_build_pharmaguard_analysis') as mock_build:
            mock_build.return_value = {
                'smiles': 'CCO',
                'triage': {'category': 'GREEN', 'risk_score': 0.2},
                'toxicity_probability': 0.2,
            }
            # Use sync mode (default for small batches)
            resp = client.post('/api/analyze/batch', json={
                'smiles_list': ['CCO', 'c1ccccc1'],
                'include_explanation': False,
                'async': False,
            })
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data['total_processed'], 2)
        self.assertIn('results', data)

    def test_batch_rejects_invalid_input(self):
        """Batch endpoint should reject requests without smiles_list."""
        app, _ = self._make_test_app()
        client = app.test_client()
        resp = client.post('/api/analyze/batch', json={'foo': 'bar'})
        self.assertEqual(resp.status_code, 400)

    def test_batch_rejects_too_large(self):
        """Batch endpoint should reject lists over 1000 molecules."""
        app, _ = self._make_test_app()
        client = app.test_client()
        resp = client.post('/api/analyze/batch', json={
            'smiles_list': ['CCO'] * 1001,
        })
        self.assertEqual(resp.status_code, 400)
        self.assertIn('Maximum', resp.get_json()['error'])


if __name__ == '__main__':
    unittest.main()
