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
import os
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
        max_train_samples: int = 2000,
        reference_path: Optional[str] = None
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
            reference_path: Path to a ``.npz`` file with a pre-computed reference
                distribution (fingerprints + latent centroid + precision). When it
                exists it is loaded directly; otherwise the distribution is built,
                fitted and persisted there for fast startup next time.
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
        self.reference_path = reference_path

        self.fingerprints = fingerprints
        self.latent_centroid = latent_centroid
        self.latent_precision = latent_precision
        self._train_smiles: List[str] = []

        # Prefer a pre-computed reference distribution for speed + consistency.
        if reference_path and os.path.exists(reference_path):
            try:
                self._load_reference(reference_path)
                logger.info(f"✅ OOD reference distribution loaded from {reference_path}")
                return
            except Exception as e:
                logger.warning(f"⚠️ Could not load OOD reference ({e}); rebuilding it")

        if fingerprints is None:
            self._build_reference_set()

        # Fit the latent (GNN-embedding) distribution when a predictor is available,
        # so the Mahalanobis signal is meaningful rather than a null Euclidean norm.
        if predictor is not None and self.fingerprints is not None:
            try:
                self.fit_latent_distribution(self._train_smiles)
            except Exception as e:
                logger.warning(f"⚠️ Latent OOD distribution fit failed: {e}")

        if reference_path:
            try:
                self.save_reference(reference_path)
            except Exception as e:
                logger.warning(f"⚠️ Could not persist OOD reference: {e}")

    # ─────────────────────────────────────────────────────────────────────
    # Reference-set persistence
    # ─────────────────────────────────────────────────────────────────────
    def _load_reference(self, path: str):
        """Load a pre-computed reference distribution from an ``.npz`` file."""
        data = np.load(path, allow_pickle=True)
        self.fingerprints = data['fingerprints']
        self.latent_centroid = (
            data['latent_centroid'] if data['latent_centroid'].size else None
        )
        self.latent_precision = (
            data['latent_precision'] if data['latent_precision'].size else None
        )
        self._train_smiles = [str(s) for s in data['train_smiles']]

    def save_reference(self, path: str):
        """Persist the reference distribution (fingerprints + latent stats)."""
        os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
        np.savez(
            path,
            fingerprints=self.fingerprints,
            latent_centroid=(
                self.latent_centroid
                if self.latent_centroid is not None else np.zeros((0,), dtype=np.float64)
            ),
            latent_precision=(
                self.latent_precision
                if self.latent_precision is not None else np.zeros((0, 0), dtype=np.float64)
            ),
            train_smiles=np.array(self._train_smiles, dtype=object)
        )
        logger.info(f"✅ OOD reference distribution saved to {path}")

    # ─────────────────────────────────────────────────────────────────────
    # Reference-set construction
    # ─────────────────────────────────────────────────────────────────────
    # A diverse, drug-like reference set spanning the common scaffolds a
    # medicinal-chemist is likely to query. Covering heterocycles, aromatics,
    # NSAIDs, antibiotics, CNS drugs, etc. makes Tanimoto + latent OOD signals
    # meaningful (SIH audit Bug #1: the previous 15-molecule set was too small
    # to anchor a real training distribution). Invalid entries are skipped.
    DEFAULT_REFERENCE_SMILES = [
        "CC(=O)OC1=CC=CC=C1C(=O)O",              # Aspirin
        "CC(=O)NC1=CC=C(C=C1)O",                 # Acetaminophen
        "CC(C)CC1=CC=C(C=C1)C(C)C(=O)O",         # Ibuprofen
        "CN1C=NC2=C1C(=O)N(C(=O)N2C)C",          # Caffeine
        "CCO",                                   # Ethanol
        "c1ccccc1",                              # Benzene
        "Cc1ccccc1",                             # Toluene
        "O=C(O)c1ccccc1",                        # Benzoic acid
        "c1ccc2[nH]ccc2c1",                      # Indole
        "C1CCCCC1",                              # Cyclohexane
        "c1ccc(cc1)c2ccccc2",                    # Biphenyl
        "O=C1NC(=O)C(N2C(=O)c3ccccc3C2=O)CC1",   # Thalidomide
        "CN1CCCC1C2=CN=CC=C2",                   # Nicotine
        "CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C",   # Testosterone
        "CC1(C)SC2C(NC(=O)Cc3ccccc3)C(=O)N2C1C(=O)O",  # Penicillin G
        "CC1(C)SC2C(NC(=O)C(O)Cc3ccc(O)cc3)C(=O)N2C1C(=O)O",  # Amoxicillin
        "OC(=O)C1CCN(C2=C(C(=O)C=C(C2)F)N2CCNCC2)C1",  # Ciprofloxacin
        "CC(C)Cc1ccc(cc1)[C@@H](C)C(=O)O",       # Naproxen
        "O=C(O)Cc1ccccc1Nc1c(Cl)cccc1Cl",        # Diclofenac
        "CC(=O)CC(c1ccccc1)C(=O)C1(C)C(=O)OC(c2ccccc2)C1=O",  # Warfarin
        "CC(C)(C)c1ccc(cc1)C(C)C(=O)N1CC[C@@H](C1)c2ccccc2",  # Atorvastatin
        "CN(C)C(=N)NC(N)=N",                     # Metformin
        "O=C(O)c1ccccc1O",                       # Salicylic acid
        "NCCc1ccc(O)c(O)c1",                     # Dopamine
        "NCCc1c[nH]c2ccc(O)cc12",                # Serotonin
        "NCCNc1cnc[nH]c1",                       # Histamine
        "COc1ccc2c(c1)CC1(O)CC(C2)NCC1",         # Morphine
        "NC(C)CCN(CC)CCc1ccnc2cc(Cl)ccc12",      # Chloroquine
        "CC1=NOC(=N1)C(=O)CO",                   # Metronidazole
        "CCCC1=NN(C)C2=C1NC(=NC2=O)c1ccccc1S(=O)(=O)N1CCN(CC1)C",  # Sildenafil
        "CNCCCOc1ccc(cc1)C(F)(F)F",              # Fluoxetine
        "CCOC(=O)C1C2=C(NC3=C(C=CC=C3C)C2C(=C(N1)C)C(=O)OC)COCCN",  # Amlodipine
        "N1(CCCC1)C(=O)NC(Cc1ccccc1)C(=O)O",     # Lisinopril
        "CCOc1ccc(cc1)c2nnc(n2)CCc3ccccc3N",     # Losartan
        "N1(CCCC1)C(=O)CC(C)C(=O)O",             # Gabapentin
        "c1ccc(cc1)O",                           # Phenol
        "Nc1ccccc1",                             # Aniline
        "CC(=O)O",                               # Acetic acid
        "NC(N)=O",                               # Urea
        "NCC(=O)O",                              # Glycine
        "OCC(O)C(O)C(O)C(O)C(=O)O",              # Glucose (open chain)
        "c1ccncc1",                              # Pyridine
        "c1cncnc1",                              # Pyrimidine
        "c1c[nH]cn1",                            # Imidazole
        "c1c[nH]n1",                             # Pyrazole
        "c1ccoc1",                              # Furan
        "c1ccsc1",                              # Thiophene
        "c1cc[nH]c1",                            # Pyrrole
        "c1nc2c(n1)ncnc2",                       # Purine
        "c1ccc2ncccc2c1",                        # Quinoline
        "c1ccc2c(c1)cncc2",                      # Isoquinoline
        "c1ccc2ccccc2c1",                        # Naphthalene
        "c1ccc2cc3ccccc3cc2c1",                  # Anthracene
        "c1ccc2c(c1)ccc3ccccc23",                # Phenanthrene
        "c1cc[n+](=O)cc1",                       # Pyridine N-oxide
        "O=Cc1ccccc1",                           # Benzaldehyde
        "CC(=O)C",                               # Acetone
        "CC=O",                                   # Acetaldehyde
        "CO",                                    # Methanol
        "ClC(Cl)Cl",                             # Chloroform
        "ClCCl",                                 # Dichloromethane
        "Clc1ccccc1",                            # Chlorobenzene
        "O=[N+]([O-])c1ccccc1",                  # Nitrobenzene
        "COc1ccccc1",                            # Anisole
        "C=Cc1ccccc1",                           # Styrene
        "CCc1ccccc1",                            # Ethylbenzene
        "Cc1cccc(C)c1",                          # Xylene
        "Oc1ccccc1O",                            # Catechol
        "Oc1cccc(O)c1",                          # Resorcinol
        "Oc1ccc(O)cc1",                          # Hydroquinone
        "O=[N+]([O-])c1ccc(O)cc1",               # 4-nitrophenol
        "CC(=O)Nc1ccccc1",                       # Acetanilide
        "NC(=O)c1ccccc1",                        # Benzamide
        "N#Cc1ccccc1",                           # Benzonitrile
        "OCc1ccccc1",                            # Benzyl alcohol
        "NCc1ccccc1",                            # Benzylamine
        "Cn1c(=O)n(C)c2ncn(C)c2c1=O",            # Theophylline
        "Nc1ncnc2ncnc12",                        # Adenine
        "Nc1nc2c(n1)ncnc2O",                     # Guanine
        "Nc1cc(=O)[nH]cn1",                      # Cytosine
        "Cc1c[nH]c(=O)[nH]c1=O",                 # Thymine
        "O=c1ccnc[nH]1",                         # Uracil
        "O=C1CC(=O)NC(=O)N1",                    # Barbituric acid
        "CCC(C)C1C(=O)NC(=O)NC1=O",              # Phenobarbital
        "O=C1N=C(C(=O)Nc2ccccc2)C3=CC=CC=C3N1C", # Diazepam
        "NC(C)C(O)c1ccc(O)c(O)c1",               # Epinephrine
        "CCOC(=O)CC(=O)N1CCN(CC1)C(=O)C",        # Lidocaine
        "CCOC(=O)C1=CC=C(C=C1)NCCN(CC)CC",       # Procaine
        "CN1CC2CCC1CC(c1ccc(F)cc1)C2",           # Citalopram
        "O=S(=O)(N)Nc1ccc(cc1)S(=O)(=O)c1ccc(cc1)N",  # Furosemide
        "c1ccc2c(c1)CC(O)N2",                     # Indoline
        "O=C(O)Cc1ccccc1",                       # Phenylacetic acid
        "Cc1ccncc1C",                             # Methylpyridine
    ]

    def _build_reference_set(self):
        """Build a diverse drug-like reference set.

        Used only when no explicit training fingerprints / reference file are
        supplied. The reference molecules cover a wide range of common scaffolds
        so Tanimoto + latent distances are meaningful for typical queries.
        """
        ref_smiles = self.DEFAULT_REFERENCE_SMILES
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
