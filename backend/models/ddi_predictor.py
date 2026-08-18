#!/usr/bin/env python3
"""
Drug-Drug Interaction (DDI) & Agentic ChemBERTa Analysis Engine
================================================================
Evaluates potential chemical and pharmacodynamic interactions between 
multiple molecules using ChemBERTa embeddings, RDKit fingerprints, and
SMARTS structural alert overlap.

Phase 3 feature for SIH 2026.

Enhanced with NIH RxNav clinical DDI integration for real-world
drug-drug interaction warnings from FDA/EMA databases.
"""

import math
import traceback
import requests
import re
import logging
from typing import Dict, Any, List, Optional
from functools import lru_cache
import time

from flask import Blueprint, jsonify, request

import numpy as np

logger = logging.getLogger(__name__)

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
        
        # RxNav session with caching
        self._rxnav_session = requests.Session()
        self._rxnav_session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'AnuDrishti/1.0 (PharmaGuard AI)'
        })
        self._rxnav_cache = {}
        self._rxnav_last_request = 0
        self._rxnav_min_interval = 0.2  # 5 requests/sec max

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
        cosine_sim = 0.0
        chemberta_available = False
        if HAS_CHEMBERTA and self.encoder and self.encoder.is_loaded:
            try:
                emb_a = self.encoder.encode(smiles_a).cpu().numpy().flatten()
                emb_b = self.encoder.encode(smiles_b).cpu().numpy().flatten()
                norm_a = np.linalg.norm(emb_a)
                norm_b = np.linalg.norm(emb_b)
                if norm_a > 0 and norm_b > 0:
                    cosine_sim = float(np.dot(emb_a, emb_b) / (norm_a * norm_b))
                    chemberta_available = True
            except Exception as e:
                print(f"⚠️ ChemBERTa encoding error in DDI: {e}")

        # Structural Tanimoto Similarity via RDKit
        tanimoto_sim = 0.0
        rdkit_fp_available = False
        if HAS_RDKIT and mol_a and mol_b:
            try:
                fp_a = MACCSkeys.GenMACCSKeys(mol_a)
                fp_b = MACCSkeys.GenMACCSKeys(mol_b)
                tanimoto_sim = float(DataStructs.TanimotoSimilarity(fp_a, fp_b))
                rdkit_fp_available = True
            except Exception:
                tanimoto_sim = 0.0

        trace.append({"step": 3, "agent": "RDKit Fingerprint Engine", "action": "Tanimoto Similarity: %.2f (%s)" % (tanimoto_sim, "available" if rdkit_fp_available else "unavailable - neutral 0.0")})

        trace.append({"step": 4, "agent": "Toxicophore Overlap Analyzer", "action": "Scanning shared electrophilic / reactive SMARTS patterns"})

        # Shared alert check (Nitro, Aromatic Amine, Thiophene, Quinone, Halide)
        alerts_a = self._find_alerts(smiles_a)
        alerts_b = self._find_alerts(smiles_b)
        shared_alerts = list(set(alerts_a).intersection(set(alerts_b)))

        # T2-E: CYP450 substrate/inhibitor analysis
        cyp450_a = self._check_cyp450_interaction(smiles_a, name_a)
        cyp450_b = self._check_cyp450_interaction(smiles_b, name_b)
        cyp450_interaction = self._evaluate_cyp450_interaction(cyp450_a, cyp450_b, name_a, name_b)
        trace.append({"step": "4b", "agent": "CYP450 Metabolism Engine", "action": f"CYP450 {cyp450_interaction.get('enzyme', '—')} analysis: {cyp450_interaction.get('summary', 'no interaction')}"})

        # Interaction Risk Score Formula
        raw_risk = (0.4 * tanimoto_sim) + (0.4 * cosine_sim) + (0.2 * (len(shared_alerts) > 0))

        # Boost risk if there's a CYP450 pharmacokinetic interaction
        if cyp450_interaction['severity'] == 'HIGH':
            raw_risk = max(raw_risk, 0.85)
            is_known_high_risk = True
        elif cyp450_interaction['severity'] == 'MODERATE':
            raw_risk = max(raw_risk, 0.5)
        # Known heavy interaction pairs (e.g. Warfarin + Aspirin)
        names_combined = f"{name_a.lower()} {name_b.lower()}"
        is_known_high_risk = any(pair in names_combined for pair in [
            "warfarin aspirin", "aspirin warfarin",
            "aspirin ibuprofen", "ibuprofen aspirin",
            "clozapine caffeine", "caffeine clozapine",
            "paracetamol alcohol", "acetaminophen warfarin"
        ])

        if is_known_high_risk:
            raw_risk = max(raw_risk, 0.6)

        risk_level = "HIGH" if raw_risk >= 0.7 else "MODERATE" if raw_risk >= 0.45 else "LOW"

        trace.append({"step": 5, "agent": "Synthesis Agent", "action": f"Synthesized final DDI Risk ({risk_level}: {(raw_risk*100):.0f}%)"})

        # Interaction mechanism synthesis
        mechanism = self._generate_mechanism(name_a, name_b, risk_level, shared_alerts, tanimoto_sim, is_known_high_risk, cyp450_interaction)

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
            "cyp450_interaction": cyp450_interaction,
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
            "Aromatic Amine": "[c][NH2]",
            "Thiophene": "c1ccsc1",
            "Quinone": "O=C1C=CC(=O)C=C1",
            "Alkyl Halide": "[CX4][Cl,Br,I]",
            "Phenol": "[c][OH]"
        }
        found = []
        for name, smarts in patterns.items():
            patt = Chem.MolFromSmarts(smarts)
            # Guard: patt must not be None AND mol must have the method
            if patt is not None and hasattr(mol, 'HasSubstructMatch') and mol.HasSubstructMatch(patt):
                found.append(name)
        return found

    def _generate_mechanism(self, name_a: str, name_b: str, risk_level: str, shared_alerts: List[str], sim: float, is_known: bool, cyp450_info: Optional[Dict] = None) -> str:
        # Incorporate CYP450 mechanism if available
        cyp_text = ""
        if cyp450_info and cyp450_info.get('severity') != 'NONE':
            enzyme = cyp450_info.get('enzyme', 'CYP450')
            interaction_type = cyp450_info.get('interaction_type', '')
            cyp_text = f" Pharmacokinetically, {name_a} and {name_b} share {enzyme} metabolism ({interaction_type})."

        if is_known:
            return f"**Documented Interaction Risk**: {name_a} and {name_b} are a clinically-flagged drug pair with established interaction potential. Monitor closely and review dosing.{cyp_text}"
        if risk_level == "HIGH":
            return f"**High Interaction Risk**: {name_a} and {name_b} share high structural similarity (Tanimoto: {sim:.2f}) and common toxicophores ({', '.join(shared_alerts) if shared_alerts else 'reactive motifs'}). Simultaneous administration may cause metabolic competitive inhibition.{cyp_text}"
        elif risk_level == "MODERATE":
            return f"**Moderate Risk**: Mild pharmacodynamic overlap detected between {name_a} and {name_b}. Monitor for additive hepatic or renal clearance loads.{cyp_text}"
        else:
            return f"**Low Risk**: {name_a} and {name_b} display distinct chemical scaffolds (Tanimoto: {sim:.2f}) with minimal shared metabolic toxicophores."


    # T2-E: CYP450 substrate/inhibitor SMARTS patterns (valid RDKit SMARTS only)
    CYP_SMARTS = {
        'CYP3A4': {
            # Imidazole/pyridine nitrogens common in CYP3A4 substrates; tertiary amines
            'substrate': ['c1ccncc1', 'CN(C)C', 'C(=O)Oc1ccccc1'],
            # Ketoconazole-like imidazole inhibitors, macrolide ester motifs
            'inhibitor': ['c1cncs1', 'OC(=O)c1ccccc1', 'N1C=CN=C1'],
        },
        'CYP2D6': {
            # Basic amine + aromatic ring — hallmark CYP2D6 substrate
            'substrate': ['cCC(N)C', 'c1ccccc1CCN'],
            # Fluoxetine-like: trifluoromethyl + aryl amine
            'inhibitor': ['c1ccc(cc1)NC', 'FC(F)(F)c1ccccc1'],
        },
        'CYP2C9': {
            # NSAIDs / warfarin: aryl acetic acid, aryl propanoic acid
            'substrate': ['c1ccccc1CC(=O)O', 'c1ccc(cc1)OC'],
            # Sulfonamide / fluconazole-type inhibitors
            'inhibitor': ['NS(=O)(=O)c1ccccc1', 'c1cnc(nc1)C'],
        },
        'CYP1A2': {
            # Planar aromatic / xanthine (caffeine-like) CYP1A2 substrates
            'substrate': ['c1ccncc1', 'C1=CN=CN=C1', 'c1ccc2ccccc2c1'],
            # Quinolone-class inhibitors
            'inhibitor': ['c1ccc2nc(ccc2c1)=O', 'c1cc(ccc1)c1ccncc1'],
        },
    }

    def _check_cyp450_interaction(self, smiles: str, name: str = "Compound") -> Dict[str, Any]:
        """Check if a compound is a CYP450 substrate or inhibitor for major enzymes."""
        if not HAS_RDKIT:
            return {'name': name, 'smiles': smiles, 'roles': {}, 'enzymes': []}
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return {'name': name, 'smiles': smiles, 'roles': {}, 'enzymes': []}

        roles = {}
        enzymes_found = []
        for enzyme, patterns_dict in self.CYP_SMARTS.items():
            def _matches(smarts_list):
                for s in smarts_list:
                    patt = Chem.MolFromSmarts(s)
                    if patt is not None and hasattr(mol, 'HasSubstructMatch') and mol.HasSubstructMatch(patt):
                        return True
                return False
            is_substrate = _matches(patterns_dict.get('substrate', []))
            is_inhibitor = _matches(patterns_dict.get('inhibitor', []))
            if is_substrate:
                roles.setdefault(enzyme, []).append('substrate')
                if enzyme not in enzymes_found:
                    enzymes_found.append(enzyme)
            if is_inhibitor:
                roles.setdefault(enzyme, []).append('inhibitor')
                if enzyme not in enzymes_found:
                    enzymes_found.append(enzyme)
        return {
            'name': name,
            'smiles': smiles,
            'roles': roles,
            'enzymes': enzymes_found
        }

    def _evaluate_cyp450_interaction(self, cyp450_a: Dict, cyp450_b: Dict, name_a: str, name_b: str) -> Dict[str, Any]:
        """Evaluate pharmacokinetic DDI based on CYP450 enzyme overlap."""
        shared_enzymes = set(cyp450_a.get('enzymes', [])).intersection(set(cyp450_b.get('enzymes', [])))
        if not shared_enzymes:
            return {
                'severity': 'NONE',
                'enzyme': None,
                'interaction_type': None,
                'mechanism': 'No CYP450 enzyme overlap detected between compounds.',
                'summary': 'No pharmacokinetic DDI predicted',
                'shared_enzymes': []
            }

        enzyme = sorted(shared_enzymes)[0]
        roles_a = set(cyp450_a.get('roles', {}).get(enzyme, []))
        roles_b = set(cyp450_b.get('roles', {}).get(enzyme, []))

        # Substrate + Inhibitor = HIGH (competitive inhibition)
        # Substrate + Substrate = MODERATE (metabolic competition)
        # Inhibitor + Inhibitor = MODERATE (additive inhibition)
        if 'substrate' in roles_a and 'inhibitor' in roles_b:
            severity = 'HIGH'
            interaction_type = 'substrate-inhibitor competitive inhibition'
            mechanism = f"{name_b} is a {enzyme} inhibitor that may reduce metabolism of {name_a} (a {enzyme} substrate), leading to elevated plasma levels of {name_a}."
        elif 'inhibitor' in roles_a and 'substrate' in roles_b:
            severity = 'HIGH'
            interaction_type = 'substrate-inhibitor competitive inhibition'
            mechanism = f"{name_a} is a {enzyme} inhibitor that may reduce metabolism of {name_b} (a {enzyme} substrate), leading to elevated plasma levels of {name_b}."
        elif 'substrate' in roles_a and 'substrate' in roles_b:
            severity = 'MODERATE'
            interaction_type = 'substrate-substrate metabolic competition'
            mechanism = f"Both {name_a} and {name_b} are {enzyme} substrates; coadministration may cause competitive inhibition and reduced clearance of one or both."
        elif 'inhibitor' in roles_a and 'inhibitor' in roles_b:
            severity = 'MODERATE'
            interaction_type = 'inhibitor-inhibitor additive effect'
            mechanism = f"Both {name_a} and {name_b} inhibit {enzyme}; coadministration may lead to additive CYP450 suppression and altered metabolism of other drugs."
        else:
            severity = 'MODERATE'
            interaction_type = 'enzyme overlap'
            mechanism = f"Both compounds interact with {enzyme}; monitor for altered drug metabolism."

        return {
            'severity': severity,
            'enzyme': enzyme,
            'interaction_type': interaction_type,
            'mechanism': mechanism,
            'summary': f'{enzyme} {interaction_type}',
            'shared_enzymes': sorted(shared_enzymes)
        }

    # ============================================================
    # NIH RxNav Clinical DDI Integration
    # ============================================================
    
    # RxNav API configuration
    RXNAV_BASE_URL = "https://rxnav.nlm.nih.gov/REST"
    
    def _rxnav_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make request to RxNav API with rate limiting and caching."""
        cache_key = f"{endpoint}:{str(params)}"
        if cache_key in self._rxnav_cache:
            return self._rxnav_cache[cache_key]
        
        try:
            # Rate limiting
            elapsed = time.time() - getattr(self, '_rxnav_last_request', 0)
            if elapsed < 0.2:
                time.sleep(0.2 - elapsed)
            
            response = requests.get(
                f"{self.RXNAV_BASE_URL}/{endpoint}",
                params=params,
                timeout=10
            )
            self._rxnav_last_request = time.time()
            
            if response.status_code == 200:
                data = response.json()
                self._rxnav_cache[cache_key] = data
                return data
            else:
                logger.warning(f"RxNav API error: {response.status_code}")
                return None
        except Exception as e:
            logger.warning(f"RxNav API request failed: {e}")
            return None
    
    def _rxnav_get_rxcui(self, drug_name: str) -> Optional[str]:
        """Get RxCUI for a drug name via RxNav."""
        data = self._rxnav_request("rxcui.json", params={"name": drug_name, "search": 2})
        if data and 'idGroup' in data and 'rxnormId' in data['idGroup']:
            return data['idGroup']['rxnormId'][0]
        return None
    
    def _rxnav_get_interactions(self, rxcui: str) -> List[Dict]:
        """Get clinical DDI interactions for an RxCUI."""
        data = self._rxnav_request("interaction/interaction.json", params={"rxcui": rxcui})
        interactions = []
        if data and 'interactionTypeGroup' in data:
            for group in data['interactionTypeGroup']:
                for interaction_type in group.get('interactionType', []):
                    for interaction in interaction_type.get('interactionPair', []):
                        interactions.append({
                            'severity': interaction.get('severity', ''),
                            'description': interaction.get('description', ''),
                            'interacting_drug': interaction.get('interactionConcept', [{}])[1].get('minConceptItem', {}).get('name', '') if len(interaction.get('interactionConcept', [])) > 1 else ''
                        })
        return interactions
    
    def get_clinical_ddi(self, name_a: str, name_b: str) -> Dict[str, Any]:
        """
        Fetch clinical DDI from NIH RxNav for known drugs.
        
        Returns structured clinical interaction data if available,
        otherwise falls back to structural prediction.
        """
        # Try to get RxCUIs for both drugs
        rxcui_a = self._rxnav_get_rxcui(name_a)
        rxcui_b = self._rxnav_get_rxcui(name_b)
        
        if not rxcui_a or not rxcui_b:
            return {
                'source': 'RxNav',
                'available': False,
                'reason': 'One or both drugs not found in RxNav database',
                'rxcui_a': rxcui_a,
                'rxcui_b': rxcui_b
            }
        
        # Get interactions for both directions
        interactions_a = self._rxnav_get_interactions(rxcui_a)
        interactions_b = self._rxnav_get_interactions(rxcui_b)
        
        # Check if drug B is in A's interactions
        found_interactions = []
        for interaction in interactions_a:
            if interaction['interacting_drug'].lower() == name_b.lower() or interaction['interacting_drug'].lower() == name_b.replace(' ', '').lower():
                found_interactions.append(interaction)
        
        for interaction in interactions_b:
            if interaction['interacting_drug'].lower() == name_a.lower() or interaction['interacting_drug'].lower() == name_a.replace(' ', '').lower():
                found_interactions.append(interaction)
        
        if not found_interactions:
            return {
                'source': 'RxNav',
                'available': True,
                'interactions_found': False,
                'rxcui_a': rxcui_a,
                'rxcui_b': rxcui_b,
                'message': f'No clinical interaction documented between {name_a} and {name_b} in RxNav'
            }
        
        # Deduplicate and summarize
        unique_interactions = {}
        for inter in found_interactions:
            key = inter['description'][:100]
            if key not in unique_interactions or len(inter['description']) > len(unique_interactions[key]['description']):
                unique_interactions[key] = inter
        
        return {
            'source': 'RxNav',
            'available': True,
            'interactions_found': True,
            'rxcui_a': rxcui_a,
            'rxcui_b': rxcui_b,
            'interactions': list(unique_interactions.values()),
            'severity': max([i.get('severity', 'Unknown') for i in unique_interactions.values()], default='Unknown'),
            'summary': f"Clinical DDI found in NIH RxNav: {len(unique_interactions)} interaction(s) documented"
        }


# Singleton instance
_ddi_instance = None

def get_ddi_predictor() -> DDIPredictor:
    global _ddi_instance
    if _ddi_instance is None:
        _ddi_instance = DDIPredictor()
    return _ddi_instance


# REST endpoint for DDI
def register_ddi_routes(bp):
    """Register DDI routes on the given blueprint."""
    @bp.route('/ddi/predict', methods=['POST'])
    def ddi_predict():
        """Predict Drug-Drug Interaction between two molecules."""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Request body required'}), 400
            
            smiles_a = data.get('smiles_a') or data.get('smiles1')
            smiles_b = data.get('smiles_b') or data.get('smiles2')
            name_a = data.get('name_a', 'Drug A')
            name_b = data.get('name_b', 'Drug B')
            
            if not smiles_a or not smiles_b:
                return jsonify({'error': 'Both smiles_a and smiles_b required'}), 400
            
            ddi = get_ddi_predictor()
            result = ddi.compute_ddi(smiles_a, smiles_b, name_a, name_b)
            
            return jsonify(result)
        except Exception as e:
            print(f"❌ DDI prediction error: {e}")
            traceback.print_exc()
            return jsonify({'error': f'DDI prediction failed: {str(e)}'}), 500

    @bp.route('/ddi/check', methods=['POST'])
    def ddi_check():
        """Quick DDI check - alias for predict."""
        return ddi_predict()
