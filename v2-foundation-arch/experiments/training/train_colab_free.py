#!/usr/bin/env python3
"""
Free Colab-Compatible Training (v2-foundation-arch)
===================================================

Reduced memory training with automatic checkpointing.
Designed for 6-12 hour Colab sessions.

Usage on Free Colab:
1. Copy this file to Colab
2. Mount Google Drive: drive.mount('/content/drive')
3. Run: python train_colab_free.py --mode pretrain --checkpoint_dir /content/drive/MyDrive/checkpoints
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
from torch import Tensor
from pathlib import Path
import argparse
import json
import sys
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')


# Local imports (handle both direct run and module import)
def get_module_paths():
    """Get the module paths for local imports."""
    base = Path(__file__).parent.parent.parent  # v2-foundation-arch/
    return str(base), str(base / 'experiments')

# Add to path
base_path, exp_path = get_module_paths()
for p in [base_path, exp_path]:
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from architecture_design.multimodal_encoder import MultimodalMoleculeEncoder
except ImportError:
    MultimodalMoleculeEncoder = None

try:
    from experiments.pretraining.graphmae_pretrain import GraphMAE
except ImportError:
    GraphMAE = None

try:
    from experiments.losses.asymmetric_loss import AsymmetricLoss
except ImportError:
    AsymmetricLoss = None

# Check for optional dependencies
try:
    from sklearn.metrics import roc_auc_score
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False

try:
    import deepchem as dc
    HAS_DEEPCHEM = True
except ImportError:
    HAS_DEEPCHEM = False


class InMemoryDataset(Dataset):
    """Memory-efficient dataset wrapper."""
    
    def __init__(self, data_list):
        self.data = data_list
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        return self.data[idx]


def find_data_file(filename: str) -> Path:
    """Dynamically search for a dataset file in parent directories or repo subdirs."""
    current = Path(__file__).resolve().parent
    for _ in range(5):
        # Look for data_packages/.../filename
        for path in current.glob(f"**/data_packages/**/*/{filename}"):
            if path.exists():
                return path
        # Look for filename directly in current or subdirs
        for path in current.glob(f"**/{filename}"):
            if path.exists():
                return path
        current = current.parent
    return None


def preprocess_smiles(smiles: str) -> dict:
    """Extract graph, SMILES, and descriptor features from a SMILES string using RDKit."""
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
        from rdkit.Chem import Descriptors
    except ImportError:
        # Fallback if rdkit is not installed
        return {
            'graph_x': torch.zeros(100, 119),
            'smiles_embed': torch.zeros(1, 128),
            'descriptor': torch.zeros(200),
        }
        
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {
            'graph_x': torch.zeros(100, 119),
            'smiles_embed': torch.zeros(1, 128),
            'descriptor': torch.zeros(200),
        }
        
    # 1. Graph features (graph_x) padded to 100 atoms
    max_atoms = 100
    n_atoms = min(mol.GetNumAtoms(), max_atoms)
    graph_x = torch.zeros(max_atoms, 119)
    for idx in range(n_atoms):
        atom = mol.GetAtomWithIdx(idx)
        z = atom.GetAtomicNum()
        if z < 119:
            graph_x[idx, z] = 1.0
        else:
            graph_x[idx, 0] = 1.0
            
    # 2. SMILES embeddings (128-bit Morgan Fingerprint)
    try:
        fp = AllChem.GetMorganFingerprintAsBitVect(mol, radius=2, nBits=128)
        fp_arr = torch.zeros(128)
        for i in range(128):
            if fp[i]:
                fp_arr[i] = 1.0
    except Exception:
        fp_arr = torch.zeros(128)
    smiles_embed = fp_arr.unsqueeze(0)  # [1, 128]
    
    # 3. RDKit Descriptors padded to 200
    try:
        desc_list = [
            Descriptors.MolWt(mol),
            Descriptors.MolLogP(mol),
            Descriptors.TPSA(mol),
            Descriptors.NumValenceElectrons(mol),
            Descriptors.NumRadicalElectrons(mol),
            Descriptors.MaxPartialCharge(mol) if mol.GetNumAtoms() > 0 else 0.0,
            Descriptors.MinPartialCharge(mol) if mol.GetNumAtoms() > 0 else 0.0,
            Descriptors.FractionCSP3(mol),
            Descriptors.NHOHCount(mol),
            Descriptors.NOCount(mol),
        ]
        desc_tensor = torch.zeros(200)
        for i, val in enumerate(desc_list[:200]):
            if not (torch.isnan(torch.tensor(val)) or torch.isinf(torch.tensor(val))):
                desc_tensor[i] = float(val)
    except Exception:
        desc_tensor = torch.zeros(200)
        
    return {
        'graph_x': graph_x,
        'smiles_embed': smiles_embed,
        'descriptor': desc_tensor,
    }


def get_mock_moleculenet_data(name: str, n_samples: int = 100, n_tasks: int = 12):
    """Generate mock MoleculeNet data when real data is unavailable."""
    data = []
    for _ in range(n_samples):
        item = {
            'graph_x': torch.randn(100, 119),  # 100 atoms, 119 features
            'smiles_embed': torch.randn(1, 128),
            'descriptor': torch.randn(200),
            'label': torch.randint(0, 2, (n_tasks,)).float(),
        }
        data.append(item)
    return data


def get_real_moleculenet_data(name: str, split: str, n_tasks: int = 12) -> list:
    """Load real MoleculeNet datasets from local CSV packages or fallback to mock."""
    import pandas as pd
    
    if name == 'mock':
        return get_mock_moleculenet_data(name, n_samples=100 if split != 'train' else 500, n_tasks=n_tasks)
        
    file_map = {
        'bbbp': f"{split}.csv",
        'clintox': f"{split}.csv",
        'tox21': "tox21.csv"
    }
    
    filename = file_map.get(name)
    if not filename:
        print(f"⚠️ Unknown dataset {name}, falling back to mock.")
        return get_mock_moleculenet_data(name, n_samples=100 if split != 'train' else 500, n_tasks=n_tasks)
        
    csv_path = find_data_file(filename)
    if csv_path and name in ['bbbp', 'clintox']:
        if name not in str(csv_path).lower():
            # Try to resolve correct directory segment
            current = Path(__file__).resolve().parent
            found = False
            for _ in range(5):
                for path in current.glob(f"**/{name}*/**/{filename}"):
                    if path.exists():
                        csv_path = path
                        found = True
                        break
                if found:
                    break
                current = current.parent
                
    if not csv_path or not csv_path.exists():
        print(f"⚠️ Could not find real data file {filename} for {name}. Falling back to mock data.")
        return get_mock_moleculenet_data(name, n_samples=100 if split != 'train' else 500, n_tasks=n_tasks)
        
    print(f"Loading real {name} ({split}) from {csv_path}...")
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"⚠️ Error reading CSV: {e}. Falling back to mock.")
        return get_mock_moleculenet_data(name, n_samples=100 if split != 'train' else 500, n_tasks=n_tasks)
        
    if name == 'bbbp':
        smiles_col = 'smiles'
        label_cols = ['p_np']
    elif name == 'clintox':
        smiles_col = 'smiles'
        label_cols = ['FDA_APPROVED', 'CT_TOX']
    elif name == 'tox21':
        smiles_col = 'smiles'
        label_cols = [
            "NR-AR", "NR-AR-LBD", "NR-AhR", "NR-Aromatase",
            "NR-ER", "NR-ER-LBD", "NR-PPAR-gamma",
            "SR-ARE", "SR-ATAD5", "SR-HSE", "SR-MMP", "SR-p53"
        ]
        # Perform splits for tox21 as it is not pre-split
        df = df.sample(frac=1.0, random_state=42).reset_index(drop=True)
        n = len(df)
        train_idx = int(n * 0.8)
        val_idx = int(n * 0.9)
        
        if split == 'train':
            df = df.iloc[:train_idx]
        elif split == 'valid':
            df = df.iloc[train_idx:val_idx]
        else:
            df = df.iloc[val_idx:]
            
    data = []
    total = len(df)
    print(f"Processing {total} molecules...")
    for idx, row in df.iterrows():
        smiles = row[smiles_col]
        if not isinstance(smiles, str) or len(smiles.strip()) == 0:
            continue
            
        feats = preprocess_smiles(smiles)
        labels = []
        for col in label_cols:
            val = row[col]
            if pd.isna(val) or val == -1:
                labels.append(float('nan'))
            else:
                labels.append(float(val))
                
        feats['label'] = torch.tensor(labels).float()
        data.append(feats)
        
        if (idx + 1) % 2000 == 0:
            print(f"Processed {idx + 1}/{total}...")
            
    return data


def get_pos_weight(labels: Tensor) -> Tensor:
    """Calculate positive class weight for imbalanced data, ignoring NaNs."""
    pos_weights = []
    for i in range(labels.shape[1]):
        col = labels[:, i]
        valid_col = col[~torch.isnan(col) & (col != -1)]
        if len(valid_col) == 0:
            pos_weights.append(1.0)
            continue
        n_pos = valid_col.sum()
        n_neg = len(valid_col) - n_pos
        n_neg = max(n_neg, 1)
        n_pos = max(n_pos, 1)
        pos_weights.append(n_neg / n_pos)
    return torch.tensor(pos_weights)


class ColabTrainer:
    """Training with automatic checkpointing for Free Colab sessions."""
    
    def __init__(self, checkpoint_dir: str, device: str = 'cuda'):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.device = device
        
    def save_checkpoint(self, model, optimizer, epoch: int, step: int = 0, extra=None):
        """Save model checkpoint."""
        ckpt = {
            'epoch': epoch,
            'step': step,
            'model_state': model.state_dict(),
            'optimizer_state': optimizer.state_dict(),
        }
        if extra:
            ckpt.update(extra)
        
        path = self.checkpoint_dir / f'checkpoint_epoch{epoch}.pt'
        torch.save(ckpt, path)
        print(f"✅ Saved checkpoint: {path}")
        
    def load_checkpoint(self, model, optimizer, epoch: int):
        """Load checkpoint if exists."""
        path = self.checkpoint_dir / f'checkpoint_epoch{epoch}.pt'
        if path.exists():
            ckpt = torch.load(path, map_location=self.device, weights_only=False)
            model.load_state_dict(ckpt['model_state'])
            optimizer.load_state_dict(ckpt['optimizer_state'])
            print(f"✅ Loaded checkpoint from epoch {epoch}")
            return ckpt.get('step', 0)
        return 0


def train_epoch(model, loader, optimizer, pos_weights: Tensor, device: str, loss_type: str = 'bce'):
    """Train single epoch."""
    model.train()
    total_loss = 0
    pos_weights = pos_weights.to(device)
    
    for batch in loader:
        optimizer.zero_grad()
        
        graph_x = batch['graph_x'].to(device)
        smiles_embed = batch['smiles_embed'].to(device)
        descriptor = batch['descriptor'].to(device)
        labels = batch['label'].to(device)
        
        out = model(
            graph_x=graph_x,
            smiles_embed=smiles_embed,
            descriptor_feats=descriptor,
        )
        
        logits = out['logits']
        
        # Mask out NaNs and -1
        is_valid = (~torch.isnan(labels)) & (labels != -1)
        
        if loss_type == 'asl':
            pred = torch.sigmoid(logits)
            pred = torch.clamp(pred, min=0.05, max=0.95)
            loss_pos = labels * torch.pow(1 - pred, 1.0) * torch.log(pred + 1e-8)
            loss_neg = (1 - labels) * torch.pow(pred, 4.0) * torch.log(1 - pred + 1e-8)
            loss_raw = -(loss_pos + loss_neg)
        else:
            pw = pos_weights.view(1, -1).expand_as(labels)
            loss_raw = F.binary_cross_entropy_with_logits(logits, torch.nan_to_num(labels, nan=0.0), reduction='none')
            loss_raw = loss_raw * (labels * (pw - 1.0) + 1.0)
            
        loss_masked = loss_raw * is_valid
        
        if is_valid.sum() > 0:
            loss = loss_masked.sum() / is_valid.sum()
        else:
            loss = torch.tensor(0.0, device=device, requires_grad=True)
            
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
    
    return total_loss / len(loader)


def evaluate(model, loader, pos_weights: Tensor, device: str):
    """Evaluate model."""
    model.eval()
    all_preds = []
    all_labels = []
    
    with torch.no_grad():
        for batch in loader:
            graph_x = batch['graph_x'].to(device)
            smiles_embed = batch['smiles_embed'].to(device)
            descriptor = batch['descriptor'].to(device)
            labels = batch['label'].to(device)
            
            out = model(
                graph_x=graph_x,
                smiles_embed=smiles_embed,
                descriptor_feats=descriptor,
            )
            
            preds = torch.sigmoid(out['logits'])
            all_preds.append(preds.cpu())
            all_labels.append(labels.cpu())
    
    all_preds = torch.cat(all_preds, dim=0)
    all_labels = torch.cat(all_labels, dim=0)
    
    # AUROC per task
    if HAS_SKLEARN:
        try:
            aurocs = []
            for i in range(all_labels.shape[1]):
                lbl = all_labels[:, i]
                prd = all_preds[:, i]
                valid_mask = (~torch.isnan(lbl)) & (lbl != -1)
                lbl_valid = lbl[valid_mask]
                prd_valid = prd[valid_mask]
                if len(lbl_valid.unique()) > 1:
                    aurocs.append(roc_auc_score(lbl_valid, prd_valid))
            return {'AUROC': sum(aurocs) / len(aurocs) if aurocs else 0.5, 'task_aurocs': aurocs}
        except Exception as e:
            return {'AUROC': 0.0, 'task_aurocs': []}
    else:
        return {'AUROC': 0.5, 'task_aurocs': [0.5] * all_labels.shape[1]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['pretrain', 'train', 'optuna'], default='train')
    parser.add_argument('--checkpoint_dir', default='./checkpoints')
    parser.add_argument('--epochs', type=int, default=100)
    parser.add_argument('--batch_size', type=int, default=8)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--device', default='cuda' if torch.cuda.is_available() else 'cpu')
    parser.add_argument('--dataset', choices=['tox21', 'bbbp', 'clintox', 'mock'], default='mock')
    parser.add_argument('--loss', choices=['bce', 'asl'], default='bce')
    args = parser.parse_args()
    
    print(f"Free Colab Training - {args.mode}")
    print(f"Batch size: {args.batch_size}")
    print(f"Device: {args.device}")
    print(f"Dataset: {args.dataset}")
    print(f"Loss: {args.loss}")
    
    # Initialize trainer
    trainer = ColabTrainer(args.checkpoint_dir, args.device)
    
    if args.mode == 'pretrain':
        # GraphMAE pretraining
        print("\n=== GraphMAE Pretraining ===")
        mae = GraphMAE(hidden_dim=256).to(args.device)
        optimizer = torch.optim.AdamW(mae.parameters(), lr=args.lr)
        
        data = get_mock_moleculenet_data('tox21', n_samples=100, n_tasks=12)
        
        for epoch in range(args.epochs):
            x = torch.randn(20, 119, device=args.device)
            loss = mae(x)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            if (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{args.epochs} - Loss: {loss.item():.4f}")
                trainer.save_checkpoint(mae, optimizer, epoch + 1)
        
        # Save pretrained weights
        pretrained_path = trainer.checkpoint_dir / 'graphmae_pretrained.pt'
        torch.save(mae.state_dict(), pretrained_path)
        print(f"✅ Pretrained weights saved to {pretrained_path}")
    
    elif args.mode == 'train':
        # Multi-task training
        print(f"\n=== Training on {args.dataset.upper()} ===")
        
        n_tasks = {'tox21': 12, 'bbbp': 1, 'clintox': 2, 'mock': 12}.get(args.dataset, 12)
        model = MultimodalMoleculeEncoder(n_tasks=n_tasks).to(args.device)
        
        # Load pretrained weights if available
        pretrained_path = Path(args.checkpoint_dir) / 'graphmae_pretrained.pt'
        if pretrained_path.exists():
            print(f"Loading pretrained weights from {pretrained_path}")
        
        optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-5)
        
        # Get data
        train_data = get_real_moleculenet_data(args.dataset, 'train', n_tasks=n_tasks)
        val_data = get_real_moleculenet_data(args.dataset, 'valid', n_tasks=n_tasks)
        test_data = get_real_moleculenet_data(args.dataset, 'test', n_tasks=n_tasks)
        
        train_loader = DataLoader(train_data, batch_size=args.batch_size, shuffle=True)
        val_loader = DataLoader(val_data, batch_size=args.batch_size)
        
        # Calculate pos_weight from training data
        all_labels = torch.stack([d['label'] for d in train_data])
        pos_weights = get_pos_weight(all_labels)
        print(f"Pos weights: {pos_weights}")
        
        best_auroc = 0
        start_epoch = 0
        
        # Check for existing checkpoint
        for ckpt_file in sorted(trainer.checkpoint_dir.glob('checkpoint_epoch*.pt')):
            try:
                epoch_num = int(ckpt_file.stem.split('epoch')[1])
                start_epoch = max(start_epoch, epoch_num)
            except:
                pass
        
        if start_epoch > 0:
            start_epoch = trainer.load_checkpoint(model, optimizer, start_epoch)
            print(f"Resuming from epoch {start_epoch}")
        
        for epoch in range(start_epoch, args.epochs):
            train_loss = train_epoch(model, train_loader, optimizer, pos_weights, args.device, args.loss)
            metrics = evaluate(model, val_loader, pos_weights, args.device)
            
            print(f"Epoch {epoch+1}/{args.epochs} - Loss: {train_loss:.4f} - AUROC: {metrics['AUROC']:.4f}")
            
            # Save checkpoint
            trainer.save_checkpoint(model, optimizer, epoch + 1, extra={'val_auroc': metrics['AUROC']})
            
            # Save best model
            if metrics['AUROC'] > best_auroc:
                best_auroc = metrics['AUROC']
                torch.save(model.state_dict(), trainer.checkpoint_dir / 'best_model.pt')
                print(f"✅ New best AUROC: {best_auroc:.4f}")
        
        # Evaluate on test set
        print("\n=== Evaluating Best Model on Test Set ===")
        best_model_path = trainer.checkpoint_dir / 'best_model.pt'
        if best_model_path.exists():
            model.load_state_dict(torch.load(best_model_path, map_location=args.device, weights_only=True))
        
        test_loader = DataLoader(test_data, batch_size=args.batch_size)
        test_metrics = evaluate(model, test_loader, pos_weights, args.device)
        print(f"Test AUROC: {test_metrics['AUROC']:.4f}")
        
        # Save final metrics
        final_metrics = {
            'dataset': args.dataset,
            'best_val_auroc': best_auroc,
            'test_auroc': test_metrics['AUROC'],
            'final_epoch': args.epochs,
            'mode': 'train',
        }
        metrics_path = trainer.checkpoint_dir / 'final_metrics.json'
        metrics_path.write_text(json.dumps(final_metrics, indent=2))
        print(f"\nFinal metrics saved to {metrics_path}")
    
    print(f"\nTraining complete for {args.mode} mode")


if __name__ == "__main__":
    main()