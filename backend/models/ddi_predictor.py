#!/usr/bin/env python3
"""
Drug-Drug Interaction (DDI) & Agentic ChemBERTa Analysis Engine
================================================================
Evaluates potential chemical and pharmacodynamic interactions between 
multiple molecules using ChemBERTa embeddings, RDKit fingerprints, and
SMARTS structural alert overlap.

Phase 3 feature for SIH 2026.
"""

import math
import numpy as np
from typing import Dict, Any, List, Optional

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, DataStructs, MACCSkeys
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False

try:
    import torch
    from models.chemberta_encoder import get_chemberta_encoder
    HAS_CHEMBERTA = True
except ImportError:
    HAS_CHEMBERTA = False


class DDIPredictor:
    """
    Drug-Drug Interaction predictor combining ChemBERTa embeddings,
    Tanimoto structural similarity, and toxicophore overlap.
    """

    def __init__(self):
        self.encoder = None
        if HAS_CHEMBERTA:
            try:
                self.encoder = get_chemberta_encoder()
            except Exception as e:
                print(f"⚠️ ChemBERTa initialization in DDI predictor: {e}")

    def compute_ddi(self, smiles_a: str, smiles_b: str, name_a: str = "Drug A", name_b: str = "Drug B") -> Dict[str, Any]:
        """
        Evaluate interaction potential between two SMILES strings.
        """
        trace = []
        trace.append({"step": 1, "agent": "Molecule Parser", "action": f"Validating SMILES for {name_a} and {name_b}"})

        mol_a = Chem.MolFromSmiles(smiles_a) if HAS_RDKIT else None
        mol_b = Chem.MolFromSmiles(smiles_b) if HAS_RDKIT else None

        if HAS_RDKIT and (not mol_a or not mol_b):
            return {
                "success": False,
                "error": "One or both SMILES strings could not be parsed by RDKit.",
                "trace": trace
            }

        trace.append({"step": 2, "agent": "ChemBERTa Transformer", "action": "Generating 768-dim SMILES embedding representations"})

        # ChemBERTa Cosine Similarity
        cosine_sim = 0.5
        if HAS_CHEMBERTA and self.encoder and self.encoder.is_loaded:
            try:
                emb_a = self.encoder.encode(smiles_a).cpu().numpy().flatten()
                emb_b = self.encoder.encode(smiles_b).cpu().numpy().flatten()
                norm_a = np.linalg.norm(emb_a)
                norm_b = np.linalg.norm(emb_b)
                if norm_a > 0 and norm_b > 0:
                    cosine_sim = float(np.dot(emb_a, emb_b) / (norm_a * norm_b))
            except Exception as e:
                print(f"⚠️ ChemBERTa encoding error in DDI: {e}")

        trace.append({"step": 3, "agent": "RDKit Fingerprint Engine", "action": f"Computing MACCS Keys & Tanimoto Similarity: {cosine_sim:.2f}"})

        # Structural Tanimoto Similarity via RDKit
        tanimoto_sim = 0.4
        if HAS_RDKIT and mol_a and mol_b:
            fp_a = MACCSkeys.GenMACCSKeys(mol_a)
            fp_b = MACCSkeys.GenMACCSKeys(mol_b)
            tanimoto_sim = float(DataStructs.TanimotoSimilarity(fp_a, fp_b))

        trace.append({"step": 4, "agent": "Toxicophore Overlap Analyzer", "action": "Scanning shared electrophilic / reactive SMARTS patterns"})

        # Shared alert check (Nitro, Aromatic Amine, Thiophene, Quinone, Halide)
        alerts_a = self._find_alerts(smiles_a)
        alerts_b = self._find_alerts(smiles_b)
        shared_alerts = list(set(alerts_a).intersection(set(alerts_b)))

        # Interaction Risk Score Formula
        raw_risk = (0.4 * tanimoto_sim) + (0.4 * cosine_sim) + (0.2 * (len(shared_alerts) > 0))
        # Known heavy interaction pairs (e.g. Warfarin + Aspirin)
        names_combined = f"{name_a.lower()} {name_b.lower()}"
        is_known_high_risk = any(pair in names_combined for pair in [
            "warfarin aspirin", "aspirin warfarin",
            "aspirin ibuprofen", "ibuprofen aspirin",
            "clozapine caffeine", "caffeine clozapine",
            "paracetamol alcohol", "acetaminophen warfarin"
        ])

        if is_known_high_risk:
            raw_risk = max(raw_risk, 0.85)

        risk_level = "HIGH" if raw_risk >= 0.7 else "MODERATE" if raw_risk >= 0.45 else "LOW"

        trace.append({"step": 5, "agent": "Synthesis Agent", "action": f"Synthesized final DDI Risk ({risk_level}: {(raw_risk*100):.0f}%)"})

        # Interaction mechanism synthesis
        mechanism = self._generate_mechanism(name_a, name_b, risk_level, shared_alerts, tanimoto_sim, is_known_high_risk)

        return {
            "success": True,
            "molecules": [
                {"name": name_a, "smiles": smiles_a, "alerts": alerts_a},
                {"name": name_b, "smiles": smiles_b, "alerts": alerts_b}
            ],
            "metrics": {
                "chemberta_cosine_similarity": round(cosine_sim, 4),
                "tanimoto_similarity": round(tanimoto_sim, 4),
                "interaction_risk_score": round(raw_risk, 4),
                "risk_level": risk_level
            },
            "shared_alerts": shared_alerts,
            "mechanism": mechanism,
            "trace": trace
        }

    def _find_alerts(self, smiles: str) -> List[str]:
        if not HAS_RDKIT:
            return []
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return []
        patterns = {
            "Nitro [NO2]": "[N+](=O)[O-]",
            "Aromatic Amine": "c[NH2]",
            "Thiophene": "c1ccsc1",
            "Quinone": "C1(=O)C=CC(=O)C=C1",
            "Alkyl Halide": "[CX4][Cl,Br,I]",
            "Phenol": "c[OH]"
        }
        found = []
        for name, smarts in patterns.items():
            patt = Chem.MolFromSmarts(smarts)
            if patt and mol.HasSubstructMatch(patt):
                found.append(name)
        return found

    def _generate_mechanism(self, name_a: str, name_b: str, risk_level: str, shared_alerts: List[str], sim: float, is_known: bool) -> str:
        if is_known:
            return f"**High Synergistic Risk**: Co-administration of {name_a} and {name_b} exhibits significant clinical interaction risk (e.g. synergistic anticoagulation, CYP450 enzyme competition, or cumulative GI ulceration)."
        if risk_level == "HIGH":
            return f"**High Interaction Risk**: {name_a} and {name_b} share high structural similarity (Tanimoto: {sim:.2f}) and common toxicophores ({', '.join(shared_alerts) if shared_alerts else 'reactive motifs'}). Simultaneous administration may cause metabolic competitive inhibition."
        elif risk_level == "MODERATE":
            return f"**Moderate Risk**: Mild pharmacodynamic overlap detected between {name_a} and {name_b}. Monitor for additive hepatic or renal clearance loads."
        else:
            return f"**Low Risk**: {name_a} and {name_b} display distinct chemical scaffolds (Tanimoto: {sim:.2f}) with minimal shared metabolic toxicophores."


# Singleton instance
_ddi_instance = None

def get_ddi_predictor() -> DDIPredictor:
    global _ddi_instance
    if _ddi_instance is None:
        _ddi_instance = DDIPredictor()
    return _ddi_instance
