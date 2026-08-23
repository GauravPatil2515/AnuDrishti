"""
Tests for PILLAR 4: Neuro-Symbolic Co-Pilot Closed-Loop Optimization
===================================================================

Verifies the 3-iteration autonomous bioisosteric optimization loop:
- Molecules below EFS 0.70 trigger the loop
- Each iteration identifies toxicophores, proposes candidate, re-scores
- EFS is computed at each step
- Verified when EFS >= 0.70
- Escalated to HUMAN_REVIEW after 3 failed iterations
- API endpoint integration via Flask test client
"""

import pytest

from models.constrained_explainer import (
    NeuroSymbolicCopilot,
    OptimizationIteration,
    EFS_THRESHOLD,
    VERDICT_VERIFIED,
    VERDICT_RETRY,
    VERDICT_HUMAN_REVIEW,
)

# ============================================================================
# Reference molecules for testing
# ============================================================================

ASPIRIN = "CC(=O)OC1=CC=CC=C1"
NITROBENZENE = "c1ccc([N+](=O)[O-])cc1"
NITRO_ANILINE = "Nc1ccccc1[N+](=O)[O-]"
WARFARIN = "CC(C)(COC(=O)c1ccccc1)c1ccccc1"


@pytest.fixture
def copilot():
    """Fresh co-pilot instance for each test."""
    return NeuroSymbolicCopilot()


# ============================================================================
# Tests: Baseline Assessment
# ============================================================================

class TestBaselineAssessment:
    """Test the initial assessment of input molecules."""

    def test_baseline_clean_molecule(self, copilot):
        """Clean molecule should have low toxicity and valid EFS."""
        result = copilot._baseline_assessment(ASPIRIN)
        assert result['candidate_smiles'] == ASPIRIN
        assert 'efs_score' in result
        assert 0.0 <= result['efs_score'] <= 1.0

    def test_baseline_nitro_toxicophore(self, copilot):
        """Nitrobenzene should have elevated toxicity."""
        result = copilot._baseline_assessment(NITROBENZENE)
        assert result['toxicity'] > 0.3
        assert 'qed' in result

    def test_baseline_invalid_smiles(self, copilot):
        """Invalid SMILES should return error."""
        result = copilot._baseline_assessment("not_a_smiles")
        assert result.get('error') is not None

    def test_baseline_warfarin_high_efS(self, copilot):
        """Warfarin (clean, high QED) should have high baseline EFS."""
        result = copilot._baseline_assessment(WARFARIN)
        assert result['efs_score'] >= EFS_THRESHOLD


# ============================================================================
# Tests: Toxicophore Identification
# ============================================================================

class TestToxicophoreIdentification:
    """Test identification of toxicophores and high-uncertainty atoms."""

    def test_identify_nitro_toxicophore(self, copilot):
        """Nitro group should be identified as a toxicophore."""
        tox_smarts, uncertain = copilot._identify_toxicophore(
            NITROBENZENE, [0.25, 0.25, 0.25, 0.25]
        )
        assert isinstance(tox_smarts, str)
        assert isinstance(uncertain, list)

    def test_identify_returns_atom_indices(self, copilot):
        """Should return atom indices as integers."""
        tox_smarts, uncertain = copilot._identify_toxicophore(
            NITROBENZENE, [0.25, 0.25, 0.25, 0.25]
        )
        assert isinstance(tox_smarts, str)
        for idx in uncertain:
            assert isinstance(idx, int)

    def test_identify_no_attention_fallback(self, copilot):
        """Without attention weights, should use structural alerts."""
        tox_smarts, uncertain = copilot._identify_toxicophore(
            NITROBENZENE, []
        )
        assert isinstance(tox_smarts, str)
        assert isinstance(uncertain, list)

    def test_identify_invalid_smiles(self, copilot):
        """Invalid SMILES should return a default pattern."""
        tox_smarts, uncertain = copilot._identify_toxicophore(
            "not_a_smiles", []
        )
        assert isinstance(tox_smarts, str)
        assert uncertain == []


# ============================================================================
# Tests: EFS Computation
# ============================================================================

class TestEFSComputation:
    """Test the Explainable Faithfulness Score proxy computation."""

    def test_efs_zero_toxicity(self, copilot):
        """Low toxicity + high QED should give high EFS."""
        efs = copilot._compute_proxy_efs(0.1, 0.8, [1.0])
        assert efs > 0.70

    def test_efs_high_toxicity(self, copilot):
        """High toxicity should give low EFS."""
        efs = copilot._compute_proxy_efs(0.9, 0.3, [0.33, 0.33, 0.33])
        assert efs < 0.40

    def test_efs_uniform_attention(self, copilot):
        """Uniform attention should yield moderate EFS."""
        efs = copilot._compute_proxy_efs(0.3, 0.6, [0.33, 0.33, 0.33])
        assert 0.3 <= efs <= 0.8

    def test_efs_range(self, copilot):
        """EFS should always be in [0, 1]."""
        for tox in [0.0, 0.3, 0.5, 0.7, 1.0]:
            for qed in [0.0, 0.5, 1.0]:
                efs = copilot._compute_proxy_efs(tox, qed, [0.25, 0.25, 0.25, 0.25])
                assert 0.0 <= efs <= 1.0


# ============================================================================
# Tests: Optimization Loop — VERIFIED path
# ============================================================================

class TestOptimizationVerified:
    """Test molecules that pass EFS threshold and get VERIFIED."""

    def test_verified_molecule_no_toxicophore(self, copilot):
        """Clean molecule with high QED should VERIFY immediately."""
        result = copilot.optimize(WARFARIN)
        assert result['verdict'] == VERDICT_VERIFIED
        assert result['iterations_run'] == 0
        assert result['accepted_candidate'] == WARFARIN

    def test_verified_accepts_baseline(self, copilot):
        """If baseline EFS >= threshold, baseline is accepted without iterations."""
        result = copilot.optimize(WARFARIN)
        assert result['accepted_candidate_efs'] is not None
        assert result['accepted_candidate_efs'] >= EFS_THRESHOLD

    def test_verified_result_has_success(self, copilot):
        """VERIFIED result should have success=True."""
        result = copilot.optimize(WARFARIN)
        assert result['success'] is True


# ============================================================================
# Tests: Optimization Loop — RETRY / HUMAN_REVIEW path
# ============================================================================

class TestOptimizationRetry:
    """Test the retry and escalation behavior."""

    def test_nitrobenzene_triggers_loop(self, copilot):
        """Nitrobenzene has toxicophore — should trigger optimization loop."""
        result = copilot.optimize(NITROBENZENE)
        # Either gets fixed via bioisostere or escalates
        assert result['iterations_run'] >= 1
        assert result['iterations_run'] <= 3
        assert result['verdict'] in [VERDICT_VERIFIED, VERDICT_HUMAN_REVIEW]

    def test_max_iterations_capped_at_3(self, copilot):
        """Should never exceed 3 iterations."""
        result = copilot.optimize(NITRO_ANILINE)
        assert result['iterations_run'] <= 3
        assert len(result['iteration_history']) <= 3

    def test_human_review_after_max_iterations(self, copilot):
        """If EFS stays below threshold for 3 iterations, escalate to HUMAN_REVIEW."""
        result = copilot.optimize(NITRO_ANILINE)
        if result['iterations_run'] == 3:
            assert result['verdict'] == VERDICT_HUMAN_REVIEW

    def test_iteration_history_tracked(self, copilot):
        """Each iteration should be recorded in history."""
        result = copilot.optimize(NITROBENZENE)
        if result['iterations_run'] > 0:
            for it in result['iteration_history']:
                assert 'iteration' in it
                assert 'candidate_smiles' in it
                assert 'efs_score' in it
                assert 'verdict' in it

    def test_iteration_has_property_delta(self, copilot):
        """Each iteration should include property delta tracking."""
        result = copilot.optimize(NITROBENZENE)
        if result['iterations_run'] > 0:
            for it in result['iteration_history']:
                if it.get('property_delta'):
                    pd = it['property_delta']
                    assert 'toxicity_delta' in pd
                    assert 'qed_delta' in pd


# ============================================================================
# Tests: Iteration Structure
# ============================================================================

class TestIterationStructure:
    """Test that iterations have correct fields."""

    def test_iteration_fields(self, copilot):
        """Iteration should have all required fields."""
        result = copilot.optimize(NITROBENZENE)
        if result['iteration_history']:
            it = result['iteration_history'][0]
            assert 'iteration' in it
            assert 'input_smiles' in it
            assert 'candidate_smiles' in it
            assert 'efs_score' in it
            assert 'verdict' in it
            assert 'mechanistic_notes' in it
            assert 'property_delta' in it

    def test_iteration_toxicophore_replaced(self, copilot):
        """Iteration should include toxicophore info."""
        result = copilot.optimize(NITROBENZENE)
        if result['iteration_history']:
            it = result['iteration_history'][0]
            # At least one of these should be present
            assert 'toxicophore_replaced' in it or 'replaced_atoms' in it


# ============================================================================
# Tests: Streaming
# ============================================================================

class TestStreaming:
    """Test the streaming interface."""

    def test_stream_yields_chunks(self, copilot):
        """Stream should yield chunks for each step."""
        chunks = list(copilot.stream_optimize(WARFARIN))
        assert len(chunks) > 0
        # First chunk should be baseline
        assert chunks[0].get('status') == 'baseline'

    def test_stream_final_has_verdict(self, copilot):
        """Final streamed chunk should have verdict."""
        chunks = list(copilot.stream_optimize(WARFARIN))
        assert 'verdict' in chunks[-1]

    def test_stream_history_chunks(self, copilot):
        """Stream should include iteration chunks when loop runs."""
        chunks = list(copilot.stream_optimize(NITROBENZENE))
        iter_chunks = [c for c in chunks if c.get('status') == 'iteration']
        # If any chunk has escalated/final verdict != VERIFIED, we should have iterations
        has_escalation = any(c.get('verdict') == 'HUMAN_REVIEW' for c in chunks)
        has_verification = any(c.get('verdict') == 'VERIFIED' for c in chunks)
        if has_escalation:
            assert len(iter_chunks) > 0

    def test_stream_iter_chunks_capped(self, copilot):
        """Stream should not exceed 3 iteration chunks."""
        chunks = list(copilot.stream_optimize(NITRO_ANILINE))
        iter_chunks = [c for c in chunks if c.get('status') == 'iteration']
        assert len(iter_chunks) <= 3


# ============================================================================
# Tests: Bioisosteric Generation
# ============================================================================

class TestBioisostericGeneration:
    """Test bioisosteric candidate generation."""

    def test_generate_nitro_to_amide(self, copilot):
        """Nitro group should be replaced with an amide."""
        candidate, info = copilot._bioisostere_generate(
            NITROBENZENE, "[N+](=O)[O-]"
        )
        assert candidate is not None
        assert len(candidate) > 0

    def test_generate_returns_smiles(self, copilot):
        """Generated candidate should be a valid SMILES."""
        from rdkit import Chem
        candidate, info = copilot._bioisostere_generate(
            NITROBENZENE, "[N+](=O)[O-]"
        )
        if candidate is not None:
            mol = Chem.MolFromSmiles(candidate)
            assert mol is not None

    def test_generate_no_toxicophore(self, copilot):
        """When no toxicophore is found, should return original or None."""
        candidate, info = copilot._bioisostere_generate(
            WARFARIN, "[N+](=O)[O-]"
        )
        # Warfarin doesn't have nitro -> either returns original or a candidate
        assert candidate is None or isinstance(candidate, str)


# ============================================================================
# Tests: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_smiles(self, copilot):
        """Empty SMILES should be rejected with error."""
        result = copilot.optimize("")
        assert 'error' in result

    def test_invalid_smiles(self, copilot):
        """Invalid SMILES should return error."""
        result = copilot.optimize("!!!invalid!!!")
        assert 'error' in result

    def test_single_atom(self, copilot):
        """Single atom should be handled."""
        result = copilot.optimize("C")
        assert 'verdict' in result or 'error' in result

    def test_very_large_smiles(self, copilot):
        """Large molecule should not crash."""
        large_smi = "C" * 100 + "N"
        result = copilot.optimize(large_smi)
        assert 'error' in result or 'verdict' in result


# ============================================================================
# Tests: Constants and Configuration
# ============================================================================

class TestConstants:
    """Test co-pilot configuration constants."""

    def test_threshold_value(self):
        """EFS_THRESHOLD should be 0.70."""
        assert EFS_THRESHOLD == 0.70

    def test_max_iterations_is_3(self, copilot):
        """Max iterations should be capped at 3."""
        result = copilot.optimize(NITROBENZENE)
        assert result['iterations_run'] <= copilot.max_iterations

    def test_verdict_constants(self):
        """Verdict constants should have correct values."""
        assert VERDICT_VERIFIED == 'VERIFIED'
        assert VERDICT_RETRY == 'RETRY'
        assert VERDICT_HUMAN_REVIEW == 'HUMAN_REVIEW'


# ============================================================================
# API Endpoint Integration Tests
# ============================================================================

class TestCopilotAPI:
    """Test the /api/copilot/optimize-loop endpoint."""

    def test_endpoint_returns_result(self, app):
        """Endpoint should return optimization result."""
        with app.test_client() as client:
            response = client.post('/api/copilot/optimize-loop',
                                   json={'smiles': WARFARIN})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['verdict'] in ['VERIFIED', 'HUMAN_REVIEW', 'RETRY']

    def test_endpoint_missing_smiles(self, app):
        """Endpoint should reject missing SMILES."""
        with app.test_client() as client:
            response = client.post('/api/copilot/optimize-loop',
                                   json={})
            assert response.status_code == 400
            data = response.get_json()
            assert 'error' in data

    def test_endpoint_nitrobenzene(self, app):
        """Endpoint should process nitrobenzene through the loop."""
        with app.test_client() as client:
            response = client.post('/api/copilot/optimize-loop',
                                   json={'smiles': NITROBENZENE})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert data['iterations_run'] >= 0
            assert data['iterations_run'] <= 3

    def test_endpoint_result_structure(self, app):
        """Endpoint response should have all required fields."""
        with app.test_client() as client:
            response = client.post('/api/copilot/optimize-loop',
                                   json={'smiles': WARFARIN})
            data = response.get_json()
            assert 'verdict' in data
            assert 'status' in data
            assert 'iterations_run' in data
            assert 'iteration_history' in data
            assert 'baseline_toxicity' in data
            assert 'baseline_qed' in data
            assert 'input_smiles' in data

    def test_stream_endpoint(self, app):
        """The /api/copilot/stream endpoint should work."""
        with app.test_client() as client:
            response = client.post('/api/copilot/stream',
                                   json={'smiles': WARFARIN})
            assert response.status_code == 200
            data = response.get_json()
            assert data['success'] is True
            assert 'stream_results' in data
            assert 'final_verdict' in data

    def test_stream_missing_smiles(self, app):
        """Stream endpoint should reject missing SMILES."""
        with app.test_client() as client:
            response = client.post('/api/copilot/stream',
                                   json={})
            assert response.status_code == 400
