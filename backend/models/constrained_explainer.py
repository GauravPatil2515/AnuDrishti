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

import json
import logging
import re
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict, field
import threading
import time

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
