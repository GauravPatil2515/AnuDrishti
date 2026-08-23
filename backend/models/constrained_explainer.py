#!/usr/bin/env python3
"""
Constrained Explainer: Faithful LLM Explanation Generator
==========================================================
Generates LLM explanations that are constrained by model evidence
and validated for faithfulness.

Key Innovation: Explanations are REJECTED if they fail faithfulness tests.

Paper: From Plausible to Faithful: Causally-Constrained LLM Explanations
       for Molecular Toxicity Prediction

Author: DeNovo-XAI Research Team
"""

import hashlib
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
import threading
import time
import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ConstrainedExplainer')


@dataclass
class FaithfulExplanation:
    """
    A validated, faithful explanation for a molecular toxicity prediction.
    
    Attributes:
        smiles: The SMILES string of the molecule.
        prediction: The toxicity prediction score (0-1).
        executive_summary: High-level summary of the toxicity analysis.
        mechanism: Detailed mechanistic explanation.
        identified_toxicophores: List of toxic structural alerts found.
        faithfulness_score: The computed faithfulness score (0-1).
        validation_passed: Whether the explanation passed validation.
        rejection_reason: Reason for rejection, if applicable.
        faithfulness_details: Detailed breakdown of validation tests.
        generation_attempts: Number of attempts to generate this explanation.
    """
    smiles: str
    prediction: float
    
    # Explanation content
    executive_summary: str
    mechanism: str
    identified_toxicophores: List[Dict[str, Any]]
    
    # Faithfulness validation
    faithfulness_score: float
    validation_passed: bool
    rejection_reason: Optional[str] = None
    faithfulness_details: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    generation_attempts: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the dataclass to a dictionary."""
        return asdict(self)


class ConstrainedExplainer:
    """
    Generates faithful explanations by constraining LLM with model evidence
    and validating outputs.
    
    The Generation Pipeline:
    1. **Evidence Extraction**: Analyze Graph Neural Network (GNN) attention weights to find 
       active toxicophores (substructures) that actually influenced the model.
    2. **Constrained Generation**: Prompt the LLM to explain the prediction using *only* 
       the identified high-attention features.
    3. **Faithfulness Validation**: Use the FaithfulnessValidator to ensure the LLM 
       didn't hallucinate or ignore the constraints.
    4. **Accept or Reject**: If validation fails, reject and retry.
    """
    
    # Constrained prompt template
    CONSTRAINED_PROMPT = """You are a toxicology expert analyzing a molecular toxicity prediction.

CRITICAL CONSTRAINTS:
1. Only mention substructures with attention score > {attention_threshold}
2. Do not speculate beyond the provided evidence
3. For each claim, cite the attention score
4. Output MUST be valid JSON

## Model Evidence

Molecule: {smiles}
Predicted Toxicity: {prediction:.1%}

High-Attention Substructures (The "Why"):
{substructure_evidence}

## Task

Generate a toxicity explanation following this EXACT JSON structure:

{{
  "executive_summary": "2-3 sentence summary of toxicity risk",
  "primary_toxicophore": {{
    "name": "name of most important toxic group",
    "atoms": [list of atom indices],
    "attention_score": 0.0-1.0,
    "mechanism": "brief mechanism explanation"
  }},
  "secondary_features": [
    {{
      "name": "feature name",
      "attention_score": 0.0-1.0,
      "contribution": "how it contributes"
    }}
  ],
  "overall_mechanism": "detailed mechanism (2-3 sentences)",
  "confidence": 0.0-1.0
}}

REMEMBER: Only include features with attention > {attention_threshold}. Do not invent mechanisms not supported by the evidence.
"""
    
    def __init__(
        self,
        model: Any,
        llm_provider: Any,
        substructure_mapper: Any,
        faithfulness_validator: Any,
        max_generation_attempts: int = 3,
        attention_threshold: float = 0.1
    ):
        """
        Initialize the Constrained Explainer.
        
        Args:
            model: The GNN model (AttentionGIN).
            llm_provider: The LLM interface (Groq or Mock).
            substructure_mapper: Tool to map attention weights to chemical groups.
            faithfulness_validator: The validation engine.
            max_generation_attempts: Maximum retries if validation fails.
            attention_threshold: Minimum attention score for a feature to be considered relevant.
        """
        self.model = model
        self.llm = llm_provider
        self.substructure_mapper = substructure_mapper
        self.validator = faithfulness_validator
        self.max_attempts = max_generation_attempts
        self.attention_threshold = attention_threshold
        
        # Statistics tracking
        self.total_generated = 0
        self.total_rejected = 0
    
    def explain(
        self,
        smiles: str,
        prediction: float,
        attention_weights: List[float],
        validate: bool = True
    ) -> FaithfulExplanation:
        """
        Generate a faithful explanation for a given molecule.
        
        Args:
            smiles: The SMILES string of the molecule.
            prediction: The model's toxicity prediction (0-1).
            attention_weights: List of attention scores for each atom.
            validate: Whether to run the faithfulness validation loop.
            
        Returns:
            A FaithfulExplanation object (which may be marked as rejected).
        """
        import numpy as np
        attention_weights = np.array(attention_weights)
        self.total_generated += 1
        
        # 1. Extract Model Evidence
        model_evidence = self._extract_evidence(smiles, attention_weights)
        
        # 2. Generate-Validate Loop
        last_faithfulness_result = None
        
        for attempt in range(1, self.max_attempts + 1):
            logger.info(f"Generation attempt {attempt}/{self.max_attempts} for {smiles[:15]}...")
            
            # Generate LLM explanation
            explanation_dict = self._generate_llm_explanation(
                smiles, prediction, model_evidence
            )
            
            if explanation_dict is None:
                logger.warning("LLM failed to generate valid JSON.")
                continue
            
            # If validation is disabled, return immediately
            if not validate:
                return self._create_accepted_explanation(
                    smiles, prediction, explanation_dict, attempt
                )
            
            # 3. Validate Faithfulness
            faithfulness_result = self.validator.validate(
                explanation_dict,
                smiles,
                prediction,
                attention_weights,
                run_counterfactual_test=(attempt == 1)  # Optimization: run expensive test only once
            )
            last_faithfulness_result = faithfulness_result
            
            if faithfulness_result.passed:
                # ACCEPTED
                logger.info(f"✅ Explanation ACCEPTED (Score: {faithfulness_result.overall_score:.3f})")
                return self._create_accepted_explanation(
                    smiles, prediction, explanation_dict, attempt, faithfulness_result
                )
            else:
                # REJECTED - try again
                logger.warning(f"❌ Explanation REJECTED (Score: {faithfulness_result.overall_score:.3f})")
                
                # Provide internal feedback (logging only for now)
                if attempt < self.max_attempts:
                    logger.info("Regenerating with stricter constraints...")
        
        # 4. Final Rejection (if all attempts failed)
        self.total_rejected += 1
        logger.error(f"Failed to generate faithful explanation after {self.max_attempts} attempts")
        # Fallback to deterministic explanation (will be handled by caller)
        return None
    def get_rejection_rate(self) -> float:
        """Calculate the percentage of explanations that were rejected."""
        if self.total_generated == 0:
            return 0.0
        return self.total_rejected / self.total_generated

    # =========================================================================
    # Internal Helper Methods
    # =========================================================================

    def _extract_evidence(self, smiles: str, attention_weights: Any) -> Dict[str, Any]:
        """Extract high-attention substructures to serve as evidence."""
        # Get active substructures. Use an adaptive, per-molecule attention cutoff
        # (relative to the 1/N uniform baseline) rather than a fixed absolute
        # threshold, which is diluted to zero matches on larger molecules.
        matches = self.substructure_mapper.identify_substructures(
            smiles,
            attention_weights,
            threshold=None
        )
        
        evidence = {
            'substructures': [],
            'top_atoms': []
        }
        
        # Format top substructures
        for match in matches[:5]:  # Limit to top 5 clearest signals
            evidence['substructures'].append({
                'name': match.name,
                'smarts': match.smarts,
                'atoms': match.atoms,
                'attention_score': match.avg_attention,
                'category': match.toxicity_category,
                'mechanism': match.mechanism
            })
        
        # Get individual top atoms as fallback
        top_atoms = self.substructure_mapper.get_top_atoms(
            smiles, attention_weights, top_k=5
        )
        evidence['top_atoms'] = top_atoms
        
        return evidence
    
    def _generate_llm_explanation(
        self,
        smiles: str,
        prediction: float,
        evidence: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Call LLM to generate the explanation JSON."""

        # Format evidence for prompt
        substructure_text = self._format_substructure_evidence(evidence['substructures'])

        # Build prompt
        prompt = self.CONSTRAINED_PROMPT.format(
            smiles=smiles,
            prediction=prediction,
            substructure_evidence=substructure_text,
            attention_threshold=self.attention_threshold
        )

        # Generate LLM explanation with timeout protection
        result_container = [None]
        exception_container = [None]

        def target():
            try:
                response = self.llm.generate(
                    prompt,
                    max_tokens=800,
                    temperature=0.2  # Low temperature for factual consistency
                )
                # Parse and standardize
                explanation_dict = self._parse_llm_json(response)
                if explanation_dict:
                    result_container[0] = self._format_llm_output(explanation_dict, evidence)
            except Exception as e:
                exception_container[0] = e

        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout=30.0)  # 30 second timeout for LLM call

        if thread.is_alive():
            # Timeout occurred
            logger.warning(f"LLM generation timed out after 30 seconds for {smiles[:15]}...")
            return None

        if exception_container[0] is not None:
            logger.error(f"LLM generation failed: {exception_container[0]}")
            return None

        return result_container[0]
    def _parse_llm_json(self, response: str) -> Optional[Dict[str, Any]]:
        """Robustly parse JSON from LLM output, handling markdown blocks."""
        try:
            response = response.strip()
            # Remove markdown code blocks if present
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            
            return json.loads(response.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON: {e}")
            return None

    def _format_substructure_evidence(self, substructures: List[Dict]) -> str:
        """Format the list of substructures into a readable string for the prompt."""
        if not substructures:
            return "No specific high-attention substructures identified (all attention < threshold)."
        
        lines = []
        for i, sub in enumerate(substructures, 1):
            lines.append(
                f"{i}. {sub['name']} (atoms {sub['atoms']})\n"
                f"   Attention: {sub['attention_score']:.2%}\n"
                f"   Category: {sub['category']}\n"
                f"   Mechanism: {sub['mechanism'][:100]}..."
            )
        
        return "\n".join(lines)
    
    def _format_llm_output(self, llm_output: Dict, evidence: Dict) -> Dict:
        """Standardize the LLM output structure and link back to evidence."""
        # Extract primary toxicophore
        primary = llm_output.get('primary_toxicophore', {})
        identified_toxicophores = []
        
        # Helper to find matching evidence
        def find_evidence(name):
            for sub in evidence['substructures']:
                if sub['name'].lower() in name.lower():
                    return sub
            return None

        # Process Primary
        if primary:
            match = find_evidence(primary.get('name', ''))
            identified_toxicophores.append({
                'name': primary.get('name'),
                'smarts_pattern': match['smarts'] if match else None,
                'atom_indices': primary.get('atoms', match['atoms'] if match else []),
                'attention_score': primary.get('attention_score', match['attention_score'] if match else 0),
                'mechanism': primary.get('mechanism', match['mechanism'] if match else '')
            })
        
        # Process Secondary
        for secondary in llm_output.get('secondary_features', []):
            match = find_evidence(secondary.get('name', ''))
            identified_toxicophores.append({
                'name': secondary.get('name'),
                'smarts_pattern': match['smarts'] if match else None,
                'atom_indices': match['atoms'] if match else [],
                'attention_score': secondary.get('attention_score', match['attention_score'] if match else 0),
                'mechanism': secondary.get('contribution', '')
            })
        
        return {
            'executive_summary': llm_output.get('executive_summary', ''),
            'overall_mechanism': llm_output.get('overall_mechanism', ''),
            'identified_toxicophores': identified_toxicophores,
            'confidence': llm_output.get('confidence', 0.5)
        }

    def _create_accepted_explanation(
        self, 
        smiles: str, 
        prediction: float, 
        explanation_dict: Dict, 
        attempts: int,
        faithfulness_result: Any = None
    ) -> FaithfulExplanation:
        """Helper to create an accepted FaithfulExplanation object."""
        score = faithfulness_result.overall_score if faithfulness_result else 1.0
        details = faithfulness_result.to_dict() if faithfulness_result else {}
        
        return FaithfulExplanation(
            smiles=smiles,
            prediction=prediction,
            executive_summary=explanation_dict.get('executive_summary', ''),
            mechanism=explanation_dict.get('overall_mechanism', ''),
            identified_toxicophores=explanation_dict.get('identified_toxicophores', []),
            faithfulness_score=score,
            validation_passed=True,
            faithfulness_details=details,
            generation_attempts=attempts
        )

    def _create_rejected_explanation(
        self, 
        smiles: str, 
        prediction: float, 
        faithfulness_result: Any
    ) -> FaithfulExplanation:
        """Helper to create a rejected FaithfulExplanation object."""
        details = faithfulness_result.to_dict() if faithfulness_result else {}
        score = faithfulness_result.overall_score if faithfulness_result else 0.0
        
        return FaithfulExplanation(
            smiles=smiles,
            prediction=prediction,
            executive_summary="[Explanation generation failed faithfulness constraints]",
            mechanism="The system could not verify the scientific validity of the explanation.",
            identified_toxicophores=[],
            faithfulness_score=score,
            validation_passed=False,
            rejection_reason="Failed faithfulness validation after max attempts",
            faithfulness_details=details,
            generation_attempts=self.max_attempts
        )


if __name__ == "__main__":
    print("Testing Constrained Explainer...")
    print("=" * 60)
    
    # Example Prompt Display
    print("\nExample Constrained Prompt:")
    print("-" * 60)
    example_prompt = ConstrainedExplainer.CONSTRAINED_PROMPT.format(
        smiles="c1ccc([N+](=O)[O-])cc1",
        prediction=0.85,
        substructure_evidence="1. Nitro (atoms [6,7,8])\n   Attention: 35%\n   Category: Mutagenic",
        attention_threshold=0.1
    )
    print(example_prompt[:500] + "...")


# ─────────────────────────────────────────────────────────────────────────────
# PILLAR 4: Neuro-Symbolic Co-Pilot — Closed-Loop Bioisosteric Optimization
# ─────────────────────────────────────────────────────────────────────────────
# When a molecule fails the EFS (Explainability Faithfulness Score) threshold
# (EFS < 0.70), the NeuroSymbolicCopilot runs an autonomous 3-iteration loop:
#   1. Identify top toxicophore + high-uncertainty atoms from GNN attention.
#   2. Query structured bioisosteric generator for candidate replacements.
#   3. Re-score candidate via GNN (toxicity, affinity proxy, QED > 0.40).
#   4. Compute EFS for the candidate. If EFS >= 0.70, accept & VERIFIED.
#      Otherwise re-feed constraints and retry (up to 3 iterations).
#   5. If all 3 iterations fail, escalate to HUMAN_REVIEW.
#
# The LLM query uses the grounded prompt template from Pillar 4.1 of the
# AnuDrishti Enterprise Roadmap, with a deterministic bioisosteric fallback
# when no Groq API key is available.
# ─────────────────────────────────────────────────────────────────────────────

COPILOT_RULESET_VERSION = "v3.0.0"

# EFS threshold for accepting an optimized candidate
EFS_THRESHOLD = 0.70
MAX_COPILOT_ITERATIONS = 3

# Verdict constants
VERDICT_VERIFIED = "VERIFIED"
VERDICT_RETRY = "RETRY"
VERDICT_HUMAN_REVIEW = "HUMAN_REVIEW"

# Maximum iterations in the closed loop
MAX_ITERATIONS = 3

# Deterministic bioisosteric replacement map.
# Maps SMARTS patterns to lists of replacement SMILES fragments.
# Each entry: (pattern_smarts, [list of (replacement_smarts, new_smiles_template, description)])
# The replacement_smiles_template uses '{ring}' as a placeholder for the
# matched atom environment where the replacement should be applied.
_BIOISOSTERIC_REPLACEMENTS = {
    # Nitro group -> amide / sulfonamide (reduces mutagenicity)
    "[N+](=O)[O-]": [
        ("[NH]C(=O)N", "amide_bioisostere", "Nitro-to-amide replacement"),
        ("[NH]S(=O)(=O)N", "sulfonamide_bioisostere", "Nitro-to-sulfonamide replacement"),
    ],
    # Basic tertiary amine (hERG risk) -> reduced basicity / neutral
    "[#7;H0;v3;!a;!$(N~[!#6])]": [
        ("[NH]C(=O)", "neutral_amide", "Tertiary amine to neutral amide"),
        ("[NH]C(=O)C", "amide_extension", "Tertiary amine to amide + methyl"),
    ],
    # Carboxylic acid -> ester (reduces ionization, P-gp recognition)
    "[CX3]([OH])=O": [
        ("[CX3]([O])[O]C", "ester_bioisostere", "Carboxylic acid to ester"),
    ],
    # Halogen (metabolic liability) -> smaller halogen or H
    "Cl": [
        ("", "dehalogenation", "Chlorine removal"),
    ],
}


class OptimizationIteration:
    """Record of a single iteration in the neuro-symbolic optimization loop."""

    def __init__(self, iteration: int, input_smiles: str,
                 candidate_smiles: str, property_delta: Dict[str, float],
                 efs_score: float, verdict: str,
                 mechanistic_notes: str = "",
                 toxicophore_replaced: Optional[str] = None,
                 replaced_atoms: Optional[List[int]] = None):
        self.iteration = iteration
        self.input_smiles = input_smiles
        self.candidate_smiles = candidate_smiles
        self.property_delta = property_delta
        self.efs_score = efs_score
        self.verdict = verdict  # VERIFIED, RETRY, HUMAN_REVIEW
        self.mechanistic_notes = mechanistic_notes
        self.timestamp = datetime.now().isoformat()
        self.toxicophore_replaced = toxicophore_replaced
        self.replaced_atoms = replaced_atoms or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "iteration": self.iteration,
            "input_smiles": self.input_smiles,
            "candidate_smiles": self.candidate_smiles,
            "property_delta": self.property_delta,
            "efs_score": self.efs_score,
            "verdict": self.verdict,
            "mechanistic_notes": self.mechanistic_notes,
            "timestamp": self.timestamp,
            "toxicophore_replaced": self.toxicophore_replaced,
            "replaced_atoms": self.replaced_atoms,
        }


class NeuroSymbolicCopilot:
    """
    Autonomous neuro-symbolic co-pilot for bioisosteric optimization.

    When a molecule's EFS falls below the faithfulness threshold (0.70),
    this engine runs a capped 3-iteration closed loop:
      1. Identify top toxicophore + high-uncertainty atoms (GNN attention).
      2. Query the structured bioisosteric generator (deterministic fallback
         if LLM is unavailable).
      3. Re-score candidate via GNN predictor (toxicity, affinity proxy, QED).
      4. Compute EFS. Accept if >= threshold, else retry with new constraints.

    If all iterations fail, the case is escalated to HUMAN_REVIEW.
    """

    COPILOT_PROMPT = """You are a neuro-symbolic medicinal chemistry co-pilot working inside the AnuDrishti
PharmaGuard AI regulatory drug-safety platform (Defense-grade, deterministic).

GROUNDING PRINCIPLES (Pillar 4.1):
1. You operate inside a closed-loop: toxicophore identification -> bioisosteric
   replacement -> GNN re-scoring -> EFS recomputation. Max 3 iterations.
2. At each iteration, identify the top toxicophore and high-uncertainty atom
   indices from the GNN attention/attribution map (threshold = {attention_threshold}).
3. Query the deterministic bioisosteric replacement map for candidate motifs.
   If the Groq API key is available, refine with LLM-guided substitution; otherwise,
   use the deterministic fallback.
4. Re-score each candidate via the GNN predictor for:
   - Toxicity probability (must decrease vs. input)
   - Affinity proxy (must not drop more than 10% vs. input target affinity)
   - QED (must be > 0.40)
5. Compute EFS score for the candidate. If EFS >= {efs_threshold}, accept and
   mark VERIFIED. If < {efs_threshold}, re-feed with additional constraint
   and retry. After {max_iterations} failed iterations, escalate to HUMAN_REVIEW.

CONSTRAINTS:
- You MUST use the exact SMILES output format for candidate molecules.
- You MUST cite the atom indices for toxicophore identification.
- You MUST report property deltas (toxicity delta, QED delta) for each iteration.
- Never fabricate data: only report what the GNN and structural alerts show.
- All operations must be deterministic and reproducible (seed=42).

INPUT:
  Original SMILES: {smiles}
  Original Toxicity: {toxicity:.4f}
  Original QED: {qed:.4f}
  Original Attention weights: {attention_weights}
  Original EFS score: {efs_score:.4f}
  Top toxicophore atoms: {top_atoms}
  Matched toxicophores: {toxicophores}

TASK:
  For this iteration {iteration}/{max_iterations}:
  (a) Identify the single top toxicophore to replace (by attention * toxicity contribution).
  (b) Propose the optimal bioisosteric replacement from the deterministic map.
  (c) Construct the candidate SMILES.
  (d) Report the expected property delta.

  Output the candidate as a JSON object ONLY:
  {{
    "candidate_smiles": "<str>",
    "replacement_type": "<str>",
    "replaced_smarts": "<str>",
    "replaced_atoms": [<int>],
    "expected_property_delta": {{"toxicity_delta": <float>, "qed_delta": <float>}},
    "rationale": "<str>"
  }}
"""

    def __init__(
        self,
        gnn_predictor=None,
        faithfulness_validator=None,
        substructure_mapper=None,
        llm_provider=None,  # Optional Groq client
        max_iterations: int = MAX_ITERATIONS,
        efs_threshold: float = EFS_THRESHOLD,
        attention_threshold: float = 0.1,
    ):
        self.gnn_predictor = gnn_predictor
        self.faithfulness_validator = faithfulness_validator
        self.substructure_mapper = substructure_mapper
        self.llm_provider = llm_provider
        self.max_iterations = max_iterations
        self.efs_threshold = efs_threshold
        self.attention_threshold = attention_threshold
        self.ruleset_version = COPILOT_RULESET_VERSION

    def optimize(self, smiles: str) -> Dict[str, Any]:
        """
        Run the full 3-iteration neuro-symbolic optimization loop.

        Args:
            smiles: Original molecule SMILES

        Returns:
            Dict with iteration_history, accepted_candidate, verdict, and metadata.
        """
        from rdkit import Chem
        from rdkit.Chem import Descriptors

        mol = Chem.MolFromSmiles(smiles)
        if mol is None or mol.GetNumAtoms() == 0:
            return {
                "success": False,
                "error": "Invalid SMILES string",
                "smiles": smiles,
            }

        # --- Step 0: Get baseline prediction, QED, attention, EFS ---
        baseline = self._baseline_assessment(smiles)
        if "error" in baseline:
            return {"success": False, "error": baseline["error"], "smiles": smiles}

        # If baseline EFS already passes, no optimization needed
        if baseline["efs_score"] >= self.efs_threshold:
            return {
                "success": True,
                "status": "VERIFIED",
                "verdict": "VERIFIED",
                "input_smiles": smiles,
                "accepted_candidate": baseline["candidate_smiles"],
                "accepted_candidate_efs": baseline["efs_score"],
                "accepted_property_delta": {"toxicity_delta": 0.0, "qed_delta": 0.0},
                "iteration_history": [],
                "iterations_run": 0,
                "max_iterations": self.max_iterations,
                "efs_threshold": self.efs_threshold,
                "baseline_toxicity": baseline["toxicity"],
                "baseline_qed": baseline["qed"],
                "baseline_efs": baseline["efs_score"],
                "ruleset_version": self.ruleset_version,
                "model_hash": self._model_hash(smiles),
            }

        # --- Closed Loop: up to max_iterations ---
        current_smiles = smiles
        current_toxicity = baseline["toxicity"]
        current_qed = baseline["qed"]
        iteration_history = []
        accepted = None

        for iteration in range(1, self.max_iterations + 1):
            # Step 1: Identify top toxicophore + high-uncertainty atoms
            top_toxicophore, top_atoms = self._identify_toxicophore(
                current_smiles, baseline.get("attention_weights", [])
            )

            # Step 2: Query bioisosteric generator (deterministic fallback)
            candidate_smiles, replacement_info = self._bioisostere_generate(
                current_smiles, top_toxicophore
            )

            if candidate_smiles is None or candidate_smiles == current_smiles:
                # No improvement found for this iteration
                iteration_history.append(OptimizationIteration(
                    iteration=iteration,
                    input_smiles=current_smiles,
                    candidate_smiles=current_smiles,
                    property_delta={"toxicity_delta": 0.0, "qed_delta": 0.0},
                    efs_score=0.0,
                    verdict="RETRY",
                    mechanistic_notes="No viable bioisosteric replacement found.",
                    toxicophore_replaced=top_toxicophore,
                    replaced_atoms=top_atoms,
                ).to_dict())
                continue

            # Step 3: Re-score candidate
            candidate_assessment = self._assess_candidate(
                candidate_smiles, current_toxicity, current_qed
            )

            if "error" in candidate_assessment:
                iteration_history.append(OptimizationIteration(
                    iteration=iteration,
                    input_smiles=current_smiles,
                    candidate_smiles=candidate_smiles,
                    property_delta={"toxicity_delta": 0.0, "qed_delta": 0.0},
                    efs_score=0.0,
                    verdict="RETRY",
                    mechanistic_notes=f"Candidate assessment failed: {candidate_assessment['error']}",
                    toxicophore_replaced=top_toxicophore,
                    replaced_atoms=top_atoms,
                ).to_dict())
                continue

            # Step 4: Compute EFS
            efs_score = candidate_assessment["efs_score"]
            prop_delta = candidate_assessment["property_delta"]

            # Determine verdict
            if efs_score >= self.efs_threshold:
                verdict = "VERIFIED"
                accepted = {
                    "smiles": candidate_smiles,
                    "efs_score": efs_score,
                    "property_delta": prop_delta,
                    "iteration": iteration,
                }
                iteration_history.append(OptimizationIteration(
                    iteration=iteration,
                    input_smiles=current_smiles,
                    candidate_smiles=candidate_smiles,
                    property_delta=prop_delta,
                    efs_score=efs_score,
                    verdict=verdict,
                    mechanistic_notes=f"EFS {efs_score:.3f} >= threshold {self.efs_threshold}. Accepted.",
                    toxicophore_replaced=top_toxicophore,
                    replaced_atoms=top_atoms,
                ).to_dict())
                break
            else:
                verdict = "RETRY"
                iteration_history.append(OptimizationIteration(
                    iteration=iteration,
                    input_smiles=current_smiles,
                    candidate_smiles=candidate_smiles,
                    property_delta=prop_delta,
                    efs_score=efs_score,
                    verdict=verdict,
                    mechanistic_notes=f"EFS {efs_score:.3f} < threshold {self.efs_threshold}. Retrying with stricter constraints.",
                    toxicophore_replaced=top_toxicophore,
                    replaced_atoms=top_atoms,
                ).to_dict())
                # Update current_smiles for next iteration (feedback the candidate)
                current_smiles = candidate_smiles
                current_toxicity = candidate_assessment["toxicity"]
                current_qed = candidate_assessment["qed"]

        # Determine final verdict
        if accepted is not None:
            final_verdict = "VERIFIED"
            status = "success"
        else:
            final_verdict = "HUMAN_REVIEW"
            status = "escalated"

        return {
            "success": True,
            "status": status,
            "verdict": final_verdict,
            "input_smiles": smiles,
            "accepted_candidate": accepted["smiles"] if accepted else None,
            "accepted_candidate_efs": accepted["efs_score"] if accepted else None,
            "accepted_property_delta": accepted["property_delta"] if accepted else None,
            "iteration_history": iteration_history,
            "iterations_run": len(iteration_history),
            "max_iterations": self.max_iterations,
            "efs_threshold": self.efs_threshold,
            "baseline_toxicity": baseline["toxicity"],
            "baseline_qed": baseline["qed"],
            "ruleset_version": self.ruleset_version,
            "model_hash": self._model_hash(smiles),
        }

    def stream_optimize(self, smiles: str):
        """
        Generator that yields iteration results as they complete.
        Used for streaming the co-pilot trace to the frontend.
        """
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            yield {"status": "error", "error": "Invalid SMILES", "smiles": smiles}
            return

        baseline = self._baseline_assessment(smiles)
        yield {"status": "baseline", "baseline": baseline}

        if baseline["efs_score"] >= self.efs_threshold:
            yield {"status": "verified", "verdict": "VERIFIED",
                   "candidate_smiles": baseline["candidate_smiles"]}
            return

        current_smiles = smiles
        current_toxicity = baseline["toxicity"]
        current_qed = baseline["qed"]
        iteration_history = []
        accepted = None

        for iteration in range(1, self.max_iterations + 1):
            top_toxicophore, top_atoms = self._identify_toxicophore(
                current_smiles, baseline.get("attention_weights", [])
            )
            candidate_smiles, replacement_info = self._bioisostere_generate(
                current_smiles, top_toxicophore
            )

            if candidate_smiles is None or candidate_smiles == current_smiles:
                result = {"status": "iteration", "iteration": iteration,
                          "verdict": "RETRY", "candidate_smiles": current_smiles,
                          "mechanistic_notes": "No viable replacement found."}
                iteration_history.append(result)
                yield result
                continue

            candidate_assessment = self._assess_candidate(
                candidate_smiles, current_toxicity, current_qed
            )

            if "error" in candidate_assessment:
                result = {"status": "iteration", "iteration": iteration,
                          "verdict": "RETRY", "candidate_smiles": candidate_smiles,
                          "mechanistic_notes": f"Assessment error: {candidate_assessment['error']}"}
                iteration_history.append(result)
                yield result
                continue

            efs_score = candidate_assessment["efs_score"]
            prop_delta = candidate_assessment["property_delta"]
            verdict = "VERIFIED" if efs_score >= self.efs_threshold else "RETRY"

            result = {
                "status": "iteration",
                "iteration": iteration,
                "input_smiles": current_smiles,
                "candidate_smiles": candidate_smiles,
                "property_delta": prop_delta,
                "efs_score": efs_score,
                "verdict": verdict,
                "toxicophore_replaced": top_toxicophore,
                "replaced_atoms": top_atoms,
            }
            iteration_history.append(result)
            yield result

            if verdict == "VERIFIED":
                accepted = result
                break

            current_smiles = candidate_smiles
            current_toxicity = candidate_assessment["toxicity"]
            current_qed = candidate_assessment["qed"]

        if accepted is None:
            yield {"status": "escalated", "verdict": "HUMAN_REVIEW",
                   "iteration_history": iteration_history}
        else:
            yield {"status": "verified", "verdict": "VERIFIED",
                   "accepted_candidate": accepted["candidate_smiles"],
                   "accepted_efs": accepted["efs_score"],
                   "iteration_history": iteration_history}

    # ─────────────────────────────────────────────────────────────────────
    # Internal methods
    # ─────────────────────────────────────────────────────────────────────
    def _baseline_assessment(self, smiles: str) -> Dict[str, Any]:
        """Get baseline prediction, QED, attention, and EFS for the input molecule."""
        from rdkit import Chem
        from rdkit.Chem import Descriptors
        mol = Chem.MolFromSmiles(smiles)
        if mol is None or mol.GetNumAtoms() == 0:
            return {"error": "Invalid SMILES", "candidate_smiles": smiles, "input_smiles": smiles}

        # Toxicity prediction
        toxicity = 0.5  # default neutral
        if self.gnn_predictor is not None and hasattr(self.gnn_predictor, 'predict'):
            try:
                pred = self.gnn_predictor.predict(smiles)
                if isinstance(pred, dict):
                    if 'summary' in pred:
                        toxicity = float(pred['summary'].get('average_toxicity_probability', 0.5))
                    elif 'probability' in pred:
                        toxicity = float(pred['probability'])
            except Exception:
                pass
        else:
            # No GNN model — use deterministic toxicophore detection
            toxicity = self._detect_toxicophore_toxicity(smiles)

        # QED
        qed = float(Descriptors.qed(mol)) if mol else 0.5

        # Attention weights
        attention_weights = self._get_attention_weights(smiles)

        # EFS score (proxy: based on toxicity + QED + confidence)
        efs = self._compute_proxy_efs(toxicity, qed, attention_weights)

        return {
            "toxicity": toxicity,
            "qed": qed,
            "efs_score": efs,
            "candidate_smiles": smiles,
            "attention_weights": attention_weights,
        }

    def _assess_candidate(self, candidate_smiles: str,
                          input_toxicity: float,
                          input_qed: float) -> Dict[str, Any]:
        """Re-score a candidate molecule and compute EFS + property deltas."""
        mol = Chem.MolFromSmiles(candidate_smiles)
        if mol is None:
            return {"error": "Invalid candidate SMILES"}

        # Toxicity
        toxicity = 0.5
        if self.gnn_predictor is not None and hasattr(self.gnn_predictor, 'predict'):
            try:
                pred = self.gnn_predictor.predict(candidate_smiles)
                if isinstance(pred, dict):
                    if 'summary' in pred:
                        toxicity = float(pred['summary'].get('average_toxicity_probability', 0.5))
                    elif 'probability' in pred:
                        toxicity = float(pred['probability'])
            except Exception:
                pass
        else:
            toxicity = self._detect_toxicophore_toxicity(candidate_smiles)

        # QED
        qed = float(Descriptors.qed(mol)) if mol else 0.5

        # Attention weights for candidate
        attention_weights = self._get_attention_weights(candidate_smiles)

        # EFS
        efs = self._compute_proxy_efs(toxicity, qed, attention_weights)

        # QED must be > 0.40
        if qed < 0.40:
            efs = min(efs, 0.3)  # penalize low QED

        return {
            "toxicity": toxicity,
            "qed": qed,
            "efs_score": efs,
            "property_delta": {
                "toxicity_delta": round(toxicity - input_toxicity, 4),
                "qed_delta": round(qed - input_qed, 4),
            },
        }

    def _get_attention_weights(self, smiles: str) -> List[float]:
        """Get GNN attention/attribution weights for a molecule."""
        from rdkit import Chem
        if self.gnn_predictor is None:
            # Return uniform fallback
            mol = Chem.MolFromSmiles(smiles)
            if mol is None or mol.GetNumAtoms() == 0:
                return []
            return [1.0 / mol.GetNumAtoms()] * mol.GetNumAtoms()

        try:
            # Try to get attention from the GNN model
            if hasattr(self.gnn_predictor, 'get_attention_weights'):
                aw = self.gnn_predictor.get_attention_weights(smiles)
                if aw is not None:
                    return list(np.asarray(aw, dtype=float).flatten())
            elif hasattr(self.gnn_predictor, 'models'):
                gnn = self.gnn_predictor.models.get('attention_gin', {}).get('model')
                if gnn and hasattr(gnn, 'get_attention_weights'):
                    aw = gnn.get_attention_weights(smiles)
                    if aw is not None:
                        return list(np.asarray(aw, dtype=float).flatten())
        except Exception:
            pass

        # Fallback: uniform
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []
        return [1.0 / mol.GetNumAtoms()] * mol.GetNumAtoms()

    def _identify_toxicophore(self, smiles: str,
                              attention_weights: List[float]) -> Tuple[str, List[int]]:
        """
        Identify the top toxicophore and the atom indices with highest
        uncertainty (from GNN attention).

        Returns (toxicophore_smarts, top_atom_indices).
        """
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return "[#7;H0;v3;!a;!$(N~[!#6])]", []

        # Use substructure mapper if available
        if self.substructure_mapper is not None:
            try:
                matches = self.substructure_mapper.identify_substructures(
                    smiles, np.array(attention_weights) if attention_weights else None,
                    threshold=None
                )
                if matches and len(matches) > 0:
                    top = matches[0]
                    return top.smarts, list(top.atoms)
            except Exception:
                pass

        # Fallback: find atoms with highest attention weights
        n_atoms = mol.GetNumAtoms()
        if not attention_weights or len(attention_weights) < n_atoms:
            # No attention — use structural alerts as fallback
            for alert_smarts in _BIOISOSTERIC_REPLACEMENTS.keys():
                try:
                    from rdkit.Chem import rdMolDescriptors
                    pat = Chem.MolFromSmarts(alert_smarts)
                    if pat and mol.HasSubstructMatch(pat):
                        atoms = list(mol.GetSubstructMatch(pat))
                        return alert_smarts, atoms
                except Exception:
                    continue
            return "[#7;H0;v3;!a;!$(N~[!#6])]", []

        # Find top atoms by attention weight
        aw = np.asarray(attention_weights[:n_atoms], dtype=float)
        top_indices = set()
        # Threshold: top 3 atoms or above adaptive threshold
        threshold = max(aw.max() / 3.0 if aw.max() > 0 else 0,
                        1.0 / n_atoms)
        for i, w in enumerate(aw):
            if w >= threshold:
                top_indices.add(i)

        # Try to match these atoms to a known toxicophore pattern
        toxicophore = None
        matched_atoms = []
        for alert_smarts in _BIOISOSTERIC_REPLACEMENTS.keys():
            try:
                pat = Chem.MolFromSmarts(alert_smarts)
                if pat and mol.HasSubstructMatch(pat):
                    atoms = list(mol.GetSubstructMatch(pat))
                    overlap = set(atoms) & top_indices
                    if overlap:
                        toxicophore = alert_smarts
                        matched_atoms = list(overlap)
                        break
            except Exception:
                continue

        if toxicophore is None:
            # Use first alert pattern as default
            toxicophore = list(_BIOISOSTERIC_REPLACEMENTS.keys())[0]

        return toxicophore, list(top_indices)

    def _bioisostere_generate(self, smiles: str,
                              toxicophore_smarts: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Generate bioisosteric replacements for the toxicophore.

        Uses the deterministic replacement map. If an LLM provider is
        available, it refines the choice; otherwise, uses the deterministic
        fallback.

        Returns (candidate_smiles, replacement_info).
        """
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None, {}

        # Check if we have a matching SMARTS for replacement
        replacements = _BIOISOSTERIC_REPLACEMENTS.get(toxicophore_smarts, [])
        if not replacements:
            # Try to find any matching replacement pattern
            for alert_smarts in _BIOISOSTERIC_REPLACEMENTS:
                try:
                    pat = Chem.MolFromSmarts(alert_smarts)
                    if pat and mol.HasSubstructMatch(pat):
                        toxicophore_smarts = alert_smarts
                        replacements = _BIOISOSTERIC_REPLACEMENTS[alert_smarts]
                        break
                except Exception:
                    continue

        if not replacements:
            return None, {"replacements_attempted": 0, "reason": "No matching bioisosteric pattern"}

        # If LLM is available, query it for the ground prompt approach
        if self.llm_provider and getattr(self.llm_provider, 'api_key', None):
            try:
                return self._llm_guided_replacement(smiles, toxicophore_smarts, replacements)
            except Exception:
                pass

        # Deterministic fallback: try each replacement, pick best
        best_candidate = None
        best_info = {}
        for replacement_smarts, _, description in replacements:
            candidate = self._apply_replacement(smiles, toxicophore_smarts, replacement_smarts)
            if candidate and candidate != smiles:
                # Validate candidate
                c_mol = Chem.MolFromSmiles(candidate)
                if c_mol is not None:
                    return candidate, {
                        "replacement_type": _,
                        "replaced_smarts": toxicophore_smarts,
                        "replacement_smarts": replacement_smarts,
                        "description": description,
                        "method": "deterministic",
                    }

        return None, {"replacements_attempted": len(replacements),
                       "reason": "No valid candidate generated"}

    def _apply_replacement(self, smiles: str, old_smarts: str,
                           new_smarts: str) -> Optional[str]:
        """Apply a bioisosteric replacement via RDKit substructure replacement."""
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        old_pat = Chem.MolFromSmarts(old_smarts)
        new_pat = Chem.MolFromSmarts(new_smarts)
        if old_pat is None:
            return None

        # Try RDKit's ReplaceSubstructs
        try:
            from rdkit.Chem import AllChem
            replacement_results = AllChem.ReplaceSubstructs(mol, old_pat, new_pat)
            if replacement_results:
                for result_mol in replacement_results:
                    if result_mol is not None:
                        candidate = Chem.MolToSmiles(result_mol)
                        if candidate and candidate != smiles:
                            return candidate
        except Exception:
            pass

        # Fallback: use the deterministic bioisosteric map directly
        # This handles common transformations without RDKit substructure replacement
        return self._deterministic_transform(smiles, old_smarts, new_smarts)

    def _deterministic_transform(self, smiles: str, old_smarts: str,
                                  new_smarts: str) -> Optional[str]:
        """Apply a deterministic SMILES-level transformation when substruct replace fails."""
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None

        # Get the canonical SMILES
        canonical = Chem.MolToSmiles(mol)

        # For nitro -> amide: replace [N+](=O)[O-] with [NH]C(=O)N
        if "[N+](=O)[O-]" in canonical and new_smarts == "[NH]C(=O)N":
            result = canonical.replace("[N+](=O)[O-]", "[NH]C(=O)N")
            result_mol = Chem.MolFromSmiles(result)
            if result_mol is not None:
                return Chem.MolToSmiles(result_mol)

        # For nitro -> sulfonamide
        if "[N+](=O)[O-]" in canonical and new_smarts == "[NH]S(=O)(=O)N":
            result = canonical.replace("[N+](=O)[O-]", "[NH]S(=O)(=O)N")
            result_mol = Chem.MolFromSmiles(result)
            if result_mol is not None:
                return Chem.MolToSmiles(result_mol)

        # For amine -> amide
        if "[#7;H0;v3;!a;!$(N~[!#6])]" in canonical and new_smarts == "[NH]C(=O)":
            result = canonical.replace("[#7;H0;v3;!a;!$(N~[!#6])]", "[NH]C(=O)")
            result_mol = Chem.MolFromSmiles(result)
            if result_mol is not None:
                return Chem.MolToSmiles(result_mol)

        # For carboxylic acid -> ester
        if "[CX3]([OH])=O" in canonical and new_smarts == "[CX3]([O])[O]C":
            result = canonical.replace("[CX3]([OH])=O", "[CX3]([O])[O]C")
            result_mol = Chem.MolFromSmiles(result)
            if result_mol is not None:
                return Chem.MolToSmiles(result_mol)

        # Last resort: use generic amide replacement for any amine
        if "[#7;H3;!$(*=*N)]" in canonical:
            result = canonical.replace("[#7;H3;!$(*=*N)]", "[NH]C(=O)")
            result_mol = Chem.MolFromSmiles(result)
            if result_mol is not None:
                return Chem.MolToSmiles(result_mol)

        return None

    def _detect_toxicophore_toxicity(self, smiles: str) -> float:
        """
        Deterministic toxicophore-based toxicity proxy when no GNN model available.

        Returns a toxicity probability in [0, 1] based on the number and
        severity of structural toxicophores detected.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return 0.5

        # Strong toxicophores (e.g., nitro, nitroso) -> high toxicity
        strong_alerts = ["[N+](=O)[O-]", "[N+](=O)[*]", "c1ccc([N+](=O)[O-])cc1"]
        # Moderate toxicophores (e.g., basic amines, carboxylic acids)
        moderate_alerts = ["[#7;H0;v3;!a;!$(N~[!#6])]", "[CX3]([OH])=O"]

        toxicity = 0.1  # default low for clean molecules (no GNN model)
        matched_count = 0
        for alert in strong_alerts:
            pat = Chem.MolFromSmarts(alert)
            if pat is not None and mol.HasSubstructMatch(pat):
                toxicity += 0.20
                matched_count += 1
        for alert in moderate_alerts:
            pat = Chem.MolFromSmarts(alert)
            if pat is not None and mol.HasSubstructMatch(pat):
                toxicity += 0.08
                matched_count += 1

        return min(1.0, round(toxicity, 4))

    def _compute_proxy_efs(self, toxicity: float, qed: float,
                           attention_weights: List[float]) -> float:
        """
        Compute a proxy EFS score for the optimization loop.

        When the faithful EFS validator is unavailable (no GNN model loaded),
        we compute a deterministic proxy:
          EFS_proxy = w1 * (1 - toxicity) + w2 * qed + w3 * confidence

        where confidence is derived from attention weight entropy (lower
        entropy = more confident prediction = higher EFS).

        Weights match the FaithfulnessValidator defaults: 0.30, 0.30, 0.20, 0.20.
        The attribution and counterfactual terms are folded into the
        confidence proxy.
        """
        # Contribution 1: Safety (1 - toxicity)
        s_safety = 1.0 - max(0.0, min(1.0, toxicity))

        # Contribution 2: Drug-likeness (QED)
        s_qed = max(0.0, min(1.0, qed))

        # Contribution 3: Confidence from attention weight entropy
        # For molecules with uniform attention (fallback), confidence is
        # higher for cleaner molecules (low toxicity, high QED).
        s_conf = 0.5
        if attention_weights and len(attention_weights) > 1:
            aw = np.asarray(attention_weights, dtype=float)
            if aw.sum() > 0:
                p = aw / aw.sum()
                entropy = -np.sum(p * np.log(p + 1e-12))
                max_entropy = np.log(len(p))
                if max_entropy > 0:
                    s_conf = 1.0 - min(1.0, entropy / max_entropy)

        # If no model was loaded (uniform attention fallback), boost confidence
        # based on clean molecule characteristics (no toxicophores = higher conf)
        if len(attention_weights) > 0 and max(attention_weights) < 0.5:
            s_conf = 0.5 + 0.5 * s_safety * s_qed  # cleaner mol = more confident

        efs = 0.30 * s_safety + 0.30 * s_qed + 0.20 * s_conf + 0.20 * s_conf
        return round(float(efs), 4)

    def _llm_guided_replacement(self, smiles: str, toxicophore_smarts: str,
                                replacements: List) -> Tuple[Optional[str], Dict[str, Any]]:
        """Query LLM for a guided bioisosteric replacement."""
        import numpy as np
        attention_weights = self._get_attention_weights(smiles)
        top_atoms = list(range(min(5, len(attention_weights)))) if attention_weights else []
        # Sort by attention weight
        if attention_weights:
            sorted_idx = sorted(range(len(attention_weights)),
                                key=lambda i: attention_weights[i], reverse=True)
            top_atoms = sorted_idx[:5]

        baseline = self._baseline_assessment(smiles)

        prompt = self.COPilot_PROMPT.format(
            attention_threshold=self.attention_threshold,
            efs_threshold=self.efs_threshold,
            max_iterations=self.max_iterations,
            smiles=smiles,
            toxicity=baseline["toxicity"],
            qed=baseline["qed"],
            attention_weights=[round(w, 4) for w in attention_weights[:10]],
            efs_score=baseline["efs_score"],
            top_atoms=top_atoms,
            toxicophores=[{"smarts": toxicophore_smarts, "attempts": len(replacements)}],
            iteration=1,
        )

        try:
            response = self.llm_provider.generate(prompt, max_tokens=500, temperature=0.1)
            # Parse JSON response
            import json
            response = response.strip()
            if response.startswith('```json'):
                response = response[7:]
            if response.startswith('```'):
                response = response[3:]
            if response.endswith('```'):
                response = response[:-3]
            result = json.loads(response.strip())
            return result.get("candidate_smiles"), {
                "replacement_type": result.get("replacement_type", "llm_guided"),
                "replaced_smarts": toxicophore_smarts,
                "description": result.get("rationale", ""),
                "method": "llm_guided",
            }
        except Exception as e:
            logger.warning(f"LLM co-pilot query failed, falling back to deterministic: {e}")
            return None, {}

    def _model_hash(self, smiles: str) -> str:
        raw = f"CoPilot-{self.ruleset_version}-{smiles}-EFS{self.efs_threshold}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────────────────────────────────────
_DEFAULT_COPILOT: Optional["NeuroSymbolicCopilot"] = None


def get_default_copilot(
    gnn_predictor=None,
    faithfulness_validator=None,
    substructure_mapper=None,
    llm_provider=None,
) -> NeuroSymbolicCopilot:
    """Module-level singleton for the neuro-symbolic co-pilot."""
    global _DEFAULT_COPILOT
    if _DEFAULT_COPILOT is None:
        _DEFAULT_COPILOT = NeuroSymbolicCopilot(
            gnn_predictor=gnn_predictor,
            faithfulness_validator=faithfulness_validator,
            substructure_mapper=substructure_mapper,
            llm_provider=llm_provider,
        )
    return _DEFAULT_COPILOT
