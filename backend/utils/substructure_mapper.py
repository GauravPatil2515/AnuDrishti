#!/usr/bin/env python3
"""
Substructure Mapper: Maps Attention Weights to Chemical Substructures
======================================================================
Converts GNN attention weights into human-interpretable chemical explanations.
Identifies toxic sub-structures and functional groups based on learned importance.

Paper: DeNovo-XAI: Interpretable Molecular Toxicity Prediction
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors, Draw
    from rdkit.Chem.Draw import rdMolDraw2D
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    print("⚠️ RDKit not available - substructure mapping disabled")


@dataclass
class SubstructureMatch:
    """Represents a matched toxic substructure."""
    name: str
    smarts: str
    atoms: List[int]
    avg_attention: float
    max_attention: float
    toxicity_category: str
    mechanism: str


# ═══════════════════════════════════════════════════════════════════════════
# Known Toxicophore Database
# ═══════════════════════════════════════════════════════════════════════════
TOXICOPHORES = {
    # ─────────────────────────────────────────────────────────────────────
    # Reactive Groups (Electrophiles)
    # ─────────────────────────────────────────────────────────────────────
    'nitro': {
        'smarts': '[N+](=O)[O-]',
        'category': 'Reactive',
        'mechanism': 'Nitro groups undergo enzymatic reduction to reactive nitroso intermediates that can form DNA adducts and cause oxidative stress.'
    },
    'nitroso': {
        'smarts': '[N]=O',
        'category': 'Reactive',
        'mechanism': 'Nitroso compounds are direct-acting mutagens that form DNA adducts, particularly at guanine residues.'
    },
    'epoxide': {
        'smarts': 'C1OC1',
        'category': 'Reactive',
        'mechanism': 'Epoxides are electrophilic and can alkylate DNA, proteins, and other macromolecules, leading to mutagenicity.'
    },
    'aldehyde': {
        'smarts': '[CH]=O',
        'category': 'Reactive',
        'mechanism': 'Aldehydes form Schiff bases with amino groups in proteins and DNA, causing cross-linking and dysfunction.'
    },
    'michael_acceptor': {
        'smarts': 'C=CC=O',
        'category': 'Reactive',
        'mechanism': 'Michael acceptors undergo nucleophilic addition with cellular thiols (glutathione, cysteine residues), depleting antioxidant defenses.'
    },
    'acyl_halide': {
        'smarts': 'C(=O)[Cl,Br,I,F]',
        'category': 'Reactive',
        'mechanism': 'Acyl halides are highly reactive electrophiles that acylate proteins and nucleic acids.'
    },
    'isocyanate': {
        'smarts': 'N=C=O',
        'category': 'Reactive',
        'mechanism': 'Isocyanates react with amino and thiol groups, causing respiratory sensitization and protein modification.'
    },
    
    # ─────────────────────────────────────────────────────────────────────
    # Aromatic Systems
    # ─────────────────────────────────────────────────────────────────────
    'polycyclic_aromatic': {
        'smarts': 'c1ccc2c(c1)cccc2',  # Naphthalene core
        'category': 'Carcinogenic',
        'mechanism': 'Polycyclic aromatic hydrocarbons are metabolized to diol-epoxides that intercalate DNA and form mutagenic adducts.'
    },
    'nitroaromatic': {
        'smarts': 'c[N+](=O)[O-]',
        'category': 'Mutagenic',
        'mechanism': 'Nitroaromatics undergo nitroreduction to form reactive hydroxylamines that cause DNA damage.'
    },
    'aminoaromatic': {
        'smarts': 'c-[NH2]',
        'category': 'Carcinogenic',
        'mechanism': 'Aromatic amines are metabolically activated to N-hydroxy derivatives that form DNA adducts.'
    },
    'halogenated_aromatic': {
        'smarts': 'c[Cl,Br,I]',
        'category': 'Persistent',
        'mechanism': 'Halogenated aromatics are resistant to metabolism, bioaccumulate, and can disrupt endocrine signaling.'
    },
    'quinone': {
        'smarts': 'O=C1C=CC(=O)C=C1',
        'category': 'Oxidative',
        'mechanism': 'Quinones undergo redox cycling, generating reactive oxygen species and causing oxidative DNA damage.'
    },
    
    # ─────────────────────────────────────────────────────────────────────
    # Nitrogen-Containing Groups
    # ─────────────────────────────────────────────────────────────────────
    'hydrazine': {
        'smarts': 'NN',
        'category': 'Hepatotoxic',
        'mechanism': 'Hydrazines are metabolized to reactive diazonium ions that alkylate DNA and cause liver damage.'
    },
    'azo': {
        'smarts': 'N=N',
        'category': 'Carcinogenic',
        'mechanism': 'Azo compounds are reduced by gut bacteria to aromatic amines, which are then metabolically activated.'
    },
    'azide': {
        'smarts': '[N-]=[N+]=N',
        'category': 'Cytotoxic',
        'mechanism': 'Azides inhibit cytochrome c oxidase, blocking cellular respiration and ATP production.'
    },
    'n_oxide': {
        'smarts': '[N+][O-]',
        'category': 'Mutagenic',
        'mechanism': 'N-oxides can directly alkylate DNA or generate reactive intermediates upon reduction.'
    },
    'triazene': {
        'smarts': 'N=NN',
        'category': 'Alkylating',
        'mechanism': 'Triazenes decompose to generate methylating species that cause DNA strand breaks.'
    },
    
    # ─────────────────────────────────────────────────────────────────────
    # Sulfur-Containing Groups
    # ─────────────────────────────────────────────────────────────────────
    'thiol': {
        'smarts': '[SH]',
        'category': 'Reactive',
        'mechanism': 'Free thiols can form disulfide bonds with protein cysteines, disrupting enzyme function.'
    },
    'disulfide': {
        'smarts': 'SS',
        'category': 'Reactive',
        'mechanism': 'Disulfides undergo thiol-disulfide exchange, potentially inactivating critical enzymes.'
    },
    'sulfite': {
        'smarts': 'S(=O)(=O)[O-]',
        'category': 'Reactive',
        'mechanism': 'Sulfites generate sulfite radicals that damage DNA and cause respiratory irritation.'
    },
    'thiocarbonyl': {
        'smarts': 'C=S',
        'category': 'Reactive',
        'mechanism': 'Thiocarbonyls are metabolized to reactive sulfur species that modify cellular proteins.'
    },
    
    # ─────────────────────────────────────────────────────────────────────
    # Halogen-Containing Groups  
    # ─────────────────────────────────────────────────────────────────────
    'alkyl_halide': {
        'smarts': 'C[Cl,Br,I]',
        'category': 'Alkylating',
        'mechanism': 'Alkyl halides are direct-acting alkylating agents that modify DNA bases.'
    },
    'trifluoromethyl': {
        'smarts': 'C(F)(F)F',
        'category': 'Metabolic',
        'mechanism': 'Trifluoromethyl groups alter drug metabolism and can generate toxic fluoride upon defluorination.'
    },
    
    # ─────────────────────────────────────────────────────────────────────
    # Phosphorus Groups
    # ─────────────────────────────────────────────────────────────────────
    'phosphate_ester': {
        'smarts': 'OP(=O)(O)O',
        'category': 'Neurotoxic',
        'mechanism': 'Organophosphates inhibit acetylcholinesterase, causing cholinergic crisis.'
    },
    
    # ─────────────────────────────────────────────────────────────────────
    # Ring Systems
    # ─────────────────────────────────────────────────────────────────────
    'furan': {
        'smarts': 'c1ccoc1',
        'category': 'Hepatotoxic',
        'mechanism': 'Furans are metabolized by CYP450 to reactive cis-enedial intermediates that cause liver necrosis.'
    },
    'thiophene': {
        'smarts': 'c1ccsc1',
        'category': 'Reactive',
        'mechanism': 'Thiophenes can form reactive sulfoxide metabolites that bind to liver proteins.'
    },
    'pyridine': {
        'smarts': 'c1ccncc1',
        'category': 'Variable',
        'mechanism': 'Pyridine nitrogen can be N-oxidized or participate in binding interactions.'
    },
    'imidazole': {
        'smarts': 'c1cnc[nH]1',
        'category': 'CYP_Inhibitor',
        'mechanism': 'Imidazoles coordinate with heme iron in CYP450 enzymes, causing drug-drug interactions.'
    },
}


class SubstructureMapper:
    """
    Maps GNN attention weights to chemically meaningful substructures.
    Provides human-interpretable explanations for toxicity predictions.
    """
    
    def __init__(self, custom_toxicophores: Optional[Dict] = None):
        """
        Initialize mapper with toxicophore database.
        
        Args:
            custom_toxicophores: Optional additional patterns to include
        """
        if not RDKIT_AVAILABLE:
            raise ImportError("RDKit is required for substructure mapping")
        
        self.toxicophores = TOXICOPHORES.copy()
        if custom_toxicophores:
            self.toxicophores.update(custom_toxicophores)
        
        # Pre-compile SMARTS patterns
        self._compiled_patterns = {}
        for name, info in self.toxicophores.items():
            pattern = Chem.MolFromSmarts(info['smarts'])
            if pattern is not None:
                self._compiled_patterns[name] = pattern
    
    def identify_substructures(
        self, 
        smiles: str,
        attention_weights: np.ndarray,
        threshold: float = 0.1
    ) -> List[SubstructureMatch]:
        """
        Identify toxic substructures based on attention weights.
        
        Args:
            smiles: SMILES string of molecule
            attention_weights: Per-atom attention scores from GNN
            threshold: Minimum average attention to report substructure
            
        Returns:
            List of SubstructureMatch objects sorted by importance
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []
        
        # Add hydrogens to match GNN processing
        mol = Chem.AddHs(mol)
        
        matches = []
        
        for name, pattern in self._compiled_patterns.items():
            # Find all occurrences of this pattern
            all_matches = mol.GetSubstructMatches(pattern)
            
            for match_atoms in all_matches:
                # Get attention scores for these atoms
                valid_atoms = [a for a in match_atoms if a < len(attention_weights)]
                if not valid_atoms:
                    continue
                
                atom_scores = attention_weights[valid_atoms]
                avg_attention = float(np.mean(atom_scores))
                max_attention = float(np.max(atom_scores))
                
                # Only include if attention is above threshold
                if avg_attention >= threshold:
                    info = self.toxicophores[name]
                    matches.append(SubstructureMatch(
                        name=name,
                        smarts=info['smarts'],
                        atoms=list(match_atoms),
                        avg_attention=avg_attention,
                        max_attention=max_attention,
                        toxicity_category=info['category'],
                        mechanism=info['mechanism']
                    ))
        
        # Sort by average attention (most important first)
        matches.sort(key=lambda x: x.avg_attention, reverse=True)
        
        return matches
    
    def get_top_atoms(
        self,
        smiles: str,
        attention_weights: np.ndarray,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Get the top-k most important atoms with chemical context.
        
        Args:
            smiles: SMILES string
            attention_weights: Per-atom attention scores
            top_k: Number of top atoms to return
            
        Returns:
            List of dicts with atom info and attention score
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []
        
        mol = Chem.AddHs(mol)
        
        # Get top-k indices
        k = min(top_k, len(attention_weights), mol.GetNumAtoms())
        top_indices = np.argsort(attention_weights)[-k:][::-1]
        
        results = []
        for idx in top_indices:
            if idx >= mol.GetNumAtoms():
                continue
            
            atom = mol.GetAtomWithIdx(int(idx))
            
            # Get atom context
            neighbors = [mol.GetAtomWithIdx(n.GetIdx()).GetSymbol() 
                        for n in atom.GetNeighbors()]
            
            results.append({
                'index': int(idx),
                'symbol': atom.GetSymbol(),
                'atomic_num': atom.GetAtomicNum(),
                'attention': float(attention_weights[idx]),
                'hybridization': str(atom.GetHybridization()),
                'is_aromatic': atom.GetIsAromatic(),
                'neighbors': neighbors,
                'degree': atom.GetDegree()
            })
        
        return results
    
    def generate_explanation(
        self,
        smiles: str,
        attention_weights: np.ndarray,
        prediction_prob: float,
        top_k_substructures: int = 3,
        top_k_atoms: int = 5
    ) -> Dict:
        """
        Generate a comprehensive explanation for a toxicity prediction.
        
        Args:
            smiles: SMILES string
            attention_weights: Per-atom attention scores
            prediction_prob: Predicted toxicity probability
            top_k_substructures: Number of substructures to report
            top_k_atoms: Number of individual atoms to report
            
        Returns:
            Dict containing structured explanation data
        """
        # Get matched substructures
        substructures = self.identify_substructures(smiles, attention_weights)[:top_k_substructures]
        
        # Get top atoms
        top_atoms = self.get_top_atoms(smiles, attention_weights, top_k_atoms)
        
        # Determine risk level
        if prediction_prob > 0.7:
            risk_level = "HIGH"
            risk_description = "Strong toxic signal detected"
        elif prediction_prob > 0.4:
            risk_level = "MODERATE"
            risk_description = "Moderate toxicity concerns"
        else:
            risk_level = "LOW"
            risk_description = "Low toxicity prediction"
        
        # Build explanation
        explanation = {
            'smiles': smiles,
            'prediction_probability': prediction_prob,
            'risk_level': risk_level,
            'risk_description': risk_description,
            
            # Substructure-based explanation
            'identified_toxicophores': [
                {
                    'name': s.name.replace('_', ' ').title(),
                    'category': s.toxicity_category,
                    'importance': round(s.avg_attention * 100, 1),
                    'mechanism': s.mechanism,
                    'atom_indices': s.atoms
                }
                for s in substructures
            ],
            
            # Atom-level explanation
            'critical_atoms': [
                {
                    'position': a['index'],
                    'element': a['symbol'],
                    'importance': round(a['attention'] * 100, 1),
                    'context': f"{a['symbol']} bonded to {', '.join(a['neighbors']) if a['neighbors'] else 'nothing'}",
                    'aromatic': a['is_aromatic']
                }
                for a in top_atoms
            ],
            
            # Summary for LLM
            'summary_for_llm': self._create_llm_summary(
                smiles, prediction_prob, substructures, top_atoms
            )
        }
        
        return explanation
    
    def _create_llm_summary(
        self,
        smiles: str,
        prediction_prob: float,
        substructures: List[SubstructureMatch],
        top_atoms: List[Dict]
    ) -> str:
        """Create a concise summary for LLM processing."""
        lines = []
        lines.append(f"Molecule: {smiles}")
        lines.append(f"Predicted Toxicity: {prediction_prob:.1%}")
        
        if substructures:
            lines.append("\nIdentified Toxic Substructures:")
            for s in substructures:
                lines.append(f"  - {s.name.replace('_', ' ').title()} "
                           f"(importance: {s.avg_attention:.1%}, "
                           f"category: {s.toxicity_category})")
        
        if top_atoms:
            lines.append("\nMost Important Atoms:")
            for a in top_atoms[:3]:
                lines.append(f"  - {a['symbol']} at position {a['index']} "
                           f"(importance: {a['attention']:.1%})")
        
        return "\n".join(lines)
    
    def visualize_attention(
        self,
        smiles: str,
        attention_weights: np.ndarray,
        output_path: Optional[str] = None,
        size: Tuple[int, int] = (400, 300)
    ):
        """
        Generate molecule image with attention highlighting.
        
        Args:
            smiles: SMILES string
            attention_weights: Per-atom attention scores
            output_path: Optional path to save image
            size: Image size (width, height)
            
        Returns:
            PIL Image or saves to file
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        # Normalize attention weights to [0, 1] for coloring
        weights = np.array(attention_weights[:mol.GetNumAtoms()])
        weights = (weights - weights.min()) / (weights.max() - weights.min() + 1e-8)
        
        # Create atom colors (red = high attention, blue = low)
        atom_colors = {}
        for i, w in enumerate(weights):
            # RGB: interpolate from blue (0,0,1) to red (1,0,0)
            atom_colors[i] = (w, 0, 1 - w)
        
        # Generate 2D coords
        AllChem.Compute2DCoords(mol)
        
        # Draw molecule
        drawer = rdMolDraw2D.MolDraw2DCairo(size[0], size[1])
        drawer.DrawMolecule(mol, highlightAtoms=list(range(mol.GetNumAtoms())),
                           highlightAtomColors=atom_colors)
        drawer.FinishDrawing()
        
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(drawer.GetDrawingText())
            return output_path
        else:
            return drawer.GetDrawingText()


# ═══════════════════════════════════════════════════════════════════════════
# Test Code
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Testing Substructure Mapper...")
    print("=" * 60)
    
    mapper = SubstructureMapper()
    
    # Test with a molecule containing known toxicophores
    # Nitrobenzene - contains nitro group
    smiles = "c1ccc(cc1)[N+](=O)[O-]"
    
    # Simulate attention weights (higher for nitro group atoms)
    mol = Chem.MolFromSmiles(smiles)
    mol = Chem.AddHs(mol)
    n_atoms = mol.GetNumAtoms()
    
    # Create fake attention (high for atoms 6,7,8 which are the nitro group)
    attention = np.random.uniform(0.02, 0.1, n_atoms)
    attention[6:9] = np.array([0.35, 0.25, 0.20])  # Nitro group
    attention = attention / attention.sum()  # Normalize
    
    print(f"Test molecule: Nitrobenzene ({smiles})")
    print(f"Number of atoms: {n_atoms}")
    print(f"Attention range: {attention.min():.3f} - {attention.max():.3f}")
    
    # Identify substructures
    matches = mapper.identify_substructures(smiles, attention, threshold=0.05)
    print(f"\n✅ Found {len(matches)} matching toxicophores:")
    for m in matches:
        print(f"   - {m.name}: atoms {m.atoms}, "
              f"attention={m.avg_attention:.1%}, "
              f"category={m.toxicity_category}")
    
    # Generate full explanation
    explanation = mapper.generate_explanation(smiles, attention, 0.85)
    print(f"\n✅ Generated explanation:")
    print(f"   Risk level: {explanation['risk_level']}")
    print(f"   Toxicophores found: {len(explanation['identified_toxicophores'])}")
    print(f"\n   LLM Summary:")
    print(explanation['summary_for_llm'])
    
    print("\n✅ Substructure Mapper ready!")
