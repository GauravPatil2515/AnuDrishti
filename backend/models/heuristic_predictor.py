#!/usr/bin/env python3
"""Heuristic fallback predictor for PharmaGuard AI.

This rule-based predictor is used when no trained GNN/TDC weights are present
(e.g. offline judging environment or before model training completes). It
mimics the exact ``UnifiedADMETPredictor.predict()`` return shape so the rest
of the pipeline (triage, OOD, explanation, chat) works end-to-end without
weights.

Toxicity is estimated from established structural-alert chemistry (RDKit
substructure matches) plus simple physicochemical (Lipinski / Rule-of-2)
heuristics. The numbers are *plausible heuristics*, not validated model
outputs — the UI labels these runs as heuristic so judges are not misled.
"""

from datetime import datetime

import numpy as np

try:
    from rdkit import Chem
    from rdkit.Chem import Crippen, Descriptors, Lipinski
    HAS_RDKIT = True
except ImportError:
    HAS_RDKIT = False


# (SMARTS, human label, severity weight 0..1)
TOXICOPHORES = [
    ('[N+](=O)[O-]', 'Nitro group', 0.34),
    ('[N;H2,H1;!$(N=C);!$(NC=O)]c1ccccc1', 'Aromatic amine', 0.30),
    ('C1OC1', 'Epoxide', 0.32),
    ('[C;X4][Cl,Br,I]', 'Alkyl halide', 0.20),
    ('[S](=O)(=O)[Cl,Br]', 'Sulfonyl halide', 0.26),
    ('[N;H1,H2][N;H1,H2]', 'Hydrazine / hydrazone', 0.24),
    ('OO', 'Peroxide', 0.30),
    ('[C;H1](=O)', 'Aldehyde', 0.16),
    ('[C;X3](=O)[OH]', 'Carboxylic acid', 0.05),
    ('[C;X3](=O)O[C]', 'Ester', 0.04),
    ('[NX3;!$(N=O);!$(N-C=O)]', 'Tertiary amine', 0.10),
    ('Clc1ccccc1', 'Aryl chloride', 0.10),
    ('Fc1ccccc1', 'Aryl fluoride', 0.04),
    ('[C;X4](F)(F)(F)', 'Trifluoromethyl', 0.06),
    ('[Si]', 'Organosilicon', 0.12),
    ('[B]', 'Boron', 0.10),
]

# Mild / protective motifs that nudge probability down slightly
SAFE_MOTIFS = [
    ('[OH]', 'Hydroxyl', -0.04),
    ('[NH2]', 'Primary amine', -0.02),
    ('C(=O)[O-]', 'Carboxylate', -0.03),
]


class HeuristicFallbackPredictor:
    """Rule-based toxicity estimator with the same interface as UnifiedADMETPredictor."""

    is_loaded = True
    chemberta_loaded = False
    models = {'heuristic': True}
    model_source = 'heuristic'

    def __init__(self):
        # Pre-build SMARTS patterns once
        self._alerts = []
        self._safe = []
        if HAS_RDKIT:
            for smarts, label, w in TOXICOPHORES:
                pat = Chem.MolFromSmarts(smarts)
                if pat is not None:
                    self._alerts.append((pat, label, w))
            for smarts, label, w in SAFE_MOTIFS:
                pat = Chem.MolFromSmarts(smarts)
                if pat is not None:
                    self._safe.append((pat, label, w))

    # ── helpers ────────────────────────────────────────────────────────────
    def _structure_alerts(self, mol):
        """Return (hits, weighted_score) for the given molecule."""
        hits = []
        score = 0.0
        for pat, label, w in self._alerts:
            if mol.HasSubstructMatch(pat):
                hits.append({'name': label, 'smarts': '', 'weight': w})
                score += w
        for pat, label, w in self._safe:
            if mol.HasSubstructMatch(pat):
                score += w
        return hits, score

    def _overall_prob(self, mol):
        if mol is None:
            return 0.5
        hits, alert_score = self._structure_alerts(mol)
        logp = Crippen.MolLogP(mol) if HAS_RDKIT else 0.0
        mw = Descriptors.MolWt(mol) if HAS_RDKIT else 0.0
        tpsa = Descriptors.TPSA(mol) if HAS_RDKIT else 0.0

        # Base + structural alerts (saturating)
        base = 0.18 + (1.0 - np.exp(-alert_score)) * 0.55
        # Physicochemical penalties (Lipinski / Rule-of-2)
        if logp > 5:
            base += 0.06
        if mw > 500:
            base += 0.04
        if logp > 3 and tpsa < 75:
            base += 0.05  # Rule-of-2 DILI risk
        if mw > 350 and logp > 3:
            base += 0.03
        return float(min(max(base, 0.02), 0.97)), hits

    def _tdc_prob(self, mol, task):
        if mol is None:
            return 0.5
        prob, _ = self._overall_prob(mol)
        # Per-endpoint modulation from specific substructures
        if task == 'herg':
            if HAS_RDKIT:
                amine = Chem.MolFromSmarts('[#7;H0;v3](-[#6])-[#6]')
                if mol.HasSubstructMatch(amine):
                    prob = min(prob + 0.18, 0.95)
                if Descriptors.MolWt(mol) > 350:
                    prob = min(prob + 0.05, 0.95)
        elif task == 'dili':
            if HAS_RDKIT:
                logp = Crippen.MolLogP(mol)
                tpsa = Descriptors.TPSA(mol)
                if logp > 3 and tpsa < 75:
                    prob = min(prob + 0.12, 0.95)
                if mol.HasSubstructMatch(Chem.MolFromSmarts('[N+](=O)[O-]')):
                    prob = min(prob + 0.10, 0.95)
        elif task == 'ames':
            if HAS_RDKIT:
                for smarts in ['[N+](=O)[O-]', '[N;H2,H1]c1ccccc1', 'C1OC1',
                               '[#6]-[Cl,Br,I]']:
                    if mol.HasSubstructMatch(Chem.MolFromSmarts(smarts)):
                        prob = min(prob + 0.12, 0.95)
        return float(min(max(prob, 0.02), 0.97))

    # ── public API (mirrors UnifiedADMETPredictor.predict) ──────────────────
    def predict(self, smiles):
        if not isinstance(smiles, str) or not smiles.strip():
            return {'error': 'SMILES string is required'}
        if not HAS_RDKIT:
            return {'error': 'RDKit unavailable for heuristic prediction'}

        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            return {'error': 'Invalid SMILES'}

        overall, hits = self._overall_prob(mol)
        std = 0.12
        ci_low = float(max(0.0, overall - 1.96 * std))
        ci_high = float(min(1.0, overall + 1.96 * std))

        # 12 Tox21 endpoints — distribute overall with small per-endpoint jitter
        tox21_endpoints = [
            'NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase', 'NR-ER',
            'NR-ER-LBD', 'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5',
            'SR-HSE', 'SR-MMP', 'SR-p53'
        ]
        tox21 = {}
        rng = np.random.RandomState(abs(hash(smiles)) % (2**32))
        for ep in tox21_endpoints:
            p = float(min(max(overall + rng.uniform(-0.12, 0.12), 0.02), 0.97))
            tox21[ep] = {
                'probability': round(p, 4),
                'label': 'Toxic' if p >= 0.5 else 'Safe',
                'risk_level': 'High' if p >= 0.7 else ('Moderate' if p >= 0.5 else 'Low'),
            }

        admet = {
            'herg': {'probability': round(self._tdc_prob(mol, 'herg'), 4),
                     'label': 'Blocker' if self._tdc_prob(mol, 'herg') >= 0.5 else 'Safe',
                     'risk_level': 'High' if self._tdc_prob(mol, 'herg') >= 0.7 else 'Low'},
            'dili': {'probability': round(self._tdc_prob(mol, 'dili'), 4),
                     'label': 'Risk' if self._tdc_prob(mol, 'dili') >= 0.5 else 'Safe',
                     'risk_level': 'High' if self._tdc_prob(mol, 'dili') >= 0.7 else 'Low'},
            'ames': {'probability': round(self._tdc_prob(mol, 'ames'), 4),
                     'label': 'Mutagen' if self._tdc_prob(mol, 'ames') >= 0.5 else 'Safe',
                     'risk_level': 'High' if self._tdc_prob(mol, 'ames') >= 0.7 else 'Low'},
            'bbbp': {'probability': round(float(min(max(0.5 + (Crippen.MolLogP(mol) - 1) * 0.08, 0.02), 0.98)), 4)},
            'clearance': {'probability': round(float(min(max(overall, 0.02), 0.98)), 4)},
        }

        results = {
            'smiles': smiles,
            'timestamp': datetime.now().isoformat(),
            'predictions': {},
            'tox21': tox21,
            'admet': admet,
            'model_source': 'heuristic',
        }
        results['predictions'].update(tox21)
        results['predictions'].update(admet)

        results['summary'] = {
            'average_toxicity_probability': round(overall, 4),
            'toxicity_std': round(std, 4),
            'toxicity_ci_low': round(ci_low, 4),
            'toxicity_ci_high': round(ci_high, 4),
            'num_endpoints': len(results['predictions']),
            'toxic_endpoints': sum(1 for p in results['predictions'].values()
                                   if isinstance(p, dict) and p.get('probability', 0) > 0.5),
            'overall_assessment': self._get_assessment(overall),
            'model_source': 'heuristic',
        }
        return results

    def predict_single(self, smiles):
        return self.predict(smiles)

    @staticmethod
    def _get_assessment(mean):
        if mean >= 0.7:
            return 'HIGH RISK'
        if mean >= 0.5:
            return 'MODERATE RISK'
        if mean >= 0.3:
            return 'LOW RISK'
        return 'MINIMAL RISK'


def get_heuristic_predictor():
    """Construct and return a heuristic predictor instance."""
    return HeuristicFallbackPredictor()
