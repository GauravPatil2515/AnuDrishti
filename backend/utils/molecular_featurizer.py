"""
Unified SMILES Featurization Module
====================================
Single canonical featurization for all GNN models.
Used by: unified_predictor, faithfulness_validator, attention_ginet, ddi_predictor
"""
from rdkit import Chem
from rdkit.Chem import AllChem
import torch
import torch.nn.functional as F
from torch_geometric.data import Data
import numpy as np


# ──────────────────────────────────────────────────────────────────────────────
# Canonical atom / bond vocabularies (matching training scripts)
# ──────────────────────────────────────────────────────────────────────────────

ATOM_LIST = list(range(1, 119))  # atomic numbers 1-118
CHIRALITY_LIST = [
    Chem.rdchem.ChiralType.CHI_UNSPECIFIED,
    Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CW,
    Chem.rdchem.ChiralType.CHI_TETRAHEDRAL_CCW,
]
BOND_LIST = [
    Chem.rdchem.BondType.SINGLE,
    Chem.rdchem.BondType.DOUBLE,
    Chem.rdchem.BondType.TRIPLE,
    Chem.rdchem.BondType.AROMATIC,
]
BONDDIR_LIST = [
    Chem.rdchem.BondDir.NONE,
    Chem.rdchem.BondDir.ENDUPRIGHT,
    Chem.rdchem.BondDir.ENDDOWNRIGHT,
]


def _atom_features_simple(atom):
    """Simple atom features: [atomic_num_idx, chirality_idx] for Attention-GIN style models."""
    at_num = atom.GetAtomicNum()
    chir = atom.GetChiralTag()
    return [
        ATOM_LIST.index(at_num) if at_num in ATOM_LIST else len(ATOM_LIST),
        CHIRALITY_LIST.index(chir) if chir in CHIRALITY_LIST else 0,
    ]


def _atom_features_rich(atom):
    """Rich atom features for models needing more descriptors."""
    return [
        atom.GetAtomicNum(),
        atom.GetDegree(),
        atom.GetFormalCharge(),
        int(atom.GetHybridization()),
        int(atom.GetIsAromatic()),
        atom.GetTotalNumHs(),
        int(atom.IsInRing()),
        atom.GetImplicitValence(),
        int(atom.GetChiralTag()),
    ]


def _bond_features(bond):
    """Bond features: [bond_type_idx, bond_dir_idx]."""
    bt = bond.GetBondType()
    bd = bond.GetBondDir()
    return [
        BOND_LIST.index(bt) if bt in BOND_LIST else len(BOND_LIST),
        BONDDIR_LIST.index(bd) if bd in BONDDIR_LIST else 0,
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def smiles_to_data(smiles: str, add_hs: bool = False, rich_features: bool = False):
    """
    Convert SMILES to PyG Data object.
    
    Args:
        smiles: SMILES string
        add_hs: Whether to add explicit hydrogens (for FaithfulnessValidator)
        rich_features: Use rich atom features (9-dim) vs simple (2-dim)
    
    Returns:
        torch_geometric.data.Data or None if invalid SMILES
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    
    if add_hs:
        mol = Chem.AddHs(mol)
    
    # Atom features
    if rich_features:
        atom_feats = [_atom_features_rich(atom) for atom in mol.GetAtoms()]
    else:
        atom_feats = [_atom_features_simple(atom) for atom in mol.GetAtoms()]
    
    x = torch.tensor(atom_feats, dtype=torch.long if not rich_features else torch.float)
    
    # Edge index & attributes
    row, col, edge_feats = [], [], []
    for bond in mol.GetBonds():
        i, j = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
        row += [i, j]
        col += [j, i]
        bf = _bond_features(bond)
        edge_feats.extend([bf, bf])
    
    if len(row) == 0:
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0, 2), dtype=torch.long)
    else:
        edge_index = torch.tensor([row, col], dtype=torch.long)
        edge_attr = torch.tensor(edge_feats, dtype=torch.long)
    
    return Data(x=x, edge_index=edge_index, edge_attr=edge_attr)


def smiles_to_graph_simple(smiles: str):
    """Legacy alias for Attention-GIN style (simple 2D features, no Hs)."""
    return smiles_to_data(smiles, add_hs=False, rich_features=False)


def smiles_to_graph_rich(smiles: str):
    """Legacy alias for XGBoost/GPS style (rich features, no Hs)."""
    return smiles_to_data(smiles, add_hs=False, rich_features=True)


def smiles_to_data_with_hs(smiles: str):
    """Legacy alias for FaithfulnessValidator (simple 2D features + Hs)."""
    return smiles_to_data(smiles, add_hs=True, rich_features=False)


# ──────────────────────────────────────────────────────────────────────────────
# RDKit descriptor extraction (for XGBoost)
# ──────────────────────────────────────────────────────────────────────────────

def extract_rdkit_descriptors(smiles: str, n_descriptors: int = 306) -> np.ndarray:
    """Extract standardized RDKit descriptors for XGBoost models."""
    try:
        from rdkit.Chem import Descriptors
        from rdkit.ML.Descriptors import MoleculeDescriptors
        
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return np.zeros(n_descriptors)
        
        descriptor_names = [desc[0] for desc in Descriptors.descList]
        calc = MoleculeDescriptors.MolecularDescriptorCalculator(descriptor_names)
        descriptors = np.array(calc.CalcDescriptors(mol))
        descriptors = np.nan_to_num(descriptors, nan=0.0, posinf=0.0, neginf=0.0)
        
        if len(descriptors) < n_descriptors:
            descriptors = np.pad(descriptors, (0, n_descriptors - len(descriptors)), 'constant')
        elif len(descriptors) > n_descriptors:
            descriptors = descriptors[:n_descriptors]
        
        return descriptors.astype(np.float64)
    except Exception:
        return np.zeros(n_descriptors)


# ──────────────────────────────────────────────────────────────────────────────
# MC Dropout Utility
# ──────────────────────────────────────────────────────────────────────────────

def mc_dropout_predict(model, data, n_samples: int = 50, device=None):
    """
    Run MC Dropout inference for uncertainty estimation.
    
    Args:
        model: PyTorch model with dropout layers
        data: PyG Data or Batch
        n_samples: Number of stochastic forward passes
        device: torch device (auto-detected if None)
    
    Returns:
        dict with keys: mean_probs, std_probs, ci_low, ci_high, all_probs
    """
    if device is None:
        device = next(model.parameters()).device
    
    model.train()  # Enable dropout
    data = data.to(device)
    
    all_probs = []
    with torch.no_grad():
        for _ in range(n_samples):
            logits = model(data.x, data.edge_index, data.edge_attr if hasattr(data, 'edge_attr') else None)
            if isinstance(logits, tuple):
                logits = logits[0]  # Handle models returning (logits, attention)
            probs = torch.sigmoid(logits).cpu().numpy()
            all_probs.append(probs)
    
    model.eval()  # Restore eval mode
    
    all_probs = np.array(all_probs)  # [n_samples, n_nodes_or_graphs, n_tasks]
    mean_probs = np.mean(all_probs, axis=0)
    std_probs = np.std(all_probs, axis=0)
    ci_low = np.percentile(all_probs, 2.5, axis=0)
    ci_high = np.percentile(all_probs, 97.5, axis=0)
    
    return {
        'mean_probs': mean_probs,
        'std_probs': std_probs,
        'ci_low': ci_low,
        'ci_high': ci_high,
        'all_probs': all_probs,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Attention extraction
# ──────────────────────────────────────────────────────────────────────────────

def extract_attention(model, data, device=None):
    """
    Extract attention weights from Attention-GIN style models.
    
    Returns:
        node_attention: [n_nodes] or edge_attention: [n_edges]
    """
    if device is None:
        device = next(model.parameters()).device
    
    model.eval()
    data = data.to(device)
    
    with torch.no_grad():
        out = model(data.x, data.edge_index, data.edge_attr if hasattr(data, 'edge_attr') else None)
        
    if isinstance(out, tuple):
        logits, attention = out
        return attention
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Validation
# ──────────────────────────────────────────────────────────────────────────────

def validate_smiles(smiles: str):
    """Validate SMILES and return (mol, error_msg)."""
    if not smiles or not isinstance(smiles, str):
        return None, "Empty or invalid SMILES string"
    mol = Chem.MolFromSmiles(smiles.strip())
    if mol is None:
        return None, f"Invalid SMILES: {smiles}"
    return mol, None


# ──────────────────────────────────────────────────────────────────────────────
# Backward-compatibility aliases (for existing imports)
# ──────────────────────────────────────────────────────────────────────────────

# For unified_predictor.UnifiedADMETPredictor._smiles_to_graph_simple
def _smiles_to_graph_simple(self, smiles):
    return smiles_to_graph_simple(smiles)

# For unified_predictor.UnifiedADMETPredictor._smiles_to_graph
def _smiles_to_graph(self, smiles):
    return smiles_to_graph_rich(smiles)

# For faithfulness_validator.FaithfulnessValidator._smiles_to_data
def _smiles_to_data(self, smiles):
    return smiles_to_data_with_hs(smiles)


if __name__ == "__main__":
    # Quick test
    test_smiles = ["CCO", "CC(=O)Oc1ccccc1C(=O)O", "c1ccccc1"]
    for smi in test_smiles:
        data = smiles_to_data(smi)
        print(f"{smi}: nodes={data.x.shape[0]}, edges={data.edge_index.shape[1]}, feat_dim={data.x.shape[1]}")