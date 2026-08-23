#!/usr/bin/env python3
"""
Multi-Component Formulation & Excipient Screening Engine
=========================================================
Phase 2 — Formulation Stability, Chemical Incompatibility, and
Synergistic Toxicity / Exposure Scoring.

Blend rule prior (P_rule) with GNN/Tanimoto embedding similarity
(P_embed) to detect pairwise chemical incompatibilities and compute
a formulation-level bioactivation + synergy risk profile.

P_incompatible = 0.60 · P_rule + 0.40 · P_embed

Reference: FDA Guidance for Industry: Manufacturing Chemical
Safety, 2024.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('FormulationEngine')

# ─────────────────────────────────────────────────────────────────────────────
# Component database: known toxicophores and reactive groups
# ─────────────────────────────────────────────────────────────────────────────
# Reducing sugars (for Maillard detection) — generic patterns matching
# the carbonyl / hemiacetal motif of reducing sugars
SUGAR_SMARTS = {
    "Lactose": "O[C@H]1[C@@H]([C@H]([C@@H]([C@H](O1)CO)O)O)O",
    "Sucrose": "OC[C@H]1O[C@@H](O)[CH](O)[CH](O)[CH]1",
    "Glucose": "OC[C@H]1O[C@H](O)[C@H](O)[C@@H](O)[C@H]1O",
    "Fructose": "OC[C@@H]1O[C@H](O)[CH](O)[CH](O)[CH]1",
    "Generic reducing sugar": "[CH]1O[C@@H]([C@@H]([C@H]([C@H]([C@@H]1O)O)O)O)CO",
}

# Also detect reducing-end motif (free aldehyde/ketone in sugar context)
REDUCING_SUGAR_SMARTS = "[O,C][CH]1[O,[CH]O][C@@H]([C@H](O)[C@H](O)[C@H]1O)CO"

# Primary / secondary amine moieties (for Maillard reaction)
AMINE_SMARTS = [
    "[NH2]-c1ccccc1",     # primary aromatic amine
    "[NH]-c1ccccc1",       # secondary aromatic amine
    "[NH2]C",             # primary aliphatic amine
    "[NH]C",              # secondary aliphatic amine
]

# Ester / carbonyl moieties (for hydrolysis risk) — only true esters,
# not amides (C=O-N is too stable for hydrolysis under formulation conditions)
ESTER_SMARTS = [
    "C(=O)OC",            # ester (excluding amides)
]

# Basic / nucleophilic excipients
NUCLEOPHIC_SMARTS = ["[OH]", "[NH2]", "[NH1]"]

# Oxidation-sensitive moieties (thioethers, phenols, sulfides)
OXIDATION_SMARTS = [
    "c1cc(O)cc1",         # phenol
    "SC",                  # thioether
    "c1sccc1",            # thiophene
]

# Peroxide / oxidizing excipients
PEROXIDE_SMARTS = {
    "Polysorbate 80": "C/C(=C/CO)CCCCC",
    "Povidone": "CCN(CC)CC",
    "Hydrogen Peroxide": "OO",
}

# Acidic excipients
ACIDIC_SMARTS = {
    "Citric Acid": "OC(=O)C(O)(C(O)O)O",
    "Tartaric Acid": "OC(=O)C(O)C(O)C(=O)O",
}

# Basic excipients
BASIC_SMARTS = {
    "Magnesium Stearate": "CCCCCCCCCC(=O)O[MgH]",
    "Aluminum Hydroxide": "O[AlH](O)O",
}


# ─────────────────────────────────────────────────────────────────────────────
# Risk scoring constants
# ─────────────────────────────────────────────────────────────────────────────
P_RULE_WEIGHT = 0.60
P_EMBED_WEIGHT = 0.40


class FormulationEngine:
    """Multi-component formulation screening engine.

    Detects chemical incompatibilities between APIs and excipients,
    computes synergistic toxicity / exposure scores, and returns a
    structured stability verdict.
    """

    def __init__(self, gnn_model=None):
        """Initialize with optional GNN model for embedding similarity.

        Args:
            gnn_model: Optional trained model with get_embedding() method.
                       Falls back to RDKit Morgan fingerprints if unavailable.
        """
        self.gnn_model = gnn_model
        self._fp_cache: Dict[str, Any] = {}

    # ─────────────────────────────────────────────────────────────────────
    # Fingerprint / embedding computation
    # ─────────────────────────────────────────────────────────────────────
    def _compute_fingerprint(self, smiles: str) -> Any:
        """Compute a Morgan fingerprint for embedding similarity (fallback)."""
        from rdkit import Chem
        from rdkit.Chem import AllChem
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            return None
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, 2, nBits=1024)
        return fp

    def _embedding_similarity(self, smiles_a: str, smiles_b: str) -> float:
        """Compute Tanimoto (or cosine) similarity between two components.

        Uses GNN embedding if available, else RDKit Morgan fingerprint.
        Returns 0.0–1.0 (higher = more similar).
        """
        if self.gnn_model and hasattr(self.gnn_model, 'get_embedding'):
            try:
                emb_a = self.gnn_model.get_embedding(smiles_a)
                emb_b = self.gnn_model.get_embedding(smiles_b)
                if emb_a is not None and emb_b is not None:
                    import numpy as np
                    dot = float(np.dot(emb_a, emb_b))
                    norm_a = float(np.linalg.norm(emb_a))
                    norm_b = float(np.linalg.norm(emb_b))
                    if norm_a == 0 or norm_b == 0:
                        return 0.0
                    return dot / (norm_a * norm_b)
            except Exception as e:
                logger.debug(f"GNN embedding failed, falling back to fingerprint: {e}")

        # Fallback: RDKit Morgan fingerprint Tanimoto
        from rdkit import Chem
        from rdkit.Chem import AllChem, DataStructs
        from rdkit import RDLogger
        RDLogger.DisableLog('rdApp.*')

        fp_a = self._get_or_compute_fp(smiles_a)
        fp_b = self._get_or_compute_fp(smiles_b)
        if fp_a is None or fp_b is None:
            return 0.0
        try:
            sim = DataStructs.TanimotoSimilarity(fp_a, fp_b)
            return float(sim)
        except Exception:
            return 0.0

    def _get_or_compute_fp(self, smiles: str) -> Any:
        if smiles not in self._fp_cache:
            self._fp_cache[smiles] = self._compute_fingerprint(smiles)
        return self._fp_cache[smiles]

    # ─────────────────────────────────────────────────────────────────────
    # SMARTS-based rule matching
    # ─────────────────────────────────────────────────────────────────────
    def _has_substructure(self, mol, smarts: str) -> bool:
        from rdkit import Chem
        from rdkit import RDLogger
        RDLogger.DisableLog('rdApp.*')
        try:
            pattern = Chem.MolFromSmarts(smarts)
            return pattern is not None and mol.HasSubstructMatch(pattern)
        except Exception:
            return False

    def _match_alert_count(self, mol, smarts_list: List[str]) -> int:
        return sum(1 for s in smarts_list if self._has_substructure(mol, s))

    def _component_risk(self, component: Dict, mol, all_mols: List) -> float:
        """Compute individual component risk based on reactivity motifs."""
        risk = 0.0
        smiles = component.get("smiles", "")

        # Oxidation risk (0.3 if phenol/thiophene present)
        for s in OXIDATION_SMARTS:
            if self._has_substructure(mol, s):
                risk += 0.3
                break

        # Ester / hydrolysis risk (0.2)
        for s in ESTER_SMARTS:
            if self._has_substructure(mol, s):
                risk += 0.2
                break

        # Nitrenium / aromatic amine (0.4)
        for s in AMINE_SMARTS:
            if self._has_substructure(mol, s):
                risk += 0.4
                break

        return min(risk, 1.0)

    # ─────────────────────────────────────────────────────────────────────
    # Incompatibility detection
    # ─────────────────────────────────────────────────────────────────────
    def _detect_incompatibility(
        self, comp_a: Dict, comp_b: Dict, mol_a, mol_b
    ) -> Optional[Dict[str, Any]]:
        """Detect a specific chemical incompatibility between two components.

        Returns {pair, risk, mechanism, p_rule, p_embed} or None.
        """
        from rdkit import RDLogger
        RDLogger.DisableLog('rdApp.*')

        name_a = comp_a.get("name", "unknown")
        name_b = comp_b.get("name", "unknown")
        role_a = comp_a.get("role", "")
        role_b = comp_b.get("role", "")
        smiles_a = comp_a.get("smiles", "")
        smiles_b = comp_b.get("smiles", "")

        p_rule = 0.0
        mechanism = ""
        risk_level = "LOW"

        # 1. Maillard reaction: amine + reducing sugar
        is_sugar_a = any(self._has_substructure(mol_a, s) for s in SUGAR_SMARTS.values())
        is_sugar_b = any(self._has_substructure(mol_b, s) for s in SUGAR_SMARTS.values())
        has_amine_a = any(self._has_substructure(mol_a, s) for s in AMINE_SMARTS)
        has_amine_b = any(self._has_substructure(mol_b, s) for s in AMINE_SMARTS)

        if (has_amine_a and is_sugar_b) or (has_amine_b and is_sugar_a):
            p_rule = 0.9
            mechanism = "Maillard reaction: primary/secondary amine + reducing sugar → brown pigments, loss of potency"
            risk_level = "HIGH"

        # 2. Ester hydrolysis / transesterification
        if not mechanism:
            has_ester_a = any(self._has_substructure(mol_a, s) for s in ESTER_SMARTS)
            has_ester_b = any(self._has_substructure(mol_b, s) for s in ESTER_SMARTS)
            has_nuc_a = any(self._has_substructure(mol_a, s) for s in NUCLEOPHIC_SMARTS)
            has_nuc_b = any(self._has_substructure(mol_b, s) for s in NUCLEOPHIC_SMARTS)
            if (has_ester_a and has_nuc_b) or (has_ester_b and has_nuc_a):
                p_rule = 0.7
                mechanism = "Ester hydrolysis / transesterification: nucleophilic excipient degrades ester API"
                risk_level = "MEDIUM"

        # 3. Oxidation: sensitive moiety + peroxide-containing excipient
        if not mechanism:
            has_oxidizable_a = any(self._has_substructure(mol_a, s) for s in OXIDATION_SMARTS)
            has_oxidizable_b = any(self._has_substructure(mol_b, s) for s in OXIDATION_SMARTS)
            has_peroxide_a = any(self._has_substructure(mol_a, s) for s in PEROXIDE_SMARTS.values())
            has_peroxide_b = any(self._has_substructure(mol_b, s) for s in PEROXIDE_SMARTS.values())
            if (has_oxidizable_a and has_peroxide_b) or (has_oxidizable_b and has_peroxide_a):
                p_rule = 0.65
                mechanism = "Oxidation: peroxide-containing excipient oxidizes sensitive moiety"
                risk_level = "MEDIUM"

        # 4. Acid-base precipitation
        if not mechanism:
            has_acid_a = any(self._has_substructure(mol_a, s) for s in ACIDIC_SMARTS.values())
            has_acid_b = any(self._has_substructure(mol_b, s) for s in ACIDIC_SMARTS.values())
            has_base_a = any(self._has_substructure(mol_a, s) for s in BASIC_SMARTS.values())
            has_base_b = any(self._has_substructure(mol_b, s) for s in BASIC_SMARTS.values())
            if (has_acid_a and has_base_b) or (has_acid_b and has_base_a):
                p_rule = 0.75
                mechanism = "Acid-base incompatibility: basic excipient deprotonates acidic API → precipitation/degradation"
                risk_level = "HIGH"

        # No rule-based match → use embedding similarity only
        if not mechanism:
            p_embed = self._embedding_similarity(smiles_a, smiles_b)
            if p_embed > 0.95:
                # Very similar structures → potential synergistic metabolism
                p_rule = 0.2
                mechanism = "Structural similarity: shared metabolic pathway may cause competitive inhibition"
                risk_level = "LOW"
            else:
                return None  # no incompatibility detected

        # Compute embedding similarity
        p_embed = self._embedding_similarity(smiles_a, smiles_b)

        # Blend: 60% rule + 40% embedding for the final score
        # But for HIGH-risk rule matches (p_rule >= 0.8), the rule confidence
        # dominates — embedding similarity should only increase, not decrease
        p_incompatible = P_RULE_WEIGHT * p_rule + P_EMBED_WEIGHT * p_embed
        if p_rule >= 0.8:
            # Rule-based high-risk alert: take the max to avoid dilution
            p_incompatible = max(p_incompatible, p_rule * 0.8)

        # Only report if blended risk exceeds threshold
        if p_incompatible < 0.3:
            return None

        # Map to risk label
        if p_incompatible >= 0.7:
            risk_level = "HIGH"
        elif p_incompatible >= 0.5:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "pair": [name_a, name_b],
            "risk": risk_level,
            "p_incompatible": round(p_incompatible, 4),
            "p_rule": round(p_rule, 4),
            "p_embed": round(p_embed, 4),
            "mechanism": mechanism,
        }

    # ─────────────────────────────────────────────────────────────────────
    # Synergistic toxicity scoring
    # ─────────────────────────────────────────────────────────────────────
    def _compute_synergistic_toxicity(
        self, components: List[Dict], preds: Dict[str, Any]
    ) -> Dict[str, float]:
        """Weight each component's toxicity endpoint by its concentration fraction.

        w_i = dose_i / sum(dose)
        synergy = sum(w_i * tox_i) with amplification if multiple
        components share the same toxicophore.
        """
        total_dose = sum(c.get("dose_mg", 0) for c in components)
        if total_dose <= 0:
            weights = [1.0 / len(components)] * len(components)
        else:
            weights = [c.get("dose_mg", 0) / total_dose for c in components]

        herg_synergy = 0.0
        dili_synergy = 0.0
        ames_synergy = 0.0

        for comp, w in zip(components, weights):
            probs = preds.get(comp.get("smiles", ""), {})
            herg_p = 0.0
            dili_p = 0.0
            ames_p = 0.0
            tox_p = 0.0

            if isinstance(probs, dict):
                for endpoint, val in probs.items():
                    if isinstance(val, dict):
                        p = val.get("probability", 0.0)
                    else:
                        p = float(val) if val else 0.0
                    ep_lower = str(endpoint).lower()
                    if "herg" in ep_lower:
                        herg_p = max(herg_p, p)
                    if "dili" in ep_lower or "hepatotox" in ep_lower:
                        dili_p = max(dili_p, p)
                    if "ames" in ep_lower or "mutagen" in ep_lower:
                        ames_p = max(ames_p, p)
                    if p > 0.5:
                        tox_p = max(tox_p, p)

            # Weight by concentration fraction
            herg_synergy += w * herg_p
            dili_synergy += w * dili_p
            ames_synergy += w * ames_p

        # Synergy amplification: if multiple high-risk components exist,
        # the combined risk is super-additive
        high_risk_count = sum(1 for w in weights if True)
        if high_risk_count > 1:
            herg_synergy = min(1.0, herg_synergy * 1.2)
            dili_synergy = min(1.0, dili_synergy * 1.2)
            ames_synergy = min(1.0, ames_synergy * 1.2)

        return {
            "herg_synergy": round(herg_synergy, 4),
            "dili_synergy": round(dili_synergy, 4),
            "ames_synergy": round(ames_synergy, 4),
        }

    # ─────────────────────────────────────────────────────────────────────
    # Main entry point
    # ─────────────────────────────────────────────────────────────────────
    def screen_formulation(self, components: List[Dict], predictor=None) -> Dict[str, Any]:
        """Screen a multi-component formulation for incompatibilities.

        Args:
            components: List of {"smiles", "name", "role", "dose_mg"}
            predictor: Optional predictor for per-component toxicity preds

        Returns:
            Structured result per the Phase 2 spec.
        """
        from rdkit import Chem
        from rdkit import RDLogger
        RDLogger.DisableLog('rdApp.*')

        # Parse all molecules
        mols = []
        for comp in components:
            mol = Chem.MolFromSmiles(comp.get("smiles", "").strip())
            if mol is None:
                logger.warning(f"Invalid SMILES for component {comp.get('name')}: {comp.get('smiles')}")
                mols.append(None)
            else:
                mols.append(mol)

        # Compute pairwise incompatibility matrix
        incompatibility_matrix = []
        max_risk_score = 0.0
        has_high = False

        for i, (comp_a, mol_a) in enumerate(zip(components, mols)):
            for j, (comp_b, mol_b) in enumerate(zip(components, mols)):
                if i >= j:
                    continue
                if mol_a is None or mol_b is None:
                    continue
                result = self._detect_incompatibility(comp_a, comp_b, mol_a, mol_b)
                if result:
                    incompatibility_matrix.append(result)
                    max_risk_score = max(max_risk_score, result["p_incompatible"])
                    if result["risk"] == "HIGH":
                        has_high = True

        # Compute per-component toxicity predictions
        preds = {}
        if predictor and hasattr(predictor, 'predict'):
            for comp in components:
                smi = comp.get("smiles", "")
                if not smi:
                    continue
                try:
                    p = predictor.predict(smi)
                    preds[smi] = p.get("predictions", p) if isinstance(p, dict) else {}
                except Exception as e:
                    logger.debug(f"Predict failed for {smi}: {e}")

        # Synergistic toxicity
        synergy = self._compute_synergistic_toxicity(components, preds)

        # Determine overall verdict
        if has_high and max_risk_score >= 0.7:
            stability = "CRITICAL_INCOMPATIBILITY"
        elif max_risk_score >= 0.5:
            stability = "WARNING"
        else:
            stability = "STABLE"

        overall_risk = round(max_risk_score * 0.5 + max(synergy.values()) * 0.5, 4)

        # Components summary
        components_summary = []
        for comp, mol in zip(components, mols):
            risk = self._component_risk(comp, mol, [m for m in mols if m is not None]) if mol else 0.0
            components_summary.append({
                "name": comp.get("name", "unknown"),
                "role": comp.get("role", "unknown"),
                "smiles": comp.get("smiles", ""),
                "dose_mg": comp.get("dose_mg", 0),
                "reactivity_risk": round(risk, 2),
            })

        return {
            "formulation_stability": stability,
            "overall_risk_score": overall_risk,
            "incompatibility_matrix": incompatibility_matrix,
            "synergistic_toxicity": synergy,
            "components_summary": components_summary,
            "n_components": len(components),
            "n_incompatibilities": len(incompatibility_matrix),
            "max_pairwise_risk": round(max_risk_score, 4),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Self-test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    engine = FormulationEngine()

    # Test 1: Paracetamol + Lactose (Maillard)
    result = engine.screen_formulation([
        {"name": "Paracetamol", "smiles": "CC(=O)Nc1ccc(O)cc1", "role": "API", "dose_mg": 500},
        {"name": "Lactose", "smiles": "OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@H]1O", "role": "excipient", "dose_mg": 100},
        {"name": "Mg Stearate", "smiles": "CCCCCCCCCC(=O)O[Mg+]", "role": "excipient", "dose_mg": 5},
    ])
    print(f"Test 1 - Stability: {result['formulation_stability']}, "
          f"Risk: {result['overall_risk_score']}, "
          f"Incompatibilities: {result['n_incompatibilities']}")

    # Test 2: Clean formulation (Paracetamol + Starch)
    result2 = engine.screen_formulation([
        {"name": "Paracetamol", "smiles": "CC(=O)Nc1ccc(O)cc1", "role": "API", "dose_mg": 500},
        {"name": "Starch", "smiles": "OC[C@@H]1[C@H](O)C(O)(C)OC1", "role": "excipient", "dose_mg": 100},
    ])
    print(f"Test 2 - Stability: {result2['formulation_stability']}, "
          f"Risk: {result2['overall_risk_score']}, "
          f"Incompatibilities: {result2['n_incompatibilities']}")
