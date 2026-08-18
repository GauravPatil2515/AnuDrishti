#!/usr/bin/env python3
"""
Target Profiling / Mechanism of Action (MoA) Service
====================================================
Queries ChEMBL API to determine protein targets for a given molecule.
Provides Mechanism of Action predictions with confidence scores.

Free public API: https://www.ebi.ac.uk/chembl/api/data
Documentation: https://chembl.gitbook.io/chembl-interface-documentation
"""

import requests
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from functools import lru_cache
import time
import re

logger = logging.getLogger(__name__)

# ChEMBL REST API base URL
CHEMBL_BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

# Request timeout (seconds)
REQUEST_TIMEOUT = 10

# Minimum pChEMBL value for meaningful binding
MIN_PCHEMBL = 6.0

# Target confidence thresholds
HIGH_CONFIDENCE_PCHEMBL = 7.0
MEDIUM_CONFIDENCE_PCHEMBL = 6.0

# Known important targets for toxicity
TOXICITY_RELEVANT_TARGETS = {
    'hERG': ['KCNH2', 'HERG', 'KV11.1'],
    'Dopamine Receptor': ['DRD1', 'DRD2', 'DRD3', 'DRD4', 'DRD5'],
    'Serotonin Receptor': ['HTR1A', 'HTR2A', 'HTR2B', 'HTR2C'],
    'Adrenergic Receptor': ['ADRA1A', 'ADRA1B', 'ADRA2A', 'ADRB1', 'ADRB2'],
    'Muscarinic Receptor': ['CHRM1', 'CHRM2', 'CHRM3', 'CHRM4', 'CHRM5'],
    'Opioid Receptor': ['OPRM1', 'OPRD1', 'OPRK1'],
    'GABA Receptor': ['GABRA1', 'GABRB2', 'GABRG2'],
    'NMDA Receptor': ['GRIN1', 'GRIN2A', 'GRIN2B'],
    'P-gp': ['ABCB1', 'MDR1'],
    'CYP450': ['CYP1A2', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP3A4'],
}


@dataclass
class Target:
    """Represents a protein target with binding data."""
    chembl_id: str
    target_name: str
    target_type: str  # SINGLE PROTEIN, PROTEIN COMPLEX, etc.
    organism: str
    pchembl_value: Optional[float] = None
    standard_type: Optional[str] = None  # IC50, Ki, Kd, EC50, etc.
    standard_units: Optional[str] = None
    standard_value: Optional[float] = None
    confidence: str = "Low"  # High, Medium, Low
    toxicity_relevance: Optional[str] = None
    target_class: Optional[str] = None
    uniprot_id: Optional[str] = None


@dataclass
class TargetProfile:
    """Complete target profile for a molecule."""
    molecule_id: str
    molecule_name: Optional[str] = None
    targets: List[Target] = field(default_factory=list)
    moa_summary: str = ""
    toxicity_mechanisms: List[str] = field(default_factory=list)
    source: str = "ChEMBL"


class TargetPredictor:
    """
    ChEMBL API wrapper for target prediction and MoA profiling.
    
    Features:
    - Exact structure lookup by SMILES (ChEMBL structure search)
    - Substructure/similarity search for novel compounds
    - Target classification with toxicity relevance
    - Confidence scoring based on pChEMBL values
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'AnuDrishti/1.0 (PharmaGuard AI)'
        })
        self._cache = {}
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request to ChEMBL API with error handling."""
        url = f"{CHEMBL_BASE_URL}/{endpoint}"
        try:
            response = self.session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"ChEMBL API error: {response.status_code} - {response.text}")
                return None
        except requests.Timeout:
            logger.warning(f"ChEMBL API timeout for {endpoint}")
            return None
        except Exception as e:
            logger.error(f"ChEMBL API request failed: {e}")
            return None
    
    def _get_chembl_id_by_smiles(self, smiles: str) -> Optional[str]:
        """Find ChEMBL ID for exact SMILES match."""
        # Use ChEMBL structure exact match endpoint
        data = self._make_request("molecule", params={
            'structure__exact_match': smiles,
            'format': 'json'
        })
        if data and data.get('molecules'):
            return data['molecules'][0].get('molecule_chembl_id')
        return None
    
    def _get_chembl_id_by_name(self, name: str) -> Optional[str]:
        """Find ChEMBL ID by drug name (synonym search)."""
        data = self._make_request("molecule", params={
            'molecule_synonyms__molecule_synonym__iexact': name,
            'format': 'json'
        })
        if data and data.get('molecules'):
            return data['molecules'][0].get('molecule_chembl_id')
        return None
    
    def _get_targets_for_molecule(self, chembl_id: str) -> List[Target]:
        """Fetch all targets with activity data for a ChEMBL molecule."""
        data = self._make_request(f"activity", params={
            'molecule_chembl_id': chembl_id,
            'pchembl_value__gte': MIN_PCHEMBL,
            'standard_type__in': 'IC50,Ki,Kd,EC50,AC50,Potency',
            'target_type__in': 'SINGLE PROTEIN,PROTEIN COMPLEX',
            'format': 'json',
            'limit': 100
        })
        
        targets = []
        if not data or not data.get('activities'):
            return targets
        
        seen_targets = {}
        for act in data['activities']:
            target_chembl_id = act.get('target_chembl_id')
            if not target_chembl_id:
                continue
            
            # Skip duplicates, keep highest pChEMBL
            pchembl = act.get('pchembl_value')
            if pchembl is None:
                continue
            
            if target_chembl_id in seen_targets:
                if pchembl > seen_targets[target_chembl_id].pchembl_value:
                    seen_targets[target_chembl_id] = self._parse_activity(act, pchembl)
            else:
                seen_targets[target_chembl_id] = self._parse_activity(act, pchembl)
        
        return list(seen_targets.values())
    
    def _parse_activity(self, activity: Dict, pchembl: float) -> Target:
        """Parse activity record into Target object."""
        target = Target(
            chembl_id=activity.get('target_chembl_id', ''),
            target_name=activity.get('target_pref_name', ''),
            target_type=activity.get('target_type', ''),
            organism=activity.get('organism', ''),
            pchembl_value=pchembl,
            standard_type=activity.get('standard_type'),
            standard_units=activity.get('standard_units'),
            standard_value=activity.get('standard_value'),
            target_class=activity.get('target_class'),
        )
        
        # Determine confidence
        if pchembl >= HIGH_CONFIDENCE_PCHEMBL:
            target.confidence = "High"
        elif pchembl >= MEDIUM_CONFIDENCE_PCHEMBL:
            target.confidence = "Medium"
        else:
            target.confidence = "Low"
        
        # Check toxicity relevance
        target.toxicity_relevance = self._check_toxicity_relevance(target)
        
        return target
    
    def _check_toxicity_relevance(self, target: Target) -> Optional[str]:
        """Check if target is relevant to known toxicity mechanisms."""
        name = target.target_name.upper()
        for toxicity_target, keywords in TOXICITY_RELEVANT_TARGETS.items():
            for kw in keywords:
                if kw in name:
                    return toxicity_target
        return None
    
    def _fetch_target_details(self, target: Target) -> Target:
        """Fetch additional details for a target (UniProt ID, etc.)."""
        if not target.chembl_id:
            return target
        
        data = self._make_request(f"target/{target.chembl_id}", params={'format': 'json'})
        if data:
            target.uniprot_id = data.get('target_components', [{}])[0].get('accession')
        return target
    
    def predict_targets(self, smiles: Optional[str] = None, name: Optional[str] = None) -> TargetProfile:
        """
        Main entry point: predict targets for a molecule.
        
        Args:
            smiles: SMILES string (preferred for exact match)
            name: Drug name (synonym search fallback)
        
        Returns:
            TargetProfile with targets, MoA summary, toxicity mechanisms
        """
        profile = TargetProfile(molecule_id=smiles or name or "unknown")
        
        chembl_id = None
        if smiles:
            chembl_id = self._get_chembl_id_by_smiles(smiles)
        if not chembl_id and name:
            chembl_id = self._get_chembl_id_by_name(name)
            profile.molecule_name = name
        
        if not chembl_id:
            profile.moa_summary = "No ChEMBL record found for this molecule. Targets unknown."
            profile.source = "ChEMBL (no match)"
            return profile
        
        # Fetch targets
        targets = self._get_targets_for_molecule(chembl_id)
        
        # Enrich with details
        for target in targets:
            self._fetch_target_details(target)
        
        # Sort by pChEMBL (highest first)
        targets.sort(key=lambda t: t.pchembl_value or 0, reverse=True)
        
        profile.targets = targets
        profile.source = f"ChEMBL ({chembl_id})"
        
        # Generate MoA summary
        profile.moa_summary = self._generate_moa_summary(targets)
        profile.toxicity_mechanisms = self._identify_toxicity_mechanisms(targets)
        
        return profile
    
    def _generate_moa_summary(self, targets: List[Target]) -> str:
        """Generate human-readable Mechanism of Action summary."""
        if not targets:
            return "No known molecular targets identified."
        
        high_conf = [t for t in targets if t.confidence == "High"]
        med_conf = [t for t in targets if t.confidence == "Medium"]
        
        parts = []
        if high_conf:
            primary = high_conf[0]
            parts.append(f"Primary target: **{primary.target_name}** ({primary.target_type}) with high affinity (pChEMBL {primary.pchembl_value:.2f}).")
            if len(high_conf) > 1:
                others = ", ".join([t.target_name for t in high_conf[1:3]])
                parts.append(f"Additional high-confidence targets: {others}.")
        
        if med_conf:
            others = ", ".join([t.target_name for t in med_conf[:3]])
            parts.append(f"Moderate-affinity targets: {others}.")
        
        return " ".join(parts) if parts else "Targets identified but with low confidence."
    
    def _identify_toxicity_mechanisms(self, targets: List[Target]) -> List[str]:
        """Identify potential toxicity mechanisms based on targets."""
        mechanisms = []
        seen = set()
        
        for target in targets:
            if target.toxicity_relevance and target.toxicity_relevance not in seen:
                seen.add(target.toxicity_relevance)
                mechanisms.append(
                    f"**{target.toxicity_relevance}** ({target.target_name}): "
                    f"Binding (pChEMBL {target.pchembl_value:.2f}) may mediate toxicity."
                )
        
        return mechanisms
    
    def similarity_search(self, smiles: str, threshold: float = 0.7, limit: int = 10) -> List[Dict]:
        """
        Find similar molecules in ChEMBL for novel compound target prediction.
        Uses ChEMBL similarity search endpoint.
        """
        data = self._make_request("similarity", params={
            'smiles': smiles,
            'threshold': threshold,
            'limit': limit,
            'format': 'json'
        })
        
        results = []
        if data and data.get('molecules'):
            for mol in data['molecules']:
                results.append({
                    'chembl_id': mol.get('molecule_chembl_id'),
                    'similarity': mol.get('similarity'),
                    'pref_name': mol.get('pref_name'),
                    'smiles': mol.get('molecule_structures', {}).get('canonical_smiles')
                })
        return results
    
    def predict_targets_for_novel(self, smiles: str, threshold: float = 0.7) -> TargetProfile:
        """
        Predict targets for novel compound using similarity search.
        Transfers targets from similar known compounds.
        """
        profile = TargetProfile(molecule_id=smiles)
        similar = self.similarity_search(smiles, threshold=threshold, limit=5)
        
        if not similar:
            profile.moa_summary = "No similar compounds found in ChEMBL for target transfer."
            profile.source = "ChEMBL (similarity search - no hits)"
            return profile
        
        # Aggregate targets from similar compounds
        all_targets = {}
        for sim_mol in similar:
            sim_targets = self._get_targets_for_molecule(sim_mol['chembl_id'])
            for t in sim_targets:
                key = t.chembl_id
                if key in all_targets:
                    # Keep higher confidence
                    if (t.pchembl_value or 0) > (all_targets[key].pchembl_value or 0):
                        all_targets[key] = t
                else:
                    all_targets[key] = t
        
        targets = list(all_targets.values())
        for t in targets:
            self._fetch_target_details(t)
        
        targets.sort(key=lambda x: x.pchembl_value or 0, reverse=True)
        profile.targets = targets
        profile.source = f"ChEMBL (similarity transfer from {len(similar)} compounds)"
        profile.moa_summary = self._generate_moa_summary(targets)
        profile.toxicity_mechanisms = self._identify_toxicity_mechanisms(targets)
        
        return profile


# Singleton instance
_target_predictor = None

def get_target_predictor() -> TargetPredictor:
    """Get or create singleton TargetPredictor instance."""
    global _target_predictor
    if _target_predictor is None:
        _target_predictor = TargetPredictor()
    return _target_predictor


if __name__ == "__main__":
    # Quick test
    predictor = get_target_predictor()
    
    # Test with aspirin
    print("Testing with Aspirin...")
    profile = predictor.predict_targets(name="aspirin")
    print(f"Source: {profile.source}")
    print(f"MoA: {profile.moa_summary}")
    print(f"Toxicity Mechanisms: {profile.toxicity_mechanisms}")
    print(f"Targets found: {len(profile.targets)}")
    for t in profile.targets[:5]:
        print(f"  - {t.target_name} (pChEMBL: {t.pchembl_value}, confidence: {t.confidence}, relevance: {t.toxicity_relevance})")