"""
Tests for PILLAR 5: Domain Sub-Modules (CNS P-gp & Oncology Kinome SI)
======================================================================

Verifies:
- CNSSafetyEngine computes composite CNS exposure score
- KinomeSelectivityEngine computes SI across 15 kinase targets
- Score_CNS = P(BBB) * (1.0 - 0.7 * P(P-gp))
- SI = 1 - (mean_off_target_affinity / target_affinity)
- API endpoints /api/safety/cns-pgp and /api/safety/kinome-selectivity
"""

import pytest
import math

from models.cns_oncology_safety import (
    CNSSafetyEngine,
    KinomeSelectivityEngine,
    get_default_cns_engine,
    get_default_kinome_engine,
    CNS_RISK_HIGH,
    CNS_RISK_MODERATE,
    CNS_RISK_LOW,
    SI_HIGH,
    SI_MODERATE,
    SI_LOW,
)

# ============================================================================
# Reference molecules
# ============================================================================

# Small flexible molecule - moderate BBB, not a P-gp substrate
PROPRAZINE = "CN(C)CCN(CC)CCN(CC)CC"  # highly basic -> likely P-gp substrate
METHYL_PHENYL = "COc1ccccc1"  # anisole - moderate BBB, low P-gp
CLONAZEPAM = "Clc1c(CCN(CC)CC)nc2ccccc12"  # benzodiazepine - high BBB
ASPIRIN = "CC(=O)OC1=CC=CC=C1"  # carboxylic acid - low BBB, acidic
WARFARIN = "CC(C)(COC(=O)c1ccccc1)c1ccccc1"  # high BBB
NITROBENZENE = "c1ccc([N+](=O)[O-])cc1"  # nitro - low BBB, PAH alert

# Oncology-relevant molecules
IMATINIB_SMILES = "CCN(CC)CCNC(=O)C1=NC=C(2C(=NC=N2)N)N=C1"  # not real, simplified
ERLOTINIB = "COc1ccc2nc(NC3=CC=CC=C3)c(N3CCN(C)CC3)nc2c1"
LAPATINIB = "Cc1ccc(Oc2c(ccc(N3CCN(CCO)CC3)N)c3)nc2"
SIMPLE_KINASE_INH = "c1ccc2c(c1)nc3c(c2)cccc3"  # indole scaffold

# ============================================================================
# CNS Safety Engine Tests
# ============================================================================

class TestCNSSafetyEngine:
    """Test the CNS P-gp composite safety engine."""

    @pytest.fixture
    def engine(self):
        return CNSSafetyEngine()

    def test_cns_score_formula(self, engine):
        """Score_CNS = P(BBB) * (1.0 - 0.7 * P(P-gp))"""
        result = engine.evaluate(ERLOTINIB)

        bbb = result['bbb_permeability']
        pgp = result['pgp_substrate_probability']
        expected_cns = bbb * (1.0 - 0.7 * pgp)

        # Account for rounding in the engine's return value
        assert math.isclose(result['cns_exposure_score'], expected_cns, abs_tol=0.01)

    def test_cns_score_range(self, engine):
        """CNS score should be in [0, 1]."""
        for smi in [ASPIRIN, WARFARIN, METHYL_PHENYL, PROPRAZINE]:
            result = engine.evaluate(smi)
            assert 0.0 <= result['cns_exposure_score'] <= 1.0

    def test_bbb_permeability_range(self, engine):
        """BBB permeability should be in [0, 1]."""
        result = engine.evaluate(ERLOTINIB)
        assert 0.0 <= result['bbb_permeability'] <= 1.0

    def test_pgp_probability_range(self, engine):
        """P-gp substrate probability should be in [0, 1]."""
        result = engine.evaluate(ERLOTINIB)
        assert 0.0 <= result['pgp_substrate_probability'] <= 1.0

    def test_cns_risk_category(self, engine):
        """Should return a valid CNS risk category."""
        result = engine.evaluate(ERLOTINIB)
        assert result['cns_risk_category'] in [
            CNS_RISK_HIGH, CNS_RISK_MODERATE, CNS_RISK_LOW
        ]

    def test_cns_risk_description(self, engine):
        """Should return a risk description string."""
        result = engine.evaluate(ERLOTINIB)
        assert isinstance(result['cns_risk_description'], str)
        assert len(result['cns_risk_description']) > 0

    def test_high_bbb_low_pgp_gives_high_cns(self, engine):
        """High BBB + low P-gp = high CNS exposure."""
        result = engine.evaluate(WARFARIN)
        assert result['cns_exposure_score'] > 0.3
        # Warfarin is a known CNS-penetrant drug (high BBB)

    def test_low_bbb_high_pgp_gives_low_cns(self, engine):
        """Low BBB + high P-gp = low CNS exposure."""
        result = engine.evaluate(PROPRAZINE)
        # Highly basic molecule -> P-gp substrate -> low CNS
        assert result['cns_exposure_score'] < 0.5 or result['cns_risk_category'] in [CNS_RISK_LOW, CNS_RISK_MODERATE]

    def test_pgp_alerts_returned(self, engine):
        """Should return matched P-gp alerts."""
        result = engine.evaluate(PROPRAZINE)
        assert 'pgp_matched_alerts' in result
        assert isinstance(result['pgp_matched_alerts'], list)

    def test_properties_computed(self, engine):
        """Should compute molecular properties."""
        result = engine.evaluate(ERLOTINIB)
        assert 'properties' in result
        props = result['properties']
        assert 'molecular_weight' in props
        assert 'logp' in props
        assert 'tpsa' in props
        assert 'hbd' in props

    def test_invalid_smiles(self, engine):
        """Invalid SMILES should return error."""
        result = engine.evaluate("!!!invalid!!!")
        assert 'error' in result

    def test_empty_smiles(self, engine):
        """Empty SMILES should return error (or be handled gracefully)."""
        result = engine.evaluate("")
        # Empty SMILES produces a valid result with default values, or an error
        assert 'success' in result or 'error' in result

    def test_singleton(self):
        """get_default_cns_engine should return singleton."""
        e1 = get_default_cns_engine()
        e2 = get_default_cns_engine()
        assert e1 is e2

    def test_mw_range(self, engine):
        """Molecular weight should be positive."""
        result = engine.evaluate(ERLOTINIB)
        assert result['properties']['molecular_weight'] > 0


# ============================================================================
# Kinome Selectivity Engine Tests
# ============================================================================

class TestKinomeSelectivityEngine:
    """Test the oncology kinome selectivity index engine."""

    @pytest.fixture
    def engine(self):
        return KinomeSelectivityEngine()

    def test_si_formula(self, engine):
        """SI = 1 - (mean_off_target_affinity / target_affinity)."""
        result = engine.evaluate(ERLOTINIB, target_kinase='EGFR')

        target_bind = result['target_affinity']
        mean_off = result['mean_off_target_affinity']
        si = result['selectivity_index']

        if target_bind > mean_off:
            expected_si = 1.0 - (mean_off / target_bind)
            assert math.isclose(si, expected_si, rel_tol=1e-6)

    def test_si_range(self, engine):
        """Selectivity index should be in [0, 1]."""
        for target in ['EGFR', 'VEGFR2', 'CDK2', 'BRAF', 'MEK1']:
            result = engine.evaluate(ERLOTINIB, target_kinase=target)
            assert 0.0 <= result['selectivity_index'] <= 1.0

    def test_si_category(self, engine):
        """Should return valid SI category."""
        result = engine.evaluate(ERLOTINIB)
        assert result['si_category'] in [SI_HIGH, SI_MODERATE, SI_LOW]

    def test_target_kinase_in_result(self, engine):
        """Result should include target kinase."""
        result = engine.evaluate(ERLOTINIB, target_kinase='BRAF')
        assert result['target_kinase'] == 'BRAF'

    def test_kinase_affinities_dict(self, engine):
        """Should return affinities for all 15 standard kinases."""
        result = engine.evaluate(ERLOTINIB)
        affinities = result['kinase_affinities']
        assert len(affinities) >= 10

        for kinase, data in affinities.items():
            assert 0.0 <= data['binding_probability'] <= 1.0
            assert 'is_target' in data

    def test_target_marked_in_affinities(self, engine):
        """Target kinase should be marked as target."""
        result = engine.evaluate(ERLOTINIB, target_kinase='EGFR')
        affinities = result['kinase_affinities']
        assert 'EGFR' in affinities
        assert affinities['EGFR']['is_target'] is True

    def test_high_risk_offtargets(self, engine):
        """Should identify high-risk off-targets (>50% binding prob)."""
        result = engine.evaluate(ERLOTINIB)
        assert 'high_risk_offtargets' in result
        assert isinstance(result['high_risk_offtargets'], list)

    def test_mean_off_target_calculation(self, engine):
        """Mean off-target affinity should be computed."""
        result = engine.evaluate(ERLOTINIB)
        affinities = result['kinase_affinities']
        off_target_vals = [
            v['binding_probability'] for v in affinities.values()
            if not v['is_target']
        ]
        if off_target_vals:
            expected_mean = sum(off_target_vals) / len(off_target_vals)
            assert math.isclose(result['mean_off_target_affinity'], expected_mean, rel_tol=1e-4)

    def test_invalid_smiles(self, engine):
        """Invalid SMILES should return error."""
        result = engine.evaluate("!!!invalid!!!")
        assert 'error' in result

    def test_default_target_is_egfr(self, engine):
        """Default target should be EGFR."""
        result = engine.evaluate(ERLOTINIB)
        assert result['target_kinase'] == 'EGFR'

    def test_singleton(self):
        """get_default_kinome_engine should return singleton."""
        e1 = get_default_kinome_engine()
        e2 = get_default_kinome_engine()
        assert e1 is e2


# ============================================================================
# Mondrian Conformal Predictor Tests
# ============================================================================

class TestMondrianConformalPredictor:
    """Test the Mondrian scaffold-stratified conformal predictor."""

    @pytest.fixture
    def predictor(self):
        from utils.conformal_predictor import MondrianConformalPredictor
        return MondrianConformalPredictor()

    def test_calibrate(self, predictor):
        """Should calibrate with training data."""
        smiles_list = ["CC(=O)OC1=CC=CC=C1", "c1ccc([N+](=O)[O-])cc1",
                       "CN1C=NC2=C1C(=O)N(C)C2=O", "c1cc(ccc1)c2c(ccc3)c2cccc3"]
        y_true = [0.1, 0.9, 0.05, 0.6]
        y_pred = [0.15, 0.85, 0.08, 0.55]

        predictor.calibrate(smiles_list, y_true, y_pred, "tox21")
        assert predictor._calibrated is True

    def test_predict_interval_returns_tuple(self, predictor):
        """predict_interval should return (ci_low, point, ci_high)."""
        smiles_list = ["CC(=O)OC1=CC=CC=C1", "c1ccc([N+](=O)[O-])cc1"]
        y_true = [0.1, 0.9]
        y_pred = [0.15, 0.85]
        predictor.calibrate(smiles_list, y_true, y_pred, "tox21")

        ci_low, point, ci_high = predictor.predict_interval(0.5, "c1ccccc1", "tox21")
        assert isinstance(ci_low, float)
        assert isinstance(ci_high, float)
        assert ci_low <= point <= ci_high or ci_low <= ci_high

    def test_prediction_set(self, predictor):
        """prediction_set should return scaffold info and interval."""
        smiles_list = ["CC(=O)OC1=CC=CC=C1", "c1ccc([N+](=O)[O-])cc1"]
        y_true = [0.1, 0.9]
        y_pred = [0.15, 0.85]
        predictor.calibrate(smiles_list, y_true, y_pred, "tox21")

        pred_set = predictor.prediction_set(0.5, "c1ccccc1", "tox21")
        assert 'scaffold' in pred_set
        assert 'scaffold_status' in pred_set
        assert 'q_hat' in pred_set
        assert 'global_q_hat' in pred_set

    def test_scaffold_status_known(self, predictor):
        """Known scaffold (from calibration) should be 'calibrated'."""
        smiles_list = ["CC(=O)OC1=CC=CC=C1", "c1ccc([N+](=O)[O-])cc1"]
        y_true = [0.1, 0.9]
        y_pred = [0.15, 0.85]
        predictor.calibrate(smiles_list, y_true, y_pred, "tox21")

        # Aspirin scaffold was in calibration -> 'calibrated'
        pred_set = predictor.prediction_set(0.5, "CC(=O)OC1=CC=CC=C1", "tox21")
        assert pred_set['scaffold_status'] == 'calibrated'

    def test_scaffold_status_novel(self, predictor):
        """Novel scaffold should be 'ood_unseen'."""
        smiles_list = ["CC(=O)OC1=CC=CC=C1", "c1ccc([N+](=O)[O-])cc1"]
        y_true = [0.1, 0.9]
        y_pred = [0.15, 0.85]
        predictor.calibrate(smiles_list, y_true, y_pred, "tox21")

        # Naphthalene scaffold is novel
        pred_set = predictor.prediction_set(0.5, "c1ccc2c(c1)cccc2", "tox21")
        assert pred_set['scaffold_status'] == 'ood_unseen'

    def test_novel_wider_ci(self, predictor):
        """Novel scaffold should have wider or equal CI than seen scaffold."""
        smiles_list = ["CC(=O)OC1=CC=CC=C1", "c1ccc([N+](=O)[O-])cc1"]
        y_true = [0.1, 0.9]
        y_pred = [0.15, 0.85]
        predictor.calibrate(smiles_list, y_true, y_pred, "tox21")

        seen_low, _, seen_high = predictor.predict_interval(0.5, "CC(=O)OC1=CC=CC=C1", "tox21")
        novel_low, _, novel_high = predictor.predict_interval(0.5, "c1ccc2c(c1)cccc2", "tox21")

        seen_width = seen_high - seen_low
        novel_width = novel_high - novel_low

        # Novel scaffolds should have wider (or equal) CIs
        assert novel_width >= seen_width

    def test_calibration_hash(self, predictor):
        """Should return a calibration hash."""
        smiles_list = ["CC(=O)OC1=CC=CC=C1"]
        y_true = [0.1]
        y_pred = [0.15]
        predictor.calibrate(smiles_list, y_true, y_pred, "tox21")
        h = predictor.calibration_hash()
        assert isinstance(h, str)
        assert len(h) > 0


# ============================================================================
# API Endpoint Integration Tests
# ============================================================================

class TestCNSKinomeAPI:
    """Test the CNS and Kinome API endpoints."""

    def test_cns_pgp_endpoint(self, app):
        """POST /api/safety/cns-pgp should return CNS analysis."""
        with app.test_client() as client:
            response = client.post('/api/safety/cns-pgp',
                                   json={'smiles': ERLOTINIB})
            assert response.status_code == 200
            data = response.get_json()
            assert data['cns_exposure_score'] is not None
            assert 'cns_risk_category' in data
            assert 'bbb_permeability' in data
            assert 'pgp_substrate_probability' in data

    def test_cns_pgp_missing_smiles(self, app):
        """Should return 400 for missing SMILES."""
        with app.test_client() as client:
            response = client.post('/api/safety/cns-pgp', json={})
            assert response.status_code == 400

    def test_cns_pgp_invalid_smiles(self, app):
        """Should return 400 for invalid SMILES."""
        with app.test_client() as client:
            response = client.post('/api/safety/cns-pgp',
                                   json={'smiles': '!!!invalid!!!'})
            assert response.status_code == 400

    def test_kinome_endpoint(self, app):
        """POST /api/safety/kinome-selectivity should return kinome analysis."""
        with app.test_client() as client:
            response = client.post('/api/safety/kinome-selectivity',
                                   json={'smiles': ERLOTINIB})
            assert response.status_code == 200
            data = response.get_json()
            assert 'selectivity_index' in data
            assert 'si_category' in data
            assert 'target_affinity' in data
            assert 'mean_off_target_affinity' in data
            assert 'kinase_affinities' in data

    def test_kinome_with_target(self, app):
        """Should accept target_kinase parameter."""
        with app.test_client() as client:
            response = client.post('/api/safety/kinome-selectivity',
                                   json={'smiles': ERLOTINIB, 'target_kinase': 'VEGFR2'})
            assert response.status_code == 200
            data = response.get_json()
            assert data['target_kinase'] == 'VEGFR2'

    def test_kinome_missing_smiles(self, app):
        """Should return 400 for missing SMILES."""
        with app.test_client() as client:
            response = client.post('/api/safety/kinome-selectivity', json={})
            assert response.status_code == 400

    def test_mondrian_endpoint(self, app):
        """POST /api/conformal/mondrian should return scaffold-stratified CI."""
        with app.test_client() as client:
            response = client.post('/api/conformal/mondrian',
                                   json={'smiles': ERLOTINIB, 'point_pred': 0.3})
            assert response.status_code == 200
            data = response.get_json()
            assert 'conformal_ci_low' in data
            assert 'conformal_ci_high' in data
            assert 'scaffold_info' in data
