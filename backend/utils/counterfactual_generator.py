#!/usr/bin/env python3
"""
Counterfactual Molecule Generator
==================================
Generates chemically valid molecular modifications for faithfulness testing.
Creates minimal perturbations to test causal relationships between structure and toxicity.

Paper: From Plausible to Faithful: Causally-Constrained LLM Explanations
       for Molecular Toxicity Prediction

Author: DeNovo-XAI Research Team
"""

import logging
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum

try:
    from rdkit import Chem
    from rdkit.Chem import AllChem, Descriptors, rdMolDescriptors, QED
    from rdkit.Chem import ReplaceSubstructs, DeleteSubstructs
    from rdkit.Contrib.SA_Score import sascorer
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False
    print("⚠️ RDKit not available - counterfactual generation disabled")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('CounterfactualGenerator')


class ModificationType(Enum):
    """Types of molecular modifications."""
    REMOVE_TOXICOPHORE = "remove_toxicophore"
    ADD_TOXICOPHORE = "add_toxicophore"
    SWAP_FUNCTIONAL_GROUP = "swap_functional_group"
    SATURATE_RING = "saturate_ring"
    HALOGENATE = "halogenate"
    DEHALOGENATE = "dehalogenate"
    BIOISOSTERIC = "bioisosteric"
    SCAFFOLD_ALTER = "scaffold_alter"


class ExpectedEffect(Enum):
    """Expected effect on toxicity."""
    INCREASE = "increase"
    DECREASE = "decrease"
    NEUTRAL = "neutral"
    UNKNOWN = "unknown"


@dataclass
class CounterfactualMolecule:
    """A counterfactual molecule with expected behavior."""
    original_smiles: str
    modified_smiles: str
    modification_type: ModificationType
    modification_description: str
    expected_toxicity_change: ExpectedEffect
    confidence: float  # How confident we are in the expected effect
    atoms_modified: List[int] = None
    qed: Optional[float] = None  # Drug-likeness score (0-1) of the modified molecule
    sa_score: Optional[float] = None  # Synthetic accessibility score (1-10) of the modified molecule


class CounterfactualGenerator:
    """
    Generates counterfactual molecules for faithfulness testing.
    
    Key principle: Minimal modifications that have predictable effects.
    """
    
    # Common functional group replacements
    FUNCTIONAL_GROUP_SWAPS = {
        # (from_smarts, to_smarts, expected_effect, confidence)
        'hydroxyl_to_methoxy': ('[OH]', '[OCH3]', ExpectedEffect.NEUTRAL, 0.7),
        'amine_to_amide': ('[NH2]', 'NC(=O)C', ExpectedEffect.DECREASE, 0.6),
        'nitro_to_amine': ('[N+](=O)[O-]', '[NH2]', ExpectedEffect.DECREASE, 0.9),
        'carbonyl_to_alcohol': ('C=O', 'CO', ExpectedEffect.DECREASE, 0.6),
        'methyl_to_ethyl': ('[CH3]', '[CH2CH3]', ExpectedEffect.NEUTRAL, 0.8),
    }
    
    # Toxicophores to remove (from substructure_mapper)
    REMOVABLE_TOXICOPHORES = {
        'nitro': ('[N+](=O)[O-]', ExpectedEffect.DECREASE, 0.9),
        'epoxide': ('C1OC1', ExpectedEffect.DECREASE, 0.8),
        'aldehyde': ('[CH]=O', ExpectedEffect.DECREASE, 0.7),
        'hydrazine': ('NN', ExpectedEffect.DECREASE, 0.9),
        'halogen': ('[Cl,Br,I]', ExpectedEffect.DECREASE, 0.6),
    }
    
    # Toxicophores to add
    ADDABLE_TOXICOPHORES = {
        'nitro': ('[H]', '[N+](=O)[O-]', ExpectedEffect.INCREASE, 0.8),
        'chloro': ('[H]', 'Cl', ExpectedEffect.INCREASE, 0.6),
        'aldehyde': ('[CH3]', 'C=O', ExpectedEffect.INCREASE, 0.7),
    }

    # Bioisosteric replacements — preserve target activity while modulating
    # toxicity / ADMET. (from_smarts, to_smarts, expected_effect, confidence)
    # These are the clinically established bioisosteres used for "what-if"
    # optimization in Mode C.
    BIOISOSTERES = {
        'nitro_to_trifluoromethyl': ('[N+](=O)[O-]', 'C(F)(F)F',
                                      ExpectedEffect.DECREASE, 0.75),
        'hydroxyl_to_fluorine': ('[OH]', 'F', ExpectedEffect.NEUTRAL, 0.7),
        'carboxylic_acid_to_tetrazole': ('C(=O)[OH]', 'c1nnnn1',
                                         ExpectedEffect.NEUTRAL, 0.65),
        'phenyl_to_pyridyl': ('c1ccccc1', 'c1ccccn1',
                              ExpectedEffect.NEUTRAL, 0.7),
        'ester_to_amide': ('C(=O)O[C]', 'C(=O)N',
                           ExpectedEffect.NEUTRAL, 0.6),
        'sulfide_to_methylene': ('S', 'C', ExpectedEffect.DECREASE, 0.6),
    }

    # Scaffold alterations — ring-size / heteroatom swaps that change the core
    # while keeping the overall pharmacophore. Conservative, validity-checked.
    SCAFFOLD_ALTERATIONS = {
        'benzene_to_pyridine': ('c1ccccc1', 'c1ccccn1', ExpectedEffect.NEUTRAL, 0.6),
        'cyclopentyl_to_cyclohexyl': ('C1CCCC1', 'C1CCCCC1', ExpectedEffect.NEUTRAL, 0.7),
        'thiophene_to_furan': ('c1ccsc1', 'c1ccoc1', ExpectedEffect.NEUTRAL, 0.6),
    }

    def __init__(self):
        if not RDKIT_AVAILABLE:
            raise ImportError("RDKit is required for counterfactual generation")
        
        self.generated_cache = {}  # Cache to avoid duplicates
    
    def generate_counterfactuals(
        self,
        smiles: str,
        n_variants: int = 5,
        modification_types: Optional[List[ModificationType]] = None
    ) -> List[CounterfactualMolecule]:
        """
        Generate multiple counterfactual variants of a molecule.
        
        Args:
            smiles: Original SMILES string
            n_variants: Number of variants to generate
            modification_types: Specific types to try (None = all)
            
        Returns:
            List of CounterfactualMolecule objects
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            logger.error(f"Invalid SMILES: {smiles}")
            return []
        
        counterfactuals = []
        
        # Try each modification type
        if modification_types is None:
            modification_types = list(ModificationType)
        
        for mod_type in modification_types:
            if len(counterfactuals) >= n_variants:
                break
            
            variants = self._apply_modification_type(smiles, mol, mod_type)
            counterfactuals.extend(variants)
        
        # Remove duplicates and limit
        unique_counterfactuals = self._deduplicate(counterfactuals)
        return unique_counterfactuals[:n_variants]
    
    def generate_optimization_candidates(self,
        smiles: str,
        n_variants: int = 6
    ) -> List[CounterfactualMolecule]:
        """Mode C helper: prioritize toxicity-lowering modifications.

        Tries, in order of expected toxicity reduction: remove toxicophores,
        bioisosteric swaps (nitro→CF3 etc.), dehalogenation, then scaffold
        alterations. Returns the unique candidates (caller re-ranks by model
        prediction)."""
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return []
        ordered = [
            ModificationType.REMOVE_TOXICOPHORE,
            ModificationType.BIOISOSTERIC,
            ModificationType.DEHALOGENATE,
            ModificationType.SCAFFOLD_ALTER,
            ModificationType.SATURATE_RING,
        ]
        cfs = []
        for mt in ordered:
            if len(cfs) >= n_variants:
                break
            cfs.extend(self._apply_modification_type(smiles, mol, mt))
        cfs = self._deduplicate(cfs)

        # Attach drug-likeness (QED) and synthetic accessibility (SA) scores to each candidate
        # so the UI can filter for chemically sensible counterfactuals (SIH audit P2 #9).
        # We filter to only keep those with QED > 0.4 and SA Score < 6.0.
        filtered_cfs = []
        for cf in cfs:
            try:
                m = Chem.MolFromSmiles(cf.modified_smiles)
                if m is not None:
                    cf.qed = round(float(QED.qed(m)), 3)
                    cf.sa_score = round(float(sascorer.calculateScore(m)), 2)
                else:
                    cf.qed = None
                    cf.sa_score = None
            except Exception:
                cf.qed = None
                cf.sa_score = None

            # Filter: only keep if QED > 0.4 and SA Score < 6.0
            if cf.qed is not None and cf.sa_score is not None:
                if cf.qed > 0.4 and cf.sa_score < 6.0:
                    filtered_cfs.append(cf)
            # If we cannot compute the scores, we discard the candidate (to be safe).
            # Alternatively, we could keep it and let the UI decide, but the audit says to filter.
            # We'll discard if we cannot compute.

        return filtered_cfs[:n_variants]
    def _apply_modification_type(
        self,
        smiles: str,
        mol: Chem.Mol,
        mod_type: ModificationType
    ) -> List[CounterfactualMolecule]:
        """Apply a specific modification type."""
        
        if mod_type == ModificationType.REMOVE_TOXICOPHORE:
            return self._remove_toxicophores(smiles, mol)
        elif mod_type == ModificationType.ADD_TOXICOPHORE:
            return self._add_toxicophores(smiles, mol)
        elif mod_type == ModificationType.SWAP_FUNCTIONAL_GROUP:
            return self._swap_functional_groups(smiles, mol)
        elif mod_type == ModificationType.SATURATE_RING:
            return self._saturate_aromatic_rings(smiles, mol)
        elif mod_type == ModificationType.DEHALOGENATE:
            return self._dehalogenate(smiles, mol)
        elif mod_type == ModificationType.BIOISOSTERIC:
            return self._bioisosteric_replacement(smiles, mol)
        elif mod_type == ModificationType.SCAFFOLD_ALTER:
            return self._scaffold_alteration(smiles, mol)
        else:
            return []
    
    def _remove_toxicophores(
        self,
        smiles: str,
        mol: Chem.Mol
    ) -> List[CounterfactualMolecule]:
        """Remove known toxicophores from the molecule."""
        counterfactuals = []
        
        for name, (smarts, expected_effect, confidence) in self.REMOVABLE_TOXICOPHORES.items():
            pattern = Chem.MolFromSmarts(smarts)
            if pattern is None:
                continue
            
            if mol.HasSubstructMatch(pattern):
                try:
                    # Replace with hydrogen
                    modified_mol = DeleteSubstructs(mol, pattern)
                    
                    if modified_mol and modified_mol.GetNumAtoms() > 0:
                        modified_smiles = Chem.MolToSmiles(modified_mol)
                        
                        counterfactuals.append(CounterfactualMolecule(
                            original_smiles=smiles,
                            modified_smiles=modified_smiles,
                            modification_type=ModificationType.REMOVE_TOXICOPHORE,
                            modification_description=f"Removed {name} group",
                            expected_toxicity_change=expected_effect,
                            confidence=confidence
                        ))
                except Exception as e:
                    logger.debug(f"Failed to remove {name}: {e}")
        
        return counterfactuals
    
    def _add_toxicophores(
        self,
        smiles: str,
        mol: Chem.Mol
    ) -> List[CounterfactualMolecule]:
        """Add toxicophores to the molecule."""
        counterfactuals = []
        
        # Find aromatic carbons with hydrogen
        for atom in mol.GetAtoms():
            if atom.GetIsAromatic() and atom.GetSymbol() == 'C':
                # Check if it has an H we can replace
                if atom.GetTotalNumHs() > 0:
                    # Try adding nitro group
                    try:
                        # Create editable mol
                        em = Chem.EditableMol(mol)
                        
                        # Add N atom
                        n_idx = em.AddAtom(Chem.Atom(7))  # Nitrogen
                        em.AddBond(atom.GetIdx(), n_idx, Chem.BondType.SINGLE)
                        
                        # Add O atoms
                        o1_idx = em.AddAtom(Chem.Atom(8))
                        o2_idx = em.AddAtom(Chem.Atom(8))
                        em.AddBond(n_idx, o1_idx, Chem.BondType.DOUBLE)
                        em.AddBond(n_idx, o2_idx, Chem.BondType.SINGLE)
                        
                        modified_mol = em.GetMol()
                        Chem.SanitizeMol(modified_mol)
                        
                        modified_smiles = Chem.MolToSmiles(modified_mol)
                        
                        counterfactuals.append(CounterfactualMolecule(
                            original_smiles=smiles,
                            modified_smiles=modified_smiles,
                            modification_type=ModificationType.ADD_TOXICOPHORE,
                            modification_description="Added nitro group to aromatic ring",
                            expected_toxicity_change=ExpectedEffect.INCREASE,
                            confidence=0.8
                        ))
                        
                        break  # Only add one for now
                        
                    except Exception as e:
                        logger.debug(f"Failed to add nitro: {e}")
        
        return counterfactuals
    
    def _swap_functional_groups(
        self,
        smiles: str,
        mol: Chem.Mol
    ) -> List[CounterfactualMolecule]:
        """Swap functional groups with similar ones."""
        counterfactuals = []
        
        for name, (from_smarts, to_smarts, expected_effect, confidence) in self.FUNCTIONAL_GROUP_SWAPS.items():
            from_pattern = Chem.MolFromSmarts(from_smarts)
            to_fragment = Chem.MolFromSmarts(to_smarts)
            
            if from_pattern is None or to_fragment is None:
                continue
            
            if mol.HasSubstructMatch(from_pattern):
                try:
                    modified_mol = AllChem.ReplaceSubstructs(
                        mol, from_pattern, to_fragment, replaceAll=False
                    )[0]
                    
                    Chem.SanitizeMol(modified_mol)
                    modified_smiles = Chem.MolToSmiles(modified_mol)
                    
                    counterfactuals.append(CounterfactualMolecule(
                        original_smiles=smiles,
                        modified_smiles=modified_smiles,
                        modification_type=ModificationType.SWAP_FUNCTIONAL_GROUP,
                        modification_description=f"Swapped functional group: {name}",
                        expected_toxicity_change=expected_effect,
                        confidence=confidence
                    ))
                    
                except Exception as e:
                    logger.debug(f"Failed to swap {name}: {e}")
        
        return counterfactuals
    
    def _saturate_aromatic_rings(
        self,
        smiles: str,
        mol: Chem.Mol
    ) -> List[CounterfactualMolecule]:
        """Convert aromatic rings to saturated rings."""
        counterfactuals = []
        
        # Find aromatic rings
        ring_info = mol.GetRingInfo()
        aromatic_rings = []
        
        for ring in ring_info.AtomRings():
            if all(mol.GetAtomWithIdx(i).GetIsAromatic() for i in ring):
                aromatic_rings.append(ring)
        
        if aromatic_rings:
            try:
                # Hydrogenate the first aromatic ring
                modified_mol = Chem.Mol(mol)
                
                for atom_idx in aromatic_rings[0]:
                    atom = modified_mol.GetAtomWithIdx(atom_idx)
                    atom.SetIsAromatic(False)
                
                # Update bonds
                for bond in modified_mol.GetBonds():
                    if bond.GetBeginAtomIdx() in aromatic_rings[0] and \
                       bond.GetEndAtomIdx() in aromatic_rings[0]:
                        bond.SetIsAromatic(False)
                        if bond.GetBondType() == Chem.BondType.AROMATIC:
                            bond.SetBondType(Chem.BondType.SINGLE)
                
                Chem.SanitizeMol(modified_mol)
                modified_smiles = Chem.MolToSmiles(modified_mol)
                
                counterfactuals.append(CounterfactualMolecule(
                    original_smiles=smiles,
                    modified_smiles=modified_smiles,
                    modification_type=ModificationType.SATURATE_RING,
                    modification_description="Saturated aromatic ring",
                    expected_toxicity_change=ExpectedEffect.DECREASE,
                    confidence=0.6
                ))
                
            except Exception as e:
                logger.debug(f"Failed to saturate ring: {e}")
        
        return counterfactuals
    
    def _dehalogenate(
        self,
        smiles: str,
        mol: Chem.Mol
    ) -> List[CounterfactualMolecule]:
        """Remove halogen atoms."""
        counterfactuals = []
        
        halogen_pattern = Chem.MolFromSmarts('[Cl,Br,I,F]')
        
        if mol.HasSubstructMatch(halogen_pattern):
            try:
                # Replace halogens with H
                h_atom = Chem.MolFromSmarts('[H]')
                modified_mol = AllChem.ReplaceSubstructs(
                    mol, halogen_pattern, h_atom, replaceAll=True
                )[0]
                
                Chem.SanitizeMol(modified_mol)
                modified_smiles = Chem.MolToSmiles(modified_mol)
                
                counterfactuals.append(CounterfactualMolecule(
                    original_smiles=smiles,
                    modified_smiles=modified_smiles,
                    modification_type=ModificationType.DEHALOGENATE,
                    modification_description="Removed halogen atoms",
                    expected_toxicity_change=ExpectedEffect.DECREASE,
                    confidence=0.7
                ))
                
            except Exception as e:
                logger.debug(f"Failed to dehalogenate: {e}")
        
        return counterfactuals
    
    def _bioisosteric_replacement(
        self,
        smiles: str,
        mol: Chem.Mol
    ) -> List[CounterfactualMolecule]:
        """Bioisosteric replacements that preserve activity, modulate safety."""
        counterfactuals = []
        for name, (from_smarts, to_smarts, expected_effect, confidence) in self.BIOISOSTERES.items():
            from_pattern = Chem.MolFromSmarts(from_smarts)
            to_fragment = Chem.MolFromSmarts(to_smarts)
            if from_pattern is None or to_fragment is None:
                continue
            if mol.HasSubstructMatch(from_pattern):
                try:
                    modified_mol = AllChem.ReplaceSubstructs(
                        mol, from_pattern, to_fragment, replaceAll=False
                    )[0]
                    Chem.SanitizeMol(modified_mol)
                    modified_smiles = Chem.MolToSmiles(modified_mol)
                    counterfactuals.append(CounterfactualMolecule(
                        original_smiles=smiles,
                        modified_smiles=modified_smiles,
                        modification_type=ModificationType.BIOISOSTERIC,
                        modification_description=f"Bioisosteric swap: {name}",
                        expected_toxicity_change=expected_effect,
                        confidence=confidence
                    ))
                except Exception as e:
                    logger.debug(f"Failed bioisostere {name}: {e}")
        return counterfactuals

    def _scaffold_alteration(
        self,
        smiles: str,
        mol: Chem.Mol
    ) -> List[CounterfactualMolecule]:
        """Conservative scaffold (core ring) alterations."""
        counterfactuals = []
        for name, (from_smarts, to_smarts, expected_effect, confidence) in self.SCAFFOLD_ALTERATIONS.items():
            from_pattern = Chem.MolFromSmarts(from_smarts)
            to_fragment = Chem.MolFromSmarts(to_smarts)
            if from_pattern is None or to_fragment is None:
                continue
            if mol.HasSubstructMatch(from_pattern):
                try:
                    modified_mol = AllChem.ReplaceSubstructs(
                        mol, from_pattern, to_fragment, replaceAll=False
                    )[0]
                    Chem.SanitizeMol(modified_mol)
                    modified_smiles = Chem.MolToSmiles(modified_mol)
                    counterfactuals.append(CounterfactualMolecule(
                        original_smiles=smiles,
                        modified_smiles=modified_smiles,
                        modification_type=ModificationType.SCAFFOLD_ALTER,
                        modification_description=f"Scaffold alteration: {name}",
                        expected_toxicity_change=expected_effect,
                        confidence=confidence
                    ))
                except Exception as e:
                    logger.debug(f"Failed scaffold alteration {name}: {e}")
        return counterfactuals

    def _deduplicate(
        self,
        counterfactuals: List[CounterfactualMolecule]
    ) -> List[CounterfactualMolecule]:
        """Remove duplicate SMILES."""
        seen = set()
        unique = []
        
        for cf in counterfactuals:
            # Canonicalize SMILES for comparison
            try:
                canonical = Chem.MolToSmiles(Chem.MolFromSmiles(cf.modified_smiles))
                if canonical not in seen and canonical != cf.original_smiles:
                    seen.add(canonical)
                    unique.append(cf)
            except:
                continue
        
        return unique
    
    def generate_for_claimed_toxicophore(
        self,
        smiles: str,
        claimed_toxicophore_smarts: str,
        toxicophore_name: str
    ) -> Optional[CounterfactualMolecule]:
        """
        Generate counterfactual by removing a specific claimed toxicophore.
        This is used for causal consistency testing.
        
        Args:
            smiles: Original molecule
            claimed_toxicophore_smarts: SMARTS pattern of claimed toxic group
            toxicophore_name: Human-readable name
            
        Returns:
            CounterfactualMolecule with the toxicophore removed
        """
        mol = Chem.MolFromSmiles(smiles)
        pattern = Chem.MolFromSmarts(claimed_toxicophore_smarts)
        
        if mol is None or pattern is None:
            return None
        
        if not mol.HasSubstructMatch(pattern):
            logger.warning(f"Molecule doesn't contain claimed toxicophore: {toxicophore_name}")
            return None
        
        try:
            modified_mol = DeleteSubstructs(mol, pattern)
            
            if modified_mol and modified_mol.GetNumAtoms() > 0:
                modified_smiles = Chem.MolToSmiles(modified_mol)
                
                return CounterfactualMolecule(
                    original_smiles=smiles,
                    modified_smiles=modified_smiles,
                    modification_type=ModificationType.REMOVE_TOXICOPHORE,
                    modification_description=f"Removed claimed toxicophore: {toxicophore_name}",
                    expected_toxicity_change=ExpectedEffect.DECREASE,
                    confidence=0.9  # High confidence for claimed features
                )
        except Exception as e:
            logger.error(f"Failed to remove toxicophore {toxicophore_name}: {e}")
        
        return None


# ═══════════════════════════════════════════════════════════════════════════
# Test Code
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Testing Counterfactual Generator...")
    print("=" * 60)
    
    generator = CounterfactualGenerator()
    
    # Test molecule: Nitrobenzene
    smiles = "c1ccc([N+](=O)[O-])cc1"
    print(f"Original: {smiles} (Nitrobenzene)")
    
    counterfactuals = generator.generate_counterfactuals(smiles, n_variants=5)
    
    print(f"\nGenerated {len(counterfactuals)} counterfactuals:")
    for i, cf in enumerate(counterfactuals, 1):
        print(f"\n{i}. {cf.modification_description}")
        print(f"   Modified SMILES: {cf.modified_smiles}")
        print(f"   Expected effect: {cf.expected_toxicity_change.value}")
        print(f"   Confidence: {cf.confidence:.2f}")
    
    # Test specific toxicophore removal
    print("\n" + "=" * 60)
    print("Testing specific toxicophore removal...")
    
    cf = generator.generate_for_claimed_toxicophore(
        smiles,
        '[N+](=O)[O-]',
        'nitro group'
    )
    
    if cf:
        print(f"✅ Successfully removed nitro group")
        print(f"   Original: {cf.original_smiles}")
        print(f"   Modified: {cf.modified_smiles}")
    
    print("\n✅ Counterfactual Generator ready!")
