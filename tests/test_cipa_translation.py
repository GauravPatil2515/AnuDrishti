#!/usr/bin/env python3
"""
Tests for Phase 3: CiPA 3-Channel CardioTox, Species Translation & Regulatory PDF.

Covers:
  1. CiPA channel predictions (hERG, Nav1.5, Cav1.2) — reference compounds
  2. qNet and PRS computation with risk classification
  3. Conformal confidence intervals present and valid
  4. Species LD50 prediction (Rat, Mouse) with GHS categorization
  5. Allometric clearance scaling ordering (Mouse > Rat > Monkey > Dog > Human)
  6. HED / NOAEL / MOS computation
  7. NAMs justification string present and non-empty
  8. Reference compound risk classification parity
  9. Regulatory PDF generation and signature verification
  10. API endpoint response structure (Flask test client)
"""
import os
import re
import json
import glob
import pytest
from unittest.mock import MagicMock

from models.cipa_cardiotox import (
    CiPACardioToxEngine,
    get_default_cipa_engine,
)
from utils.species_translation import (
    SpeciesTranslationEngine,
    get_default_translation_engine,
    SPECIES_DB,
)
from services.regulatory_pdf import (
    RegulatoryPDFGenerator,
    get_default_pdf_generator,
    PDF_RULESET_VERSION,
    _compute_file_hash,
    _compute_signature,
)


# ───────────────────────────────────────────────────────────────────────────
# Step 1: CiPA Reference Compound Validation
# ───────────────────────────────────────────────────────────────────────────
class TestCipaReferenceCompounds:
    """Verify all 8 CiPA reference compounds produce correct risk classification."""

    @pytest.fixture
    def engine(self):
        return CiPACardioToxEngine()

    def test_all_reference_compounds(self, engine):
        """All reference compounds must match their expected risk classification."""
        refs = engine.reference_compounds
        results = {}
        for name, info in refs.items():
            result = engine.evaluate_molecule(info["smiles"])
            results[name] = result

        for name, info in refs.items():
            result = results[name]
            if "error" in result:
                pytest.fail(f"{name}: engine returned error: {result['error']}")
            assert result["risk_classification"] == info["risk"], (
                f"{name}: expected {info['risk']}, got {result['risk_classification']}"
            )

    def test_dofetilide_high_risk(self, engine):
        """Dofetilide — potent hERG blocker → HIGH_TORSADES_RISK."""
        result = engine.evaluate_molecule(engine.reference_compounds["dofetilide"]["smiles"])
        assert result["risk_classification"] == "HIGH_TORSADES_RISK"
        assert result["channels"]["herg_channel"]["probability"] > 0.5

    def test_cisapride_high_risk(self, engine):
        """Cisapride — potent hERG blocker → HIGH_TORSADES_RISK."""
        result = engine.evaluate_molecule(engine.reference_compounds["cisapride"]["smiles"])
        assert result["risk_classification"] == "HIGH_TORSADES_RISK"

    def test_verapamil_low_risk(self, engine):
        """Verapamil — multi-channel block (hERG + Cav1.2) → LOW_ARRHYTHMIC_RISK."""
        result = engine.evaluate_molecule(engine.reference_compounds["verapamil"]["smiles"])
        assert result["risk_classification"] == "LOW_ARRHYTHMIC_RISK"
        # Verapamil should have significant Cav1.2 block (>0.3)
        assert result["channels"]["cav12_channel"]["probability"] > 0.3

    def test_ranolazine_low_risk(self, engine):
        """Ranolazine — multi-channel block → LOW_ARRHYTHMIC_RISK."""
        result = engine.evaluate_molecule(engine.reference_compounds["ranolazine"]["smiles"])
        assert result["risk_classification"] == "LOW_ARRHYTHMIC_RISK"

    def test_aspirin_low_risk(self, engine):
        """Aspirin — clean molecule → LOW_ARRHYTHMIC_RISK."""
        result = engine.evaluate_molecule(engine.reference_compounds["aspirin"]["smiles"])
        assert result["risk_classification"] == "LOW_ARRHYTHMIC_RISK"
        assert result["channels"]["herg_channel"]["probability"] < 0.3

    def test_sotalol_high_risk(self, engine):
        """Sotalol — beta-blocker with primary amine, known hERG blocker → HIGH_TORSADES_RISK."""
        result = engine.evaluate_molecule(engine.reference_compounds["sotalol"]["smiles"])
        assert result["risk_classification"] == "HIGH_TORSADES_RISK"
        assert result["channels"]["herg_channel"]["probability"] > 0.4

    def test_nifedipine_low_risk(self, engine):
        """Nifedipine — dihydropyridine Ca channel blocker → LOW_ARRHYTHMIC_RISK."""
        result = engine.evaluate_molecule(engine.reference_compounds["nifedipine"]["smiles"])
        assert result["risk_classification"] == "LOW_ARRHYTHMIC_RISK"
        # Nifedipine should NOT trigger hERG basic_amine pattern
        assert result["channels"]["herg_channel"]["probability"] < 0.3


# ───────────────────────────────────────────────────────────────────────────
# Step 2: CiPA Channel Probabilities & Confidence Intervals
# ───────────────────────────────────────────────────────────────────────────
class TestCipaChannelPredictions:
    """Verify channel probability structure, ranges, and conf intervals."""

    @pytest.fixture
    def engine(self):
        return CiPACardioToxEngine()

    def test_all_three_channels(self, engine):
        """Result must contain hERG, Nav1.5, and Cav1.2 channel data."""
        result = engine.evaluate_molecule("c1ccccc1")
        assert "channels" in result
        assert "herg_channel" in result["channels"]
        assert "nav15_channel" in result["channels"]
        assert "cav12_channel" in result["channels"]

    def test_probability_range(self, engine):
        """All channel probabilities must be in [0, 1]."""
        result = engine.evaluate_molecule("CC(=O)OC1=CC=CC=C1")
        for ch_name, ch_data in result["channels"].items():
            prob = ch_data["probability"]
            assert 0.0 <= prob <= 1.0, f"{ch_name}: probability {prob} out of [0,1]"

    def test_conformal_ci_present(self, engine):
        """Each channel must have conformal_ci_low and conformal_ci_high."""
        result = engine.evaluate_molecule("CC(=O)OC1=CC=CC=C1")
        for ch_name, ch_data in result["channels"].items():
            assert "conformal_ci_low" in ch_data, f"{ch_name}: missing conformal_ci_low"
            assert "conformal_ci_high" in ch_data, f"{ch_name}: missing conformal_ci_high"
            assert ch_data["conformal_ci_low"] <= ch_data["probability"] <= ch_data["conformal_ci_high"] or \
                   ch_data["conformal_ci_low"] <= ch_data["conformal_ci_high"], \
                   f"{ch_name}: CI [{ch_data['conformal_ci_low']}, {ch_data['conformal_ci_high']}] invalid"

    def test_prs_in_valid_range(self, engine):
        """Proarrhythmic Risk Score must be in [0, 1]."""
        result = engine.evaluate_molecule("CC(=O)OC1=CC=CC=C1")
        prs = result["proarrhythmic_risk_score"]
        assert 0.0 <= prs <= 1.0

    def test_qnet_present(self, engine):
        """qNet (net charge carrier balance) must be present and a float."""
        result = engine.evaluate_molecule("CC(=O)OC1=CC=CC=C1")
        assert "q_net" in result
        assert isinstance(result["q_net"], (int, float))

    def test_risk_classification_valid(self, engine):
        """Risk classification must be one of the valid categories."""
        valid = {"LOW_ARRHYTHMIC_RISK", "INTERMEDIATE_MONITOR", "HIGH_TORSADES_RISK"}
        result = engine.evaluate_molecule("CC(=O)OC1=CC=CC=C1")
        assert result["risk_classification"] in valid

    def test_ghs_risk_flag_present(self, engine):
        """GHS risk flag must be present."""
        result = engine.evaluate_molecule("CC(=O)OC1=CC=CC=C1")
        assert "ghs_risk_flag" in result
        assert result["ghs_risk_flag"] in ("[GREEN]", "[YELLOW]", "[RED]")

    def test_model_version_present(self, engine):
        """Result must include model_version."""
        result = engine.evaluate_molecule("CC(=O)OC1=CC=CC=C1")
        assert "model_version" in result
        assert len(result["model_version"]) > 0

    def test_mechanistic_details(self, engine):
        """Result must include mechanistic interpretation."""
        result = engine.evaluate_molecule("CC(=O)OC1=CC=CC=C1")
        assert "mechanistic_details" in result

    def test_invalid_smiles(self, engine):
        """Invalid SMILES should return error."""
        result = engine.evaluate_molecule("not a smiles at all")
        assert "error" in result

    def test_singleton(self):
        """get_default_cipa_engine() must return the same instance."""
        e1 = get_default_cipa_engine()
        e2 = get_default_cipa_engine()
        assert e1 is e2


# ───────────────────────────────────────────────────────────────────────────
# Step 3: Species Translation — LD50 & GHS
# ───────────────────────────────────────────────────────────────────────────
class TestSpeciesTranslationLD50:
    """Tests for LD50 prediction and GHS categorization."""

    @pytest.fixture
    def engine(self):
        return SpeciesTranslationEngine()

    def test_ld50_prediction(self, engine):
        """LD50 results must have rat, mouse values and GHS categories."""
        result = engine.translate_molecule("CC(=O)OC1=CC=CC=C1")
        assert "ld50" in result
        ld50 = result["ld50"]
        assert "rat_ld50_mg_per_kg" in ld50
        assert "mouse_ld50_mg_per_kg" in ld50
        assert "rat_ghs_category" in ld50
        assert "mouse_ghs_category" in ld50
        assert ld50["rat_ld50_mg_per_kg"] > 0
        assert ld50["mouse_ld50_mg_per_kg"] > 0

    def test_ghs_category_structure(self, engine):
        """GHS category must have category, label, and color fields."""
        result = engine.translate_molecule("c1ccccc1")
        rat_cat = result["ld50"]["rat_ghs_category"]
        assert "category" in rat_cat
        assert "label" in rat_cat
        assert "color" in rat_cat
        assert rat_cat["category"] in ("I", "II", "III", "IV")

    def test_ld50_category_for_toxic(self, engine):
        """Nitrobenzene (moderately toxic) should be in a defined GHS category."""
        result = engine.translate_molecule("c1ccc([N+](=O)[O-])cc1")
        rat_cat = result["ld50"]["rat_ghs_category"]["category"]
        assert rat_cat in ("I", "II", "III", "IV")

    def test_human_clearance_override(self, engine):
        """Providing human_clearance should override predicted human CL."""
        result = engine.translate_molecule("c1ccccc1", human_clearance=5.0)
        assert result["clearance_ml_per_min_per_kg"]["human"] == 5.0

    def test_human_clearance_none(self, engine):
        """Without human_clearance, human CL should be a positive number."""
        result = engine.translate_molecule("c1ccccc1")
        assert result["clearance_ml_per_min_per_kg"]["human"] > 0


# ───────────────────────────────────────────────────────────────────────────
# Step 4: Species Translation — Allometric Scaling
# ───────────────────────────────────────────────────────────────────────────
class TestSpeciesTranslationScaling:
    """Tests for allometric PK scaling across species."""

    @pytest.fixture
    def engine(self):
        return SpeciesTranslationEngine()

    def test_species_coverage(self, engine):
        """All 5 species must be in the species DB."""
        result = engine.translate_molecule("c1ccccc1")
        cls = result["clearance_ml_per_min_per_kg"]
        for sp in ["human", "rat", "mouse", "dog", "monkey"]:
            assert sp in cls, f"Missing species: {sp}"

    def test_allometric_ordering(self, engine):
        """Clearance per kg should follow allometric scaling: Mouse > Rat > Monkey > Dog > Human."""
        result = engine.translate_molecule("CC(=O)OC1=CC=CC=C1")
        cls = result["clearance_ml_per_min_per_kg"]
        # By body weight: mouse(0.03) < rat(0.25) < monkey(3) < dog(10) < human(70)
        # CL/kg ∝ BW^(-0.25), so smaller = higher CL/kg
        assert cls["mouse"] > cls["rat"], f"Mouse ({cls['mouse']}) should be > Rat ({cls['rat']})"
        assert cls["rat"] > cls["monkey"], f"Rat ({cls['rat']}) should be > Monkey ({cls['monkey']})"
        assert cls["monkey"] > cls["dog"], f"Monkey ({cls['monkey']}) should be > Dog ({cls['dog']})"
        assert cls["dog"] > cls["human"], f"Dog ({cls['dog']}) should be > Human ({cls['human']})"

    def test_volume_of_distribution(self, engine):
        """Vd should be larger for larger species (proportional to BW)."""
        result = engine.translate_molecule("c1ccccc1")
        vds = result["volume_of_distribution_l"]
        # Vd ∝ BW, so human Vd > rat Vd
        assert vds["human"] > vds["rat"], f"Human Vd ({vds['human']}) should be > Rat Vd ({vds['rat']})"

    def test_all_species_positive(self, engine):
        """All clearance and Vd values must be positive."""
        result = engine.translate_molecule("c1ccccc1")
        for sp, cl in result["clearance_ml_per_min_per_kg"].items():
            assert cl > 0, f"Clearance for {sp} must be positive, got {cl}"
        for sp, vd in result["volume_of_distribution_l"].items():
            assert vd > 0, f"Vd for {sp} must be positive, got {vd}"


# ───────────────────────────────────────────────────────────────────────────
# Step 5: Species Translation — HED, NOAEL, NAMs
# ───────────────────────────────────────────────────────────────────────────
class TestSpeciesTranslationHED:
    """Tests for HED, NOAEL, and NAMs justification."""

    @pytest.fixture
    def engine(self):
        return SpeciesTranslationEngine()

    def test_hed_computation(self, engine):
        """HED, NOAEL, MOS must be computed when dose_mg is provided."""
        result = engine.translate_molecule("c1ccccc1", dose_mg=100)
        assert result["hed_mg"] is not None
        assert result["noael_mg"] is not None
        assert result["margin_of_safety"] is not None
        assert result["hed_mg"] > 0
        assert result["noael_mg"] > 0
        assert result["margin_of_safety"] > 0

    def test_hed_none_without_dose(self, engine):
        """HED/NOAEL/MOS should be None when dose_mg is not provided."""
        result = engine.translate_molecule("c1ccccc1")
        assert result["hed_mg"] is None
        assert result["noael_mg"] is None
        assert result["margin_of_safety"] is None

    def test_nams_justification_present(self, engine):
        """NAMs justification string must be present and non-empty."""
        result = engine.translate_molecule("CC(=O)OC1=CC=CC=C1")
        assert "nams_justification" in result
        assert len(result["nams_justification"]) > 50

    def test_nams_mentions_modernization_act(self, engine):
        """NAMs text should reference FDA Modernization Act."""
        result = engine.translate_molecule("CC(=O)OC1=CC=CC=C1")
        assert "Modernization" in result["nams_justification"]
        assert "NAMs" in result["nams_justification"]

    def test_model_hash_present(self, engine):
        """Model hash must be present and deterministic."""
        r1 = engine.translate_molecule("c1ccccc1")
        r2 = engine.translate_molecule("c1ccccc1")
        assert "model_hash" in r1
        assert r1["model_hash"] == r2["model_hash"]
        assert len(r1["model_hash"]) > 0

    def test_ruleset_version(self, engine):
        """Engine must report its ruleset version."""
        assert engine.ruleset_version == "v3.0.0"

    def test_invalid_smiles(self, engine):
        """Invalid SMILES should return error."""
        result = engine.translate_molecule("invalidsmiles")
        assert "error" in result


# ───────────────────────────────────────────────────────────────────────────
# Step 6: Regulatory PDF Generation & Signature Verification
# ───────────────────────────────────────────────────────────────────────────
class TestRegulatoryPDF:
    """Tests for 21 CFR Part 11 regulatory PDF generation and verification."""

    @pytest.fixture
    def cipa_engine(self):
        return CiPACardioToxEngine()

    @pytest.fixture
    def translator(self):
        return SpeciesTranslationEngine()

    @pytest.fixture
    def pdf_gen(self):
        return RegulatoryPDFGenerator()

    @pytest.fixture
    def sample_data(self, cipa_engine, translator):
        """Generate sample CiPA + Species data for PDF tests."""
        smiles = "CC(=O)OC1=CC=CC=C1"
        cipa = cipa_engine.evaluate_molecule(smiles)
        species = translator.translate_molecule(smiles, dose_mg=100)
        species["human_dose_mg"] = 100
        return cipa, species

    def test_pdf_generation(self, pdf_gen, sample_data):
        """PDF generation must produce a valid file with correct hash/signature."""
        cipa, species = sample_data
        path = pdf_gen.generate(cipa, species, batch_id="TEST", compound_name="aspirin")
        assert os.path.exists(path)
        assert os.path.getsize(path) > 1000  # At least 1KB
        # Clean up
        os.remove(path)
        # Remove directory if empty
        report_dir = os.path.join(os.getcwd(), "regulatory_reports")
        if os.path.isdir(report_dir) and not os.listdir(report_dir):
            os.rmdir(report_dir)

    def test_pdf_file_hash_deterministic(self, pdf_gen, sample_data):
        """File hash must be deterministic for same inputs."""
        cipa, species = sample_data
        h1 = _compute_file_hash(cipa, species, "2024-01-01T00:00:00Z", "BATCH1", "TestCompound")
        h2 = _compute_file_hash(cipa, species, "2024-01-01T00:00:00Z", "BATCH1", "TestCompound")
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex length

    def test_pdf_signature_verification(self, pdf_gen, sample_data):
        """Generated PDF must pass signature verification."""
        cipa, species = sample_data
        path = pdf_gen.generate(cipa, species, batch_id="TEST", compound_name="aspirin")
        result = pdf_gen.verify_signature(path)
        assert result["valid"] is True
        assert result["file_hash_match"] is True
        assert result["signature_match"] is True
        assert result["version"] == PDF_RULESET_VERSION
        # Clean up
        os.remove(path)

    def test_pdf_tamper_detection(self, pdf_gen, sample_data):
        """Tampered metadata should fail verification."""
        import json as _json
        cipa, species = sample_data
        path = pdf_gen.generate(cipa, species, batch_id="TEST", compound_name="aspirin")

        # Read PDF, tamper with embedded data, rewrite
        with open(path, "rb") as f:
            raw = f.read()
        raw_str = raw.decode("utf-8", errors="replace")

        # Find and extract hex metadata
        import re as _re
        meta_match = _re.search(r"/AnuDrishtiMetadata /Data \(([0-9a-f]+)\)", raw_str)
        if meta_match:
            meta_hex = meta_match.group(1)
            meta_json = bytes.fromhex(meta_hex).decode("utf-8")
            meta = _json.loads(meta_json)
            # Tamper: change a prediction value
            meta["cipa_data"]["risk_classification"] = "HIGH_TORSADES_RISK"
            tampered_json = _json.dumps(meta, sort_keys=True, default=str)
            tampered_hex = tampered_json.encode("utf-8").hex()
            tampered_str = raw_str.replace(
                f"/AnuDrishtiMetadata /Data ({meta_hex})",
                f"/AnuDrishtiMetadata /Data ({tampered_hex})"
            )
            with open(path, "wb") as f:
                f.write(tampered_str.encode("utf-8"))

        result = pdf_gen.verify_signature(path)
        assert result["valid"] is False
        assert result["file_hash_match"] is False
        # Clean up
        os.remove(path)

    def test_pdf_nonexistent_file(self, pdf_gen):
        """Verification of non-existent file should return error."""
        result = pdf_gen.verify_signature("/nonexistent/file.pdf")
        assert result["valid"] is False
        assert "error" in result

    def test_singleton(self):
        """get_default_pdf_generator must return same instance."""
        g1 = get_default_pdf_generator()
        g2 = get_default_pdf_generator()
        assert g1 is g2

    def test_ruleset_version(self, pdf_gen):
        """PDF generator must report correct version."""
        assert pdf_gen.ruleset_version == "v3.0.0"


# ───────────────────────────────────────────────────────────────────────────
# Step 7: API Endpoint Integration Tests
# ───────────────────────────────────────────────────────────────────────────
class TestPhase3Endpoints:
    """Integration tests for Phase 3 API endpoints via Flask test client."""

    @pytest.fixture
    def client(self):
        from flask import Flask
        import routes.pharmaguard as pg
        app = Flask(__name__)
        app.register_blueprint(pg.pharmaguard_bp)
        with app.test_client() as c:
            yield c

    def test_cipa_endpoint(self, client):
        """POST /api/cardiotox/cipa with valid SMILES returns full result."""
        resp = client.post('/api/cardiotox/cipa', json={'smiles': 'CC(=O)OC1=CC=CC=C1'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'channels' in data
        assert 'q_net' in data
        assert 'proarrhythmic_risk_score' in data
        assert 'risk_classification' in data
        assert 'ghs_risk_flag' in data
        assert 'model_version' in data
        assert 'herg_channel' in data['channels']
        assert 'nav15_channel' in data['channels']
        assert 'cav12_channel' in data['channels']

    def test_cipa_endpoint_missing_smiles(self, client):
        """POST /api/cardiotox/cipa without SMILES returns 400."""
        resp = client.post('/api/cardiotox/cipa', json={})
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_cipa_endpoint_invalid_smiles(self, client):
        """POST /api/cardiotox/cipa with invalid SMILES returns 400."""
        resp = client.post('/api/cardiotox/cipa', json={'smiles': 'INVALIDSMILES!!!'})
        assert resp.status_code == 400
        data = resp.get_json()
        assert 'error' in data

    def test_translation_endpoint(self, client):
        """POST /api/translation/animal with valid SMILES returns translation."""
        resp = client.post('/api/translation/animal', json={
            'smiles': 'CC(=O)OC1=CC=CC=C1',
            'dose_mg': 100,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'ld50' in data
        assert 'clearance_ml_per_min_per_kg' in data
        assert 'hed_mg' in data
        assert 'noael_mg' in data
        assert 'margin_of_safety' in data
        assert 'nams_justification' in data
        assert 'model_hash' in data
        assert 'success' in data
        assert data['success'] is True

    def test_translation_endpoint_species_coverage(self, client):
        """Translation endpoint must return all 5 species."""
        resp = client.post('/api/translation/animal', json={'smiles': 'c1ccccc1'})
        data = resp.get_json()
        cls = data['clearance_ml_per_min_per_kg']
        for sp in ['human', 'rat', 'mouse', 'dog', 'monkey']:
            assert sp in cls, f"Missing species: {sp}"

    def test_translation_endpoint_missing_smiles(self, client):
        """POST /api/translation/animal without SMILES returns 400."""
        resp = client.post('/api/translation/animal', json={})
        assert resp.status_code == 400
        assert 'error' in resp.get_json()

    def test_regulatory_pdf_endpoint(self, client):
        """POST /api/report/regulatory-pdf generates a valid PDF."""
        resp = client.post('/api/report/regulatory-pdf', json={
            'smiles': 'CC(=O)OC1=CC=CC=C1',
            'compound_name': 'aspirin',
            'batch_id': 'TEST_E2E',
            'dose_mg': 100,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['success'] is True
        assert 'pdf_path' in data
        assert os.path.exists(data['pdf_path'])
        assert data['cipa_risk'] in ('LOW_ARRHYTHMIC_RISK', 'INTERMEDIATE_MONITOR', 'HIGH_TORSADES_RISK')
        assert 'verify_url' in data
        # Clean up
        if os.path.exists(data['pdf_path']):
            os.remove(data['pdf_path'])
        report_dir = os.path.join(os.getcwd(), "regulatory_reports")
        if os.path.isdir(report_dir) and not os.listdir(report_dir):
            os.rmdir(report_dir)

    def test_verify_signature_endpoint(self, client):
        """GET /api/report/verify-signature verifies a generated PDF."""
        # First generate a PDF
        resp = client.post('/api/report/regulatory-pdf', json={
            'smiles': 'CC(=O)OC1=CC=CC=C1',
            'compound_name': 'aspirin',
            'batch_id': 'VERIFY_TEST',
        })
        pdf_path = resp.get_json()['pdf_path']

        # Then verify
        resp2 = client.get('/api/report/verify-signature', query_string={'pdf_path': pdf_path})
        assert resp2.status_code == 200
        data = resp2.get_json()
        assert data['valid'] is True
        assert data['file_hash_match'] is True

        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        report_dir = os.path.join(os.getcwd(), "regulatory_reports")
        if os.path.isdir(report_dir) and not os.listdir(report_dir):
            os.rmdir(report_dir)

    def test_dose_endpoint(self, client):
        """Both endpoints should work with just a SMILES (no dose)."""
        resp = client.post('/api/translation/animal', json={'smiles': 'c1ccccc1'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['hed_mg'] is None  # no dose → no HED


# ───────────────────────────────────────────────────────────────────────────
# Step 8: End-to-End Reference Compound Pipeline
# ───────────────────────────────────────────────────────────────────────────
class TestEndToEndPipeline:
    """End-to-end test: CiPA → PDF → Signature Verify for all reference compounds."""

    @pytest.fixture
    def engines(self):
        return CiPACardioToxEngine(), SpeciesTranslationEngine(), RegulatoryPDFGenerator()

    @pytest.fixture
    def client(self):
        from flask import Flask
        import routes.pharmaguard as pg
        app = Flask(__name__)
        app.register_blueprint(pg.pharmaguard_bp)
        with app.test_client() as c:
            yield c

    def test_reference_compound_pipeline(self, engines, client):
        """Run full pipeline for each reference compound and verify PDF signature."""
        cipa_engine, translator, pdf_gen = engines

        for name, info in cipa_engine.reference_compounds.items():
            smiles = info["smiles"]
            cipa = cipa_engine.evaluate_molecule(smiles)
            species = translator.translate_molecule(smiles, dose_mg=50)
            species["human_dose_mg"] = 50

            path = pdf_gen.generate(cipa, species, batch_id="REF_TEST",
                                    compound_name=name)
            assert os.path.exists(path), f"PDF not generated for {name}"
            result = pdf_gen.verify_signature(path)
            assert result["valid"] is True, f"Signature failed for {name}: {result}"
            os.remove(path)

        # Clean up directory
        report_dir = os.path.join(os.getcwd(), "regulatory_reports")
        if os.path.isdir(report_dir) and not os.listdir(report_dir):
            os.rmdir(report_dir)
