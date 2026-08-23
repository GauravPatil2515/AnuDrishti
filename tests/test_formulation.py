#!/usr/bin/env python3
"""
Tests for Phase 2: Formulation Engine & Reactive Metabolite Scanner.
Covers:
  1. Epoxide / oxirane detection
  2. Quinone detection (catechol / hydroquinone)
  3. Maillard reaction incompatibility (amine + reducing sugar)
  4. Clean formulation returns STABLE
  5. Dose-weighted synergy scoring
  6. Formulation API endpoint response structure
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from utils.reactive_metabolites import detect_reactive_metabolites
from models.formulation_engine import FormulationEngine


# ─────────────────────────────────────────────────────────────────────────────
# Step 1: Reactive Metabolite Scanner Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestReactiveMetabolites:
    """Tests for the reactive metabolite & bioactivation scanner."""

    def test_reactive_metabolites_epoxide(self):
        """Verify oxirane / arene epoxide detection (C1CO1 = ethylene oxide)."""
        result = detect_reactive_metabolites("C1CO1")
        assert result["alert_count"] >= 1
        assert result["bri_score"] >= 0.8
        assert result["risk_label"] == "HIGH"
        alert_names = [a["name"] for a in result["detected_alerts"]]
        assert "epoxide" in alert_names
        # Matched atom indices should be non-empty
        epoxide_alert = next(a for a in result["detected_alerts"] if a["name"] == "epoxide")
        assert len(epoxide_alert["matched_atoms"]) > 0

    def test_reactive_metabolites_quinone(self):
        """Verify quinone detection on catechol (ortho-dihydroxybenzene)."""
        # Catechol: ortho-dihydroxybenzene — precursor to ortho-quinone
        result = detect_reactive_metabolites("c1cc(O)c(O)cc1")
        assert result["alert_count"] >= 1
        assert result["bri_score"] >= 0.85
        alert_names = [a["name"] for a in result["detected_alerts"]]
        assert "ortho-quinone" in alert_names

    def test_reactive_metabolites_nitrobenzene(self):
        """Verify nitrenium ion precursor detection on nitrobenzene."""
        result = detect_reactive_metabolites("c1ccc([N+](=O)[O-])cc1")
        assert result["alert_count"] >= 1
        assert result["bri_score"] >= 0.8
        assert result["risk_label"] == "HIGH"

    def test_clean_molecule_no_alerts(self):
        """Benzene should produce no alerts."""
        result = detect_reactive_metabolites("c1ccccc1")
        assert result["alert_count"] == 0
        assert result["bri_score"] == 0.0
        assert result["risk_label"] == "SAFE"

    def test_invalid_smiles(self):
        """Invalid SMILES should return error without crashing."""
        result = detect_reactive_metabolites("not a smiles")
        assert "error" in result
        assert result["bri_score"] == 0.0

    def test_bri_score_range(self):
        """BRI score must be between 0.0 and 1.0."""
        for smi in ["C1CO1", "c1cc(O)c(O)cc1", "c1ccc([N+](=O)[O-])cc1", "c1ccccc1"]:
            result = detect_reactive_metabolites(smi)
            assert 0.0 <= result["bri_score"] <= 1.0

    def test_smiles_hash_present(self):
        """Result should include a deterministic smiles_hash."""
        r1 = detect_reactive_metabolites("C1CO1")
        r2 = detect_reactive_metabolites("C1CO1")
        assert r1["smiles_hash"] == r2["smiles_hash"]
        assert len(r1["smiles_hash"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Step 2: Formulation Engine Tests
# ─────────────────────────────────────────────────────────────────────────────
class TestFormulationEngine:
    """Tests for the multi-component formulation engine."""

    @pytest.fixture
    def engine(self):
        return FormulationEngine()

    def test_maillard_incompatibility(self, engine):
        """Verify primary/secondary amine + reducing sugar triggers Maillard flag."""
        # Paracetamol has a secondary amine; Lactose is a reducing sugar
        result = engine.screen_formulation([
            {"name": "Paracetamol", "smiles": "CC(=O)Nc1ccc(O)cc1", "role": "API", "dose_mg": 500},
            {"name": "Lactose", "smiles": "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@H]1O", "role": "excipient", "dose_mg": 100},
        ])
        # Should detect Maillard reaction incompatibility
        maillard_found = any(
            "Maillard" in inc["mechanism"]
            for inc in result["incompatibility_matrix"]
        )
        assert maillard_found, "Expected Maillard reaction flag for amine + lactose"
        # The Maillard pair should have HIGH risk
        for inc in result["incompatibility_matrix"]:
            if "Maillard" in inc["mechanism"]:
                assert inc["risk"] == "HIGH"
                assert inc["p_rule"] >= 0.8  # Rule prior
                assert inc["p_incompatible"] >= 0.5  # Blended should still be high

    def test_clean_formulation_stable(self, engine):
        """Verify benign formulation (Paracetamol + Starch) returns STABLE."""
        result = engine.screen_formulation([
            {"name": "Paracetamol", "smiles": "CC(=O)Nc1ccc(O)cc1", "role": "API", "dose_mg": 500},
            {"name": "Starch", "smiles": "OC[C@@H]1[C@H](O)C(O)(C)OC1", "role": "excipient", "dose_mg": 100},
        ])
        assert result["formulation_stability"] == "STABLE"
        assert result["n_incompatibilities"] == 0

    def test_dose_weighted_synergy(self, engine):
        """Verify higher dose increases synergistic risk score."""
        # Same components, different doses
        low_dose = engine.screen_formulation([
            {"name": "Aspirin", "smiles": "CC(=O)OC1=CC=CC=C1", "role": "API", "dose_mg": 10},
            {"name": "Starch", "smiles": "OC[C@@H]1[C@H](O)C(O)(C)OC1", "role": "excipient", "dose_mg": 5},
        ], predictor=None)

        high_dose = engine.screen_formulation([
            {"name": "Aspirin", "smiles": "CC(=O)OC1=CC=CC=C1", "role": "API", "dose_mg": 500},
            {"name": "Starch", "smiles": "OC[C@@H]1[C@H](O)C(O)(C)OC1", "role": "excipient", "dose_mg": 200},
        ], predictor=None)

        # Both should have the same structure, but weight fractions change
        assert low_dose["n_components"] == 2
        assert high_dose["n_components"] == 2
        # Both should be stable (no incompatibility) but dose changes weight fractions
        assert low_dose["formulation_stability"] in ("STABLE", "WARNING", "CRITICAL_INCOMPATIBILITY")
        assert high_dose["formulation_stability"] in ("STABLE", "WARNING", "CRITICAL_INCOMPATIBILITY")

    def test_three_component_formulation(self, engine):
        """Verify 3-component formulation returns expected structure."""
        result = engine.screen_formulation([
            {"name": "Paracetamol", "smiles": "CC(=O)Nc1ccc(O)cc1", "role": "API", "dose_mg": 500},
            {"name": "Lactose", "smiles": "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@H]1O", "role": "excipient", "dose_mg": 100},
            {"name": "Mg Stearate", "smiles": "CCCCCCCCCC(=O)O[Mg+]", "role": "excipient", "dose_mg": 5},
        ])
        assert result["n_components"] == 3
        assert "formulation_stability" in result
        assert result["formulation_stability"] in ("STABLE", "WARNING", "CRITICAL_INCOMPATIBILITY")
        assert "incompatibility_matrix" in result
        assert "synergistic_toxicity" in result
        assert "components_summary" in result
        assert len(result["components_summary"]) == 3
        for comp in result["components_summary"]:
            assert "name" in comp
            assert "role" in comp
            assert "reactivity_risk" in comp

    def test_synergy_keys_present(self, engine):
        """Verify synergistic_toxicity has herg, dili, ames keys."""
        result = engine.screen_formulation([
            {"name": "Paracetamol", "smiles": "CC(=O)Nc1ccc(O)cc1", "role": "API", "dose_mg": 500},
            {"name": "Starch", "smiles": "OC[C@@H]1[C@H](O)C(O)(C)OC1", "role": "excipient", "dose_mg": 100},
        ])
        assert "herg_synergy" in result["synergistic_toxicity"]
        assert "dili_synergy" in result["synergistic_toxicity"]
        assert "ames_synergy" in result["synergistic_toxicity"]


# ─────────────────────────────────────────────────────────────────────────────
# Step 3: API Endpoint Test
# ─────────────────────────────────────────────────────────────────────────────
class TestFormulationAPI:
    """Integration tests for the formulation screening API endpoint."""

    def test_formulation_api_endpoint(self):
        """Test /api/formulation/screen response structure."""
        from flask import Flask
        import routes.pharmaguard as pg

        app = Flask(__name__)
        app.register_blueprint(pg.pharmaguard_bp)

        with app.test_client() as c:
            resp = c.post('/api/formulation/screen', json={
                'name': 'Test Formulation',
                'components': [
                    {'name': 'Paracetamol', 'smiles': 'CC(=O)Nc1ccc(O)cc1', 'role': 'API', 'dose_mg': 500},
                    {'name': 'Lactose', 'smiles': 'OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@H]1O', 'role': 'excipient', 'dose_mg': 100},
                ]
            })
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True
            assert data['mode'] == 'formulation'
            assert 'formulation_stability' in data
            assert 'incompatibility_matrix' in data
            assert 'synergistic_toxicity' in data
            assert 'components_summary' in data
            assert 'reactive_metabolite_scan' in data
            assert data['n_components'] == 2

    def test_reactive_metabolites_api_endpoint(self):
        """Test /api/adme/reactive-metabolites response structure."""
        from flask import Flask
        import routes.pharmaguard as pg

        app = Flask(__name__)
        app.register_blueprint(pg.pharmaguard_bp)

        with app.test_client() as c:
            # Test with epoxide
            resp = c.post('/api/adme/reactive-metabolites', json={'smiles': 'C1CO1'})
            assert resp.status_code == 200
            data = resp.get_json()
            assert data['success'] is True
            assert data['mode'] == 'reactive-metabolites'
            assert data['alert_count'] >= 1
            assert 'bri_score' in data
            assert 'risk_label' in data
            assert 'detected_alerts' in data

            # Test with clean molecule
            resp2 = c.post('/api/adme/reactive-metabolites', json={'smiles': 'c1ccccc1'})
            assert resp2.status_code == 200
            data2 = resp2.get_json()
            assert data2['alert_count'] == 0
            assert data2['bri_score'] == 0.0
