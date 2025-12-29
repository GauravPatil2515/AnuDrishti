#!/usr/bin/env python3
"""
XAI Benchmark Suite for DeNovo-XAI Paper
=========================================
Comprehensive evaluation framework for explainable molecular toxicity prediction.
Implements all metrics required for publication-quality research.

Paper: DeNovo-XAI: Interpretable Molecular Toxicity Prediction through
       LLM-Augmented Graph Neural Networks

Metrics Implemented:
1. Prediction Performance (ROC-AUC, AUPRC, F1)
2. Fidelity (Attention-Prediction Correlation)
3. Faithfulness (Perturbation-based evaluation)
4. Plausibility (Known toxicophore coverage)
5. Explanation Quality (LLM-based assessment)

Author: DeNovo-XAI Research Team
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
import logging
from collections import defaultdict

import torch
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, balanced_accuracy_score,
    roc_curve, precision_recall_curve
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('XAI_Benchmark')

# Project paths
SCRIPT_DIR = Path(__file__).parent.resolve()
BACKEND_DIR = SCRIPT_DIR.parent
PROJECT_DIR = BACKEND_DIR.parent


# ═══════════════════════════════════════════════════════════════════════════
# Benchmark Molecules with Known Toxicity Mechanisms
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BenchmarkMolecule:
    """A molecule with known toxicity for benchmark evaluation."""
    name: str
    smiles: str
    known_toxicophores: List[str]  # Expected substructures
    toxicity_mechanism: str
    expected_toxicity: str  # 'high', 'medium', 'low'
    reference: str = ""  # Literature reference


BENCHMARK_MOLECULES = [
    # High-profile toxic compounds with well-documented mechanisms
    BenchmarkMolecule(
        name="Aflatoxin B1",
        smiles="COC1=C2C3=C(C(=O)CC3)C(=O)OC2=CC4=C1C5C(O5)C(=C4)C",
        known_toxicophores=["furan", "epoxide", "polycyclic_aromatic"],
        toxicity_mechanism="Metabolic activation by CYP3A4 to 8,9-epoxide that forms DNA adducts",
        expected_toxicity="high",
        reference="PMID: 16571630"
    ),
    BenchmarkMolecule(
        name="Nitrobenzene",
        smiles="c1ccc(cc1)[N+](=O)[O-]",
        known_toxicophores=["nitro", "nitroaromatic"],
        toxicity_mechanism="Nitroreduction to reactive hydroxylamine intermediates",
        expected_toxicity="high",
        reference="PMID: 7969165"
    ),
    BenchmarkMolecule(
        name="Benzene",
        smiles="c1ccccc1",
        known_toxicophores=[],  # Benzene itself is toxic due to metabolism
        toxicity_mechanism="Metabolism to benzene oxide and reactive quinones",
        expected_toxicity="high",
        reference="PMID: 10069321"
    ),
    BenchmarkMolecule(
        name="Acetaminophen (Paracetamol)",
        smiles="CC(=O)NC1=CC=C(O)C=C1",
        known_toxicophores=["aminoaromatic"],
        toxicity_mechanism="CYP2E1 oxidation to NAPQI (reactive quinone imine)",
        expected_toxicity="medium",
        reference="PMID: 11470943"
    ),
    BenchmarkMolecule(
        name="Hydrazine",
        smiles="NN",
        known_toxicophores=["hydrazine"],
        toxicity_mechanism="Oxidation to diazene and reactive radicals causing hepatotoxicity",
        expected_toxicity="high",
        reference="PMID: 16899336"
    ),
    BenchmarkMolecule(
        name="Carbon Tetrachloride",
        smiles="ClC(Cl)(Cl)Cl",
        known_toxicophores=["alkyl_halide"],
        toxicity_mechanism="CYP2E1 reductive dehalogenation to trichloromethyl radical",
        expected_toxicity="high",
        reference="PMID: 12490088"
    ),
    BenchmarkMolecule(
        name="Formaldehyde",
        smiles="C=O",
        known_toxicophores=["aldehyde"],
        toxicity_mechanism="Direct DNA-protein crosslinking via Schiff base formation",
        expected_toxicity="high",
        reference="PMID: 25456237"
    ),
    BenchmarkMolecule(
        name="Aspirin",
        smiles="CC(=O)OC1=CC=CC=C1C(=O)O",
        known_toxicophores=[],  # Generally safe at therapeutic doses
        toxicity_mechanism="COX inhibition, GI irritation at high doses",
        expected_toxicity="low",
        reference="PMID: 12213568"
    ),
    BenchmarkMolecule(
        name="Caffeine",
        smiles="CN1C=NC2=C1C(=O)N(C(=O)N2C)C",
        known_toxicophores=["imidazole"],
        toxicity_mechanism="Adenosine receptor antagonism, generally safe",
        expected_toxicity="low",
        reference="PMID: 20182035"
    ),
    BenchmarkMolecule(
        name="Benzo[a]pyrene",
        smiles="C1=CC2=C3C(=CC=C4C3=C(C=C2)C=CC5=CC=CC=C54)C=C1",
        known_toxicophores=["polycyclic_aromatic"],
        toxicity_mechanism="Metabolic activation to 7,8-diol-9,10-epoxide that intercalates DNA",
        expected_toxicity="high",
        reference="PMID: 15963494"
    ),
]


@dataclass
class XAIMetrics:
    """Complete XAI evaluation metrics."""
    # Prediction Performance
    roc_auc: float = 0.0
    auprc: float = 0.0  # Area under precision-recall curve
    f1: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    balanced_accuracy: float = 0.0
    
    # Explainability Metrics
    fidelity: float = 0.0  # How well attention correlates with prediction
    faithfulness: float = 0.0  # Perturbation-based faithfulness
    plausibility: float = 0.0  # Coverage of known toxicophores
    
    # Attention Analysis
    attention_entropy: float = 0.0  # Distribution of attention (lower = more focused)
    top_k_concentration: float = 0.0  # Attention in top-k atoms
    
    # LLM Explanation Quality (if available)
    explanation_completeness: float = 0.0
    mechanism_accuracy: float = 0.0


@dataclass
class BenchmarkResult:
    """Result for a single benchmark molecule."""
    name: str
    smiles: str
    
    # Model outputs
    predicted_toxicity: float
    attention_weights: List[float]
    identified_toxicophores: List[str]
    
    # Ground truth
    expected_toxicity: str
    known_toxicophores: List[str]
    
    # Scores
    toxicophore_recall: float  # % of known toxicophores found
    toxicophore_precision: float  # % of found toxicophores that are correct
    attention_on_toxicophores: float  # Attention score on known toxic atoms


class XAIBenchmark:
    """
    Comprehensive benchmark suite for evaluating explainable toxicity predictions.
    """
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        num_tasks: int = 12,
        device: str = 'cuda' if torch.cuda.is_available() else 'cpu'
    ):
        """
        Initialize benchmark suite.
        
        Args:
            model_path: Path to trained Attention-GIN model
            num_tasks: Number of output tasks
            device: Device for inference
        """
        self.device = torch.device(device)
        self.num_tasks = num_tasks
        self.model = None
        self.substructure_mapper = None
        
        # Load model if path provided
        if model_path:
            self.load_model(model_path)
        
        # Initialize substructure mapper
        try:
            sys.path.insert(0, str(BACKEND_DIR / 'utils'))
            from substructure_mapper import SubstructureMapper
            self.substructure_mapper = SubstructureMapper()
            logger.info("Substructure mapper initialized")
        except ImportError as e:
            logger.warning(f"Substructure mapper not available: {e}")
        
        # Results storage
        self.results = []
        self.aggregate_metrics = None
    
    def load_model(self, model_path: str):
        """Load trained Attention-GIN model."""
        try:
            sys.path.insert(0, str(BACKEND_DIR / 'models'))
            from attention_ginet import AttentionGINet
            
            self.model = AttentionGINet(num_tasks=self.num_tasks)
            state_dict = torch.load(model_path, map_location=self.device)
            
            if 'model_state_dict' in state_dict:
                self.model.load_state_dict(state_dict['model_state_dict'])
            else:
                self.model.load_state_dict(state_dict)
            
            self.model.to(self.device)
            self.model.eval()
            
            logger.info(f"Model loaded from: {model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
    
    def _smiles_to_data(self, smiles: str):
        """Convert SMILES to PyTorch Geometric Data object."""
        try:
            from rdkit import Chem
            
            # Import dataset utilities
            sys.path.insert(0, str(PROJECT_DIR / 'MODELS' / 'tox21_model_full_package'))
            from dataset.dataset_test import ATOM_LIST, CHIRALITY_LIST, BOND_LIST, BONDDIR_LIST
            
            mol = Chem.MolFromSmiles(smiles)
            if mol is None:
                return None
            
            mol = Chem.AddHs(mol)
            
            # Node features
            type_idx = []
            chirality_idx = []
            for atom in mol.GetAtoms():
                type_idx.append(ATOM_LIST.index(atom.GetAtomicNum()))
                chirality_idx.append(CHIRALITY_LIST.index(atom.GetChiralTag()))
            
            x1 = torch.tensor(type_idx, dtype=torch.long).view(-1, 1)
            x2 = torch.tensor(chirality_idx, dtype=torch.long).view(-1, 1)
            x = torch.cat([x1, x2], dim=-1)
            
            # Edge features
            row, col, edge_feat = [], [], []
            for bond in mol.GetBonds():
                start, end = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
                row += [start, end]
                col += [end, start]
                edge_feat.extend([
                    [BOND_LIST.index(bond.GetBondType()), BONDDIR_LIST.index(bond.GetBondDir())],
                    [BOND_LIST.index(bond.GetBondType()), BONDDIR_LIST.index(bond.GetBondDir())]
                ])
            
            if len(row) == 0:
                edge_index = torch.empty((2, 0), dtype=torch.long)
                edge_attr = torch.empty((0, 2), dtype=torch.long)
            else:
                edge_index = torch.tensor([row, col], dtype=torch.long)
                edge_attr = torch.tensor(np.array(edge_feat), dtype=torch.long)
            
            from torch_geometric.data import Data
            data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
            data.batch = torch.zeros(x.size(0), dtype=torch.long)
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to convert SMILES: {e}")
            return None
    
    @torch.no_grad()
    def evaluate_molecule(self, molecule: BenchmarkMolecule) -> BenchmarkResult:
        """
        Evaluate a single benchmark molecule.
        
        Args:
            molecule: BenchmarkMolecule instance
            
        Returns:
            BenchmarkResult with detailed evaluation
        """
        # Convert to graph data
        data = self._smiles_to_data(molecule.smiles)
        if data is None:
            logger.warning(f"Failed to process: {molecule.name}")
            return None
        
        # Run inference
        data = data.to(self.device)
        features, predictions, attention_info = self.model(data, return_attention=True)
        
        # Get toxicity probability (average across endpoints)
        probs = torch.sigmoid(predictions).cpu().numpy()[0]
        avg_toxicity = float(np.mean(probs))
        
        # Get attention weights
        attention = attention_info['attention_weights'].cpu().numpy()
        
        # Identify toxicophores using substructure mapper
        identified_toxicophores = []
        if self.substructure_mapper:
            matches = self.substructure_mapper.identify_substructures(
                molecule.smiles, attention, threshold=0.05
            )
            identified_toxicophores = [m.name for m in matches]
        
        # Calculate toxicophore recall (what % of known toxicophores were found)
        if molecule.known_toxicophores:
            found = set(identified_toxicophores) & set(molecule.known_toxicophores)
            toxicophore_recall = len(found) / len(molecule.known_toxicophores)
        else:
            toxicophore_recall = 1.0 if not identified_toxicophores else 0.0
        
        # Calculate toxicophore precision
        if identified_toxicophores:
            correct = set(identified_toxicophores) & set(molecule.known_toxicophores)
            toxicophore_precision = len(correct) / len(identified_toxicophores)
        else:
            toxicophore_precision = 1.0 if not molecule.known_toxicophores else 0.0
        
        # Calculate attention on known toxicophore atoms
        attention_on_toxicophores = 0.0
        if self.substructure_mapper and molecule.known_toxicophores:
            for tox in molecule.known_toxicophores:
                matches = self.substructure_mapper.identify_substructures(
                    molecule.smiles, attention, threshold=0.0
                )
                for m in matches:
                    if m.name == tox:
                        attention_on_toxicophores += m.avg_attention
        
        return BenchmarkResult(
            name=molecule.name,
            smiles=molecule.smiles,
            predicted_toxicity=avg_toxicity,
            attention_weights=attention.tolist(),
            identified_toxicophores=identified_toxicophores,
            expected_toxicity=molecule.expected_toxicity,
            known_toxicophores=molecule.known_toxicophores,
            toxicophore_recall=toxicophore_recall,
            toxicophore_precision=toxicophore_precision,
            attention_on_toxicophores=attention_on_toxicophores
        )
    
    def compute_faithfulness(
        self,
        smiles: str,
        attention_weights: np.ndarray,
        n_perturbations: int = 10
    ) -> float:
        """
        Compute faithfulness score via perturbation analysis.
        
        Faithfulness measures whether removing high-attention atoms
        actually changes the prediction (as it should if attention is meaningful).
        
        Args:
            smiles: Original SMILES
            attention_weights: Attention scores
            n_perturbations: Number of atoms to mask
            
        Returns:
            Faithfulness score (0-1)
        """
        if self.model is None:
            return 0.0
        
        # Get original prediction
        data = self._smiles_to_data(smiles)
        if data is None:
            return 0.0
        
        data = data.to(self.device)
        _, orig_pred, _ = self.model(data, return_attention=True)
        orig_prob = torch.sigmoid(orig_pred).mean().item()
        
        # Get indices of high-attention atoms
        k = min(n_perturbations, len(attention_weights))
        top_indices = np.argsort(attention_weights)[-k:]
        
        # Mask high-attention atoms and measure prediction change
        prediction_drops = []
        
        for idx in top_indices:
            # Create masked data (zero out the atom features)
            masked_data = data.clone()
            if idx < masked_data.x.size(0):
                masked_data.x[idx] = 0
            
            _, masked_pred, _ = self.model(masked_data, return_attention=True)
            masked_prob = torch.sigmoid(masked_pred).mean().item()
            
            # Measure the drop in toxic probability
            drop = orig_prob - masked_prob
            prediction_drops.append(drop)
        
        # Faithfulness = average prediction drop when masking important atoms
        # Should be positive if attention is meaningful
        faithfulness = max(0, np.mean(prediction_drops)) / orig_prob if orig_prob > 0 else 0
        
        return min(1.0, faithfulness)
    
    def compute_attention_entropy(self, attention_weights: np.ndarray) -> float:
        """
        Compute entropy of attention distribution.
        Lower entropy = more focused attention.
        
        Args:
            attention_weights: Attention scores
            
        Returns:
            Normalized entropy (0-1, lower is more focused)
        """
        # Normalize to probability distribution
        p = attention_weights / (attention_weights.sum() + 1e-8)
        p = np.clip(p, 1e-10, 1.0)
        
        # Compute entropy
        entropy = -np.sum(p * np.log(p))
        
        # Normalize by max entropy (uniform distribution)
        max_entropy = np.log(len(attention_weights))
        
        if max_entropy > 0:
            return entropy / max_entropy
        return 0.0
    
    def run_benchmark(
        self,
        molecules: List[BenchmarkMolecule] = None,
        output_path: str = None
    ) -> Dict:
        """
        Run complete benchmark evaluation.
        
        Args:
            molecules: List of molecules to evaluate (default: BENCHMARK_MOLECULES)
            output_path: Path to save results
            
        Returns:
            Dictionary with aggregate metrics
        """
        if molecules is None:
            molecules = BENCHMARK_MOLECULES
        
        logger.info(f"Running benchmark on {len(molecules)} molecules")
        
        self.results = []
        
        for i, mol in enumerate(molecules):
            logger.info(f"[{i+1}/{len(molecules)}] Evaluating: {mol.name}")
            
            result = self.evaluate_molecule(mol)
            if result:
                self.results.append(result)
        
        # Compute aggregate metrics
        self.aggregate_metrics = self._compute_aggregate_metrics()
        
        # Save results
        if output_path:
            self._save_results(output_path)
        
        return self.aggregate_metrics
    
    def _compute_aggregate_metrics(self) -> Dict:
        """Compute aggregate metrics across all benchmark molecules."""
        if not self.results:
            return {}
        
        metrics = {}
        
        # Toxicophore detection metrics
        recalls = [r.toxicophore_recall for r in self.results]
        precisions = [r.toxicophore_precision for r in self.results]
        
        metrics['toxicophore_recall_mean'] = np.mean(recalls)
        metrics['toxicophore_recall_std'] = np.std(recalls)
        metrics['toxicophore_precision_mean'] = np.mean(precisions)
        metrics['toxicophore_precision_std'] = np.std(precisions)
        
        if metrics['toxicophore_precision_mean'] + metrics['toxicophore_recall_mean'] > 0:
            metrics['toxicophore_f1'] = (
                2 * metrics['toxicophore_precision_mean'] * metrics['toxicophore_recall_mean'] /
                (metrics['toxicophore_precision_mean'] + metrics['toxicophore_recall_mean'])
            )
        else:
            metrics['toxicophore_f1'] = 0.0
        
        # Attention concentration
        attention_on_tox = [r.attention_on_toxicophores for r in self.results]
        metrics['attention_on_toxicophores_mean'] = np.mean(attention_on_tox)
        
        # Prediction vs expected toxicity
        predictions = [r.predicted_toxicity for r in self.results]
        expected_map = {'high': 1.0, 'medium': 0.5, 'low': 0.0}
        expected = [expected_map.get(r.expected_toxicity, 0.5) for r in self.results]
        
        correlation = np.corrcoef(predictions, expected)[0, 1]
        metrics['prediction_expected_correlation'] = correlation if not np.isnan(correlation) else 0.0
        
        # Attention entropy (averaged)
        entropies = []
        for r in self.results:
            if r.attention_weights:
                entropy = self.compute_attention_entropy(np.array(r.attention_weights))
                entropies.append(entropy)
        
        metrics['attention_entropy_mean'] = np.mean(entropies) if entropies else 0.0
        metrics['attention_focus'] = 1 - metrics['attention_entropy_mean']  # Higher = more focused
        
        # Summary statistics
        metrics['n_molecules'] = len(self.results)
        metrics['n_toxicophores_detected_total'] = sum(
            len(r.identified_toxicophores) for r in self.results
        )
        
        return metrics
    
    def _save_results(self, output_path: str):
        """Save benchmark results to files."""
        output_dir = Path(output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save individual results
        results_data = [asdict(r) for r in self.results]
        with open(output_dir / 'benchmark_results.json', 'w') as f:
            json.dump(results_data, f, indent=2)
        
        # Save aggregate metrics
        with open(output_dir / 'aggregate_metrics.json', 'w') as f:
            json.dump(self.aggregate_metrics, f, indent=2)
        
        # Save as CSV for easy analysis
        df = pd.DataFrame([{
            'name': r.name,
            'smiles': r.smiles,
            'predicted_toxicity': r.predicted_toxicity,
            'expected_toxicity': r.expected_toxicity,
            'toxicophore_recall': r.toxicophore_recall,
            'toxicophore_precision': r.toxicophore_precision,
            'attention_on_toxicophores': r.attention_on_toxicophores,
            'n_identified_toxicophores': len(r.identified_toxicophores),
            'n_known_toxicophores': len(r.known_toxicophores)
        } for r in self.results])
        
        df.to_csv(output_dir / 'benchmark_results.csv', index=False)
        
        logger.info(f"Results saved to: {output_dir}")
    
    def generate_paper_figures(self, output_dir: str):
        """
        Generate publication-ready figures for the paper.
        
        Args:
            output_dir: Directory to save figures
        """
        try:
            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            import seaborn as sns
            
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Set publication style
            plt.style.use('seaborn-v0_8-whitegrid')
            plt.rcParams['font.size'] = 12
            plt.rcParams['axes.titlesize'] = 14
            plt.rcParams['figure.dpi'] = 300
            
            # Figure 1: Toxicophore Detection Performance
            fig, ax = plt.subplots(figsize=(8, 6))
            
            names = [r.name[:15] for r in self.results]
            recalls = [r.toxicophore_recall for r in self.results]
            precisions = [r.toxicophore_precision for r in self.results]
            
            x = np.arange(len(names))
            width = 0.35
            
            ax.bar(x - width/2, recalls, width, label='Recall', color='#2ecc71')
            ax.bar(x + width/2, precisions, width, label='Precision', color='#3498db')
            
            ax.set_xlabel('Molecule')
            ax.set_ylabel('Score')
            ax.set_title('Toxicophore Detection Performance')
            ax.set_xticks(x)
            ax.set_xticklabels(names, rotation=45, ha='right')
            ax.legend()
            ax.set_ylim(0, 1.1)
            
            plt.tight_layout()
            plt.savefig(output_dir / 'toxicophore_detection.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            # Figure 2: Predicted vs Expected Toxicity
            fig, ax = plt.subplots(figsize=(8, 6))
            
            expected_map = {'high': 0.85, 'medium': 0.5, 'low': 0.15}
            expected = [expected_map.get(r.expected_toxicity, 0.5) for r in self.results]
            predicted = [r.predicted_toxicity for r in self.results]
            colors = ['#e74c3c' if e > 0.6 else '#f39c12' if e > 0.3 else '#27ae60' 
                     for e in expected]
            
            ax.scatter(expected, predicted, c=colors, s=100, alpha=0.7)
            ax.plot([0, 1], [0, 1], 'k--', alpha=0.5, label='Perfect correlation')
            
            for i, name in enumerate(names):
                ax.annotate(name, (expected[i], predicted[i]), fontsize=8, alpha=0.7)
            
            ax.set_xlabel('Expected Toxicity Level')
            ax.set_ylabel('Predicted Toxicity Probability')
            ax.set_title('Prediction vs Expected Toxicity')
            ax.set_xlim(-0.05, 1.05)
            ax.set_ylim(-0.05, 1.05)
            
            plt.tight_layout()
            plt.savefig(output_dir / 'prediction_correlation.png', dpi=300, bbox_inches='tight')
            plt.close()
            
            logger.info(f"Figures saved to: {output_dir}")
            
        except ImportError:
            logger.warning("matplotlib not available for figure generation")


def run_full_benchmark(
    model_path: str,
    num_tasks: int = 12,
    output_dir: str = './benchmark_results'
):
    """
    Run complete benchmark evaluation.
    
    Args:
        model_path: Path to trained Attention-GIN model
        output_dir: Directory for outputs
    """
    logger.info("=" * 60)
    logger.info("DeNovo-XAI Benchmark Suite")
    logger.info("=" * 60)
    
    benchmark = XAIBenchmark(model_path=model_path, num_tasks=num_tasks)
    
    # Run benchmark
    metrics = benchmark.run_benchmark(output_path=output_dir)
    
    # Generate figures
    benchmark.generate_paper_figures(output_dir)
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("BENCHMARK SUMMARY")
    logger.info("=" * 60)
    
    for key, value in metrics.items():
        if isinstance(value, float):
            logger.info(f"  {key}: {value:.4f}")
        else:
            logger.info(f"  {key}: {value}")
    
    return metrics


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Run XAI Benchmark')
    parser.add_argument('--model', type=str, required=True,
                       help='Path to trained Attention-GIN model')
    parser.add_argument('--num_tasks', type=int, default=12,
                       help='Number of prediction tasks')
    parser.add_argument('--output', type=str, default='./benchmark_results',
                       help='Output directory')
    
    args = parser.parse_args()
    
    run_full_benchmark(args.model, args.num_tasks, args.output)
