#!/usr/bin/env python3
"""
OODDetector — Out-of-Distribution Detection for PharmaGuard AI
===============================================================

Flags molecules that fall outside the model's learned training distribution
so the platform can explicitly lower confidence and recommend expert review
instead of presenting an over-confident prediction.

Two complementary signals are combined:

1. **Fingerprint Tanimoto distance** — Minimum Tanimoto distance from the query
   molecule to every training-set molecule (ECFP4 / Morgan radius 2). A query
   far from all known structures is likely structurally novel.

2. **Latent Mahalanobis distance** — Distance of the GNN graph-level embedding
   to the training-set embedding centroid in latent space. Captures
   distributional shift beyond nearest-neighbour similarity.

The final ``ood_score`` (0 = in-distribution, 1 = far out-of-distribution) is a
harmonic blend of the two normalized signals, and ``is_ood`` is a configurable
threshold on that score.

Author: PharmaGuard AI Team
"""

import logging
import numpy as np
from typing import Dict, Any, List, Optional

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    print("⚠️ RDKit not available - OOD detection disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('OODDetector')


class OODDetector:
    """Detect whether a molecule is out-of-distribution for the predictor."""

    def __init__(
        self,
        predictor,
        fingerprints: Optional[np.ndarray] = None,
        latent_centroid: Optional[np.ndarray] = None,
        latent_precision: Optional[np.ndarray] = None,
        ood_threshold: float = 0.6,
        tanimoto_weight: float = 0.5,
        latent_weight: float = 0.5,
        fp_radius: int = 2,
        fp_bits: int = 2048,
        max_train_samples: int = 2000
    ):
        """
        Args:
            predictor: UnifiedADMETPredictor (used to obtain GNN embeddings).
            fingerprints: Pre-computed training-set Morgan fingerprint matrix
                (n_train x fp_bits). If None, an internal reference set is built
                lazily from a small set of common drug-like molecules.
            latent_centroid: Mean of training-set GNN latent embeddings.
            latent_precision: Inverse covariance of training-set embeddings
                (Mahalanobis). If None, Euclidean distance is used.
            ood_threshold: Score above which a molecule is flagged as OOD.
            tanimoto_weight / latent_weight: Blend weights (auto-normalized).
            fp_radius, fp_bits: Morgan fingerprint parameters.
            max_train_samples: Cap on reference set size for speed.
        """
        if not RDKIT_AVAILABLE:
            raise ImportError("RDKit is required for OOD detection")

        self.predictor = predictor
        self.ood_threshold = ood_threshold
        self.tanimoto_weight = tanimoto_weight
        self.latent_weight = latent_weight
        self.fp_radius = fp_radius
        self.fp_bits = fp_bits
        self.max_train_samples = max_train_samples

        self.fingerprints = fingerprints
        self.latent_centroid = latent_centroid
        self.latent_precision = latent_precision
        self._train_smiles: List[str] = []

        if fingerprints is None:
            self._build_reference_set()

    # ─────────────────────────────────────────────────────────────────────
    # Reference-set construction
    # ─────────────────────────────────────────────────────────────────────
    def _build_reference_set(self):
        """Build a small but representative drug-like reference set.

        Used only when no explicit training fingerprints are supplied. The
        reference molecules cover common scaffolds so Tanimoto distances are
        meaningful for typical queries.
        """
        ref_smiles = [
            "CC(=O)OC1=CC=CC=C1C(=O)O",          # Aspirin
            "CC(=O)NC1=CC=C(C=C1)O",             # Acetaminophen
            "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",     # Ibuprofen
            "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",      # Caffeine
            "CCO",                                # Ethanol
            "C1=CC=CC=C1",                        # Benzene
            "CC1=CC=CC=C1",                       # Toluene
            "O=C(O)c1ccccc1",                     # Benzoic acid
            "c1ccc2[nH]ccc2c1",                   # Indole
            "C1CCCCC1",                           # Cyclohexane
            "CC(=O)Nc1ccc(O)cc1",                 # Paracetamol alt
            "c1ccc(cc1)c2ccccc2",                 # Biphenyl
            "O=C1NC(=O)C(N2C(=O)c3ccccc3C2=O)CC1", # Thalidomide
            "CN1CCCC1C2=CN=CC=C2",               # Nicotine
            "CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C" # Testosterone
        ]
        fps = []
        valid = []
        for smi in ref_smiles:
            fp = self._morgan_fp(smi)
            if fp is not None:
                fps.append(fp)
                valid.append(smi)
        if fps:
            self.fingerprints = np.vstack(fps)
            self._train_smiles = valid
            logger.info(f"✅ OOD reference set built with {len(valid)} molecules")
        else:
            self.fingerprints = np.zeros((1, self.fp_bits), dtype=np.int8)
            logger.warning("⚠️ OOD reference set empty (no valid SMILES)")

    # ─────────────────────────────────────────────────────────────────────
    # Fingerprint helpers
    # ─────────────────────────────────────────────────────────────────────
    def _morgan_fp(self, smiles: str) -> Optional[np.ndarray]:
        """Return a binary Morgan fingerprint (radius 2) for a SMILES string."""
        try:
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            fp = AllChem.GetMorganFingerprintAsBitVect(
                mol, self.fp_radius, nBits=self.fp_bits
            )
            arr = np.zeros((self.fp_bits,), dtype=np.int8)
            from rdkit.DataStructs import ConvertToNumpyArray
            ConvertToNumpyArray(fp, arr)
            return arr
        except Exception as e:
            logger.debug(f"FP failed for {smiles}: {e}")
            return None

    @staticmethod
    def _tanimoto(a: np.ndarray, b: np.ndarray) -> float:
        """Tanimoto similarity between two binary fingerprints."""
        ab = np.logical_and(a, b).sum()
        a_ = a.sum()
        b_ = b.sum()
        denom = a_ + b_ - ab
        if denom == 0:
            return 0.0
        return float(ab) / float(denom)

    def _min_tanimoto_distance(self, fp: np.ndarray) -> float:
        """1 - max(Tanimoto similarity) to the reference set."""
        if self.fingerprints is None or len(self.fingerprints) == 0:
            return 1.0
        best = 0.0
        for ref in self.fingerprints:
            sim = self._tanimoto(fp, ref)
            if sim > best:
                best = sim
        return 1.0 - best

    # ─────────────────────────────────────────────────────────────────────
    # Latent embedding
    # ─────────────────────────────────────────────────────────────────────
    def _latent_embedding(self, smiles: str) -> Optional[np.ndarray]:
        """Extract the GNN graph-level embedding for a molecule.

        Falls back to a Morgan-based feature vector when the predictor cannot
        produce a latent embedding, so OOD scoring degrades gracefully.
        """
        try:
            model = getattr(self.predictor, 'models', {}).get('attention_gin', {}).get('model')
            if model is not None:
                # Use the correct featurization method that matches training
                data = getattr(self.predictor, '_smiles_to_graph_simple', lambda s: None)(smiles)
                if data is not None:
                    from torch_geometric.data import Batch
                    import torch
                    batch = Batch.from_data_list([data]).to(self.predictor.device)
                    with torch.no_grad():
                        feat, _ = model(batch, return_attention=False)
                    return feat.cpu().numpy()[0]
        except Exception as e:
            logger.debug(f"Latent extraction failed: {e}")

        # Fallback: use the raw fingerprint as a feature proxy
        fp = self._morgan_fp(smiles)
        return fp.astype(np.float32) if fp is not None else None

    def _mahalanobis(self, x: np.ndarray) -> float:
        """Mahalanobis distance to the training centroid (Euclidean fallback)."""
        if self.latent_centroid is None:
            return float(np.linalg.norm(x))
        diff = x - self.latent_centroid
        if self.latent_precision is not None:
            try:
                return float(np.sqrt(diff @ self.latent_precision @ diff))
            except Exception:
                pass
        return float(np.linalg.norm(diff))

    # ─────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────
    def evaluate(self, smiles: str) -> Dict[str, Any]:
        """Evaluate OOD status for a single SMILES string."""
        fp = self._morgan_fp(smiles)
        if fp is None:
            return {
                'ood_score': 1.0,
                'is_ood': True,
                'confidence_modifier': 0.0,
                'nearest_neighbor_similarity': 0.0,
                'latent_distance': None,
                'note': 'Invalid or unparseable SMILES treated as out-of-distribution'
            }

        tanimoto_dist = self._min_tanimoto_distance(fp)
        nearest_sim = 1.0 - tanimoto_dist

        latent = self._latent_embedding(smiles)
        latent_dist = None
        if latent is not None:
            latent_dist = self._mahalanobis(latent)
            # Normalize latent distance via a soft logistic with a scale of 5.0
            latent_component = float(1.0 / (1.0 + np.exp(-(latent_dist - 5.0) / 2.0)))
        else:
            latent_component = 0.5

        w_sum = self.tanimoto_weight + self.latent_weight
        ood_score = (self.tanimoto_weight * tanimoto_dist +
                     self.latent_weight * latent_component) / w_sum

        is_ood = bool(ood_score >= self.ood_threshold)
        # Confidence is reduced as OOD increases: 1.0 in-dist -> ~0.2 far OOD
        confidence_modifier = float(max(0.2, 1.0 - ood_score))

        return {
            'ood_score': round(float(ood_score), 4),
            'is_ood': is_ood,
            'confidence_modifier': round(confidence_modifier, 4),
            'nearest_neighbor_similarity': round(float(nearest_sim), 4),
            'tanimoto_distance': round(float(tanimoto_dist), 4),
            'latent_distance': round(float(latent_dist), 4) if latent_dist is not None else None,
            'ood_threshold': self.ood_threshold
        }

    def fit_latent_distribution(self, train_smiles: List[str]):
        """Compute centroid (and precision) of training-set latent embeddings."""
        embs = []
        for smi in train_smiles[: self.max_train_samples]:
            e = self._latent_embedding(smi)
            if e is not None:
                embs.append(e)
        if not embs:
            return
        X = np.vstack(embs)
        self.latent_centroid = X.mean(axis=0)
        try:
            cov = np.cov(X, rowvar=False)
            self.latent_precision = np.linalg.inv(cov + 1e-6 * np.eye(cov.shape[0]))
        except Exception:
            self.latent_precision = None
        logger.info(f"✅ Latent OOD distribution fitted on {len(embs)} molecules")


if __name__ == "__main__":
    print("Testing OODDetector...")
    print("=" * 60)
    # Lightweight test without a real predictor
    class _DummyPredictor:
        device = 'cpu'
        models = {}
        def _smiles_to_graph(self, s):
            return None
    det = OODDetector(_DummyPredictor())
    for smi in ["CC(=O)OC1=CC=CC=C1C(=O)O", "CCO", "C1=CC=CC=C1"]:
        print(smi, "->", det.evaluate(smi))
    print("\n✅ OODDetector ready!")
