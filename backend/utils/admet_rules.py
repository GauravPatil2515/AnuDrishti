#!/usr/bin/env python3
"""
ADMET Rule-Based Interpreter
============================
Provides physicochemical property calculations and rule-based overrides
to correct ML model predictions for edge cases.
"""

from rdkit import Chem
from rdkit.Chem import Descriptors, Crippen, Lipinski
from typing import Dict, Any, Optional
import math


def calculate_molecular_properties(smiles: str) -> Optional[Dict[str, Any]]:
    """
    Calculate physicochemical properties using RDKit
    
    Args:
        smiles: SMILES string
        
    Returns:
        Dictionary of molecular properties or None if invalid
    """
    try:
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        
        props = {
            'mw': Descriptors.MolWt(mol),
            'logP': Crippen.MolLogP(mol),
            'tpsa': Descriptors.TPSA(mol),
            'hbd': Lipinski.NumHDonors(mol),
            'hba': Lipinski.NumHAcceptors(mol),
            'rotatable_bonds': Lipinski.NumRotatableBonds(mol),
            'aromatic_rings': Lipinski.NumAromaticRings(mol),
            'num_atoms': mol.GetNumAtoms(),
            'num_heavy_atoms': Lipinski.HeavyAtomCount(mol),
            'is_lipinski_compliant': is_lipinski_compliant(mol)
        }
        
        return props
        
    except Exception as e:
        print(f"⚠️ Property calculation failed: {e}")
        return None


def is_lipinski_compliant(mol) -> bool:
    """Check Lipinski's Rule of Five compliance"""
    mw = Descriptors.MolWt(mol)
    logP = Crippen.MolLogP(mol)
    hbd = Lipinski.NumHDonors(mol)
    hba = Lipinski.NumHAcceptors(mol)
    
    violations = 0
    if mw > 500: violations += 1
    if logP > 5: violations += 1
    if hbd > 5: violations += 1
    if hba > 10: violations += 1
    
    return violations <= 1  # Allow 1 violation


def absorption_rule(mw: float, logP: float, tpsa: float) -> Dict[str, Any]:
    """
    ABSORPTION — Caco-2 / Oral Absorption Rules
    
    Corrects for:
    - Small molecules (diffusion-dominated, bypass membranes)
    - High polarity compounds (poor permeation)
    
    Rule Logic:
    - MW < 150: High absorption (paracellular/diffusion-dominated)
    - TPSA > 140: Low absorption (polarity barrier)
    - Else: Use ML Caco-2 model
    """
    # Small molecules - diffusion-dominated transport
    if mw < 150:
        return {
            "absorption": "High (diffusion-dominated)",
            "mechanism": "Paracellular/passive diffusion",
            "ml_applicable": False,
            "override_reason": "MW < 150 Da: transport bypasses Caco-2 mechanism (transcellular)",
            "confidence": "high",
            "clinical_note": "Rapid, complete absorption expected regardless of Caco-2 value"
        }
    
    # High polarity barrier
    if tpsa > 140:
        return {
            "absorption": "Low (polarity-limited)",
            "mechanism": "Membrane permeation barrier",
            "ml_applicable": True,
            "override_reason": "TPSA > 140 Ų: poor membrane permeability",
            "confidence": "high",
            "clinical_note": "Poor oral bioavailability likely; consider alternative routes"
        }
    
    # ML model domain - drug-like space
    return {
        "absorption": "Use ML Caco-2 prediction",
        "mechanism": "Transcellular transport",
        "ml_applicable": True,
        "override_reason": None,
        "confidence": "high",
        "clinical_note": "ML model reliable for this chemical space"
    }


def distribution_rule(logP: float, tpsa: float, mw: float) -> Dict[str, Any]:
    """
    DISTRIBUTION — BBB Penetration Rules
    
    ⚠️ CRITICAL: BBB penetration is DISTRIBUTION, NOT TOXICITY
    
    High BBB penetration indicates:
    - CNS site-of-action potential
    - NOT inherently dangerous
    
    Rule Logic:
    - TPSA < 90 AND logP > 1.5: High BBB penetration
    - Else: Low BBB penetration
    """
    # High BBB penetration - CNS accessible
    if tpsa < 90 and logP > 1.5:
        return {
            "bbb_penetration": "High",
            "distribution": "CNS + peripheral",
            "ml_applicable": True,
            "override_reason": None,
            "confidence": "high",
            "clinical_note": "CNS site-of-action potential (NOT inherently toxic)",
            "interpretation": "Drug can reach CNS - relevant for neurological targets OR sedation risk"
        }
    
    # Low BBB penetration - peripherally restricted
    return {
        "bbb_penetration": "Low",
        "distribution": "Peripheral only",
        "ml_applicable": True,
        "override_reason": "TPSA ≥ 90 or logP ≤ 1.5: limited BBB crossing",
        "confidence": "high",
        "clinical_note": "Peripherally acting - minimal CNS exposure",
        "interpretation": "Suitable for non-CNS targets; reduced sedation/neurotoxicity risk"
    }


def metabolism_rule(mw: float, logP: float, num_atoms: int) -> Dict[str, Any]:
    """
    METABOLISM — Intrinsic Clearance Rules
    
    ⚠️ CRITICAL: Intrinsic clearance assumes CYP/microsomal metabolism
    
    Non-CYP pathways (ADH, ALDH, esterases) follow different kinetics.
    DO NOT directly compare clearance values across enzyme classes.
    
    Rule Logic:
    - Small molecules (MW < 150): Non-CYP metabolism (ADH/ALDH/esterase)
    - High logP (> 3): CYP-mediated metabolism
    - Hydrophilic (logP < 0): Minimal hepatic metabolism
    """
    # Very small molecules - non-CYP pathways
    if mw < 150 and num_atoms < 10:
        return {
            "metabolism": "High (non-CYP)",
            "pathway": "ADH/ALDH/esterase (capacity-limited)",
            "ml_applicable": False,
            "override_reason": "Small molecule: non-microsomal metabolism pathway",
            "confidence": "high",
            "clinical_note": "Intrinsic clearance values NOT directly comparable (assumes first-order CYP kinetics)",
            "kinetics": "Non-linear, capacity-limited"
        }
    
    # Highly lipophilic - extensive CYP metabolism
    if logP > 3:
        return {
            "metabolism": "Moderate–High (CYP-mediated)",
            "pathway": "Cytochrome P450",
            "ml_applicable": True,
            "override_reason": None,
            "confidence": "moderate",
            "clinical_note": "CYP substrate - watch for drug-drug interactions",
            "kinetics": "First-order, CYP-mediated"
        }
    
    # Hydrophilic - minimal hepatic metabolism
    if logP < 0:
        return {
            "metabolism": "Low (renal elimination)",
            "pathway": "Primarily renal",
            "ml_applicable": False,
            "override_reason": "Hydrophilic: bypasses hepatic metabolism",
            "confidence": "high",
            "clinical_note": "Minimal hepatic extraction - dose adjust in renal impairment",
            "kinetics": "Renal filtration/secretion"
        }
    
    # Standard CYP metabolism
    return {
        "metabolism": "Use ML clearance prediction",
        "pathway": "CYP/microsomal",
        "ml_applicable": True,
        "override_reason": None,
        "confidence": "moderate",
        "kinetics": "First-order"
    }


def excretion_rule(mw: float, logP: float, tpsa: float) -> Dict[str, Any]:
    """
    EXCRETION — Renal vs Hepatic Elimination
    
    Industry-standard rule:
    - MW < 300 AND logP < 1: Renal dominant
    - logP > 3: Hepatic/biliary dominant
    - Else: Mixed elimination
    """
    # Primarily renal (small, hydrophilic)
    if mw < 300 and logP < 1:
        return {
            "excretion": "Renal dominant",
            "route": "Glomerular filtration + tubular secretion",
            "ml_applicable": False,
            "override_reason": "Small hydrophilic molecules: renal clearance predominates",
            "confidence": "high",
            "clinical_note": "Dose adjustment required in renal impairment (CrCl monitoring)"
        }
    
    # Primarily hepatic (lipophilic)
    if logP > 3:
        return {
            "excretion": "Hepatic/biliary dominant",
            "route": "Hepatic metabolism + biliary secretion",
            "ml_applicable": False,
            "override_reason": "Lipophilic molecules: hepatic clearance predominates",
            "confidence": "high",
            "clinical_note": "Dose adjustment required in hepatic impairment (Child-Pugh monitoring)"
        }
    
    # Mixed elimination
    return {
        "excretion": "Mixed renal + hepatic",
        "route": "Both renal and hepatic pathways",
        "ml_applicable": False,
        "override_reason": None,
        "confidence": "moderate",
        "clinical_note": "Both renal and hepatic function affect clearance - dual monitoring"
    }


def toxicity_rule(
    is_approved_drug: bool,
    tox21_score: float,
    bbb_penetration: str,
    mw: float,
    logP: float
) -> Dict[str, Any]:
    """
    TOXICITY — Clinical Risk Assessment
    
    ⚠️ CRITICAL DISTINCTIONS:
    1. Hazard (in vitro signal) ≠ Clinical Risk (dose-dependent)
    2. Approved/food/endogenous = dose-dependent, manageable toxicity
    3. BBB penetration = distribution, NOT toxicity
    
    Rule Logic:
    - Approved/endogenous: Dose-dependent, clinically manageable
    - High Tox21 + High BBB: Elevated CNS exposure potential
    - Else: Use ML classification (with context)
    """
    # FDA-approved or endogenous compounds
    if is_approved_drug:
        return {
            "toxicity_classification": "Dose-dependent, clinically manageable",
            "hazard_detected": tox21_score > 0.5,
            "clinical_risk": "Low at therapeutic doses",
            "ml_applicable": False,
            "override_reason": "Approved drug or endogenous compound - established therapeutic window",
            "confidence": "high",
            "clinical_note": "Known safety profile - toxicity is dose-dependent and manageable",
            "interpretation": "Hazard signals present but clinical use validated (risk-benefit assessed)"
        }
    
    # High CNS exposure potential
    if "High" in bbb_penetration and tox21_score > 0.7:
        return {
            "toxicity_classification": "Elevated CNS exposure potential",
            "hazard_detected": True,
            "clinical_risk": "Moderate (dose-dependent)",
            "ml_applicable": True,
            "override_reason": None,
            "confidence": "moderate",
            "clinical_note": "BBB penetration + toxicity signals indicate CNS site-of-action",
            "interpretation": "Monitor for sedation/drowsiness at high exposure - NOT inherently dangerous"
        }
    
    # Peripheral exposure only
    if "Low" in bbb_penetration and tox21_score > 0.7:
        return {
            "toxicity_classification": "Peripheral hazard signals",
            "hazard_detected": True,
            "clinical_risk": "Moderate (dose-dependent)",
            "ml_applicable": True,
            "override_reason": None,
            "confidence": "moderate",
            "clinical_note": "Toxicity signals present but limited CNS exposure",
            "interpretation": "Monitor hepato/nephrotoxicity - dose-dependent effects"
        }
    
    # Low hazard signals
    if tox21_score < 0.3:
        return {
            "toxicity_classification": "Low hazard signals",
            "hazard_detected": False,
            "clinical_risk": "Low",
            "ml_applicable": True,
            "override_reason": None,
            "confidence": "moderate",
            "clinical_note": "Minimal in vitro toxicity signals detected",
            "interpretation": "Standard safety monitoring recommended - always dose-dependent"
        }
    
    # Default: use ML with context
    return {
        "toxicity_classification": "Moderate hazard signals (dose-dependent)",
        "hazard_detected": tox21_score > 0.5,
        "clinical_risk": "Moderate (exposure-dependent)",
        "ml_applicable": True,
        "override_reason": None,
        "confidence": "moderate",
        "clinical_note": "In vitro hazard signals - clinical risk depends on dose/exposure",
        "interpretation": "Hazard ≠ toxicity. All compounds have dose-dependent effects."
    }


def interpret_admet_predictions(
    smiles: str,
    ml_predictions: Dict[str, Any],
    is_approved_drug: bool = False
) -> Dict[str, Any]:
    """
    Master ADMET Interpreter
    
    Combines ML predictions with rule-based overrides
    
    Args:
        smiles: SMILES string
        ml_predictions: Raw ML model outputs
        is_approved_drug: Whether compound is FDA-approved
        
    Returns:
        Comprehensive ADMET assessment with rules applied
    """
    # Calculate molecular properties
    props = calculate_molecular_properties(smiles)
    
    if props is None:
        return {
            'error': 'Invalid SMILES - could not calculate properties',
            'properties': None,
            'interpretations': {}
        }
    
    # Extract ML predictions
    caco2_ml = ml_predictions.get('caco2', {})
    bbbp_ml = ml_predictions.get('bbbp', {})
    clearance_ml = ml_predictions.get('clearance', {})
    hlm_ml = ml_predictions.get('hlm_clint', {})
    tox21_ml = ml_predictions.get('tox21', {})
    clintox_ml = ml_predictions.get('clintox', {})
    
    # Get toxicity score (average of available)
    tox_scores = []
    if 'probability' in tox21_ml:
        tox_scores.append(tox21_ml['probability'])
    if 'probability' in clintox_ml:
        tox_scores.append(clintox_ml['probability'])
    tox21_score = sum(tox_scores) / len(tox_scores) if tox_scores else 0.5
    
    # Apply rules
    absorption = absorption_rule(props['mw'], props['logP'], props['tpsa'])
    distribution = distribution_rule(props['logP'], props['tpsa'], props['mw'])
    metabolism = metabolism_rule(props['mw'], props['logP'], props['num_atoms'])
    excretion = excretion_rule(props['mw'], props['logP'], props['tpsa'])
    toxicity = toxicity_rule(
        is_approved_drug,
        tox21_score,
        distribution.get('bbb_penetration', 'Unknown'),
        props['mw'],
        props['logP']
    )
    
    # Build comprehensive result
    result = {
        'properties': props,
        'interpretations': {
            'absorption': {
                **absorption,
                'ml_prediction': caco2_ml.get('value', 'N/A') if 'value' in caco2_ml else caco2_ml.get('probability', 'N/A'),
                'ml_prediction_type': caco2_ml.get('type', 'N/A')
            },
            'distribution': {
                **distribution,
                'ml_prediction': bbbp_ml.get('probability', 'N/A'),
                'ml_prediction_label': bbbp_ml.get('label', 'N/A')
            },
            'metabolism': {
                **metabolism,
                'ml_prediction': clearance_ml.get('value', hlm_ml.get('value', 'N/A')),
                'ml_prediction_type': clearance_ml.get('type', hlm_ml.get('type', 'N/A'))
            },
            'excretion': excretion,
            'toxicity': {
                **toxicity,
                'tox21_score': tox21_score,
                'tox21_label': tox21_ml.get('label', 'N/A'),
                'clintox_label': clintox_ml.get('label', 'N/A')
            }
        },
        'lipinski_compliant': props['is_lipinski_compliant'],
        'drug_likeness': assess_drug_likeness(props),
        'summary': generate_admet_summary(absorption, distribution, metabolism, excretion, toxicity, props),
        'layer_separation': {
            'ml_layer': 'Biological hazard detection (in vitro signals)',
            'rule_layer': 'ADMET interpretation + clinical context',
            'note': 'Hazard signals ≠ clinical toxicity. All compounds are dose-dependent.'
        }
    }
    
    return result


def assess_drug_likeness(props: Dict[str, Any]) -> Dict[str, Any]:
    """Assess overall drug-likeness"""
    score = 0
    reasons = []
    
    if props['is_lipinski_compliant']:
        score += 2
        reasons.append("Lipinski compliant")
    else:
        reasons.append("Lipinski violations present")
    
    if 200 <= props['mw'] <= 500:
        score += 1
    elif props['mw'] < 200:
        reasons.append("Low MW (may lack selectivity)")
    else:
        reasons.append("High MW (poor oral absorption)")
    
    if 0 <= props['logP'] <= 5:
        score += 1
    else:
        reasons.append("logP outside optimal range")
    
    if props['tpsa'] < 140:
        score += 1
    else:
        reasons.append("High TPSA (poor permeability)")
    
    if props['rotatable_bonds'] <= 10:
        score += 1
    else:
        reasons.append("High flexibility (poor oral bioavailability)")
    
    # Score interpretation
    if score >= 5:
        likeness = "Excellent"
    elif score >= 3:
        likeness = "Good"
    elif score >= 2:
        likeness = "Fair"
    else:
        likeness = "Poor"
    
    return {
        'score': score,
        'max_score': 6,
        'likeness': likeness,
        'reasons': reasons
    }


def generate_admet_summary(
    absorption: Dict,
    distribution: Dict,
    metabolism: Dict,
    excretion: Dict,
    toxicity: Dict,
    props: Dict
) -> str:
    """Generate human-readable ADMET summary with correct terminology"""
    summary_parts = []
    
    # Absorption
    abs_status = absorption.get('absorption', 'Unknown')
    summary_parts.append(f"**Absorption**: {abs_status}")
    if not absorption.get('ml_applicable', True):
        summary_parts.append(f"  ⚠️ Model limitation: {absorption.get('override_reason', 'N/A')}")
    
    # Distribution (NOT toxicity)
    bbb_status = distribution.get('bbb_penetration', 'Unknown')
    summary_parts.append(f"**Distribution (BBB)**: {bbb_status}")
    summary_parts.append(f"  ℹ️ {distribution.get('interpretation', 'Standard distribution')}")
    
    # Metabolism
    met_status = metabolism.get('metabolism', 'Unknown')
    summary_parts.append(f"**Metabolism**: {met_status}")
    if not metabolism.get('ml_applicable', True):
        summary_parts.append(f"  ⚠️ {metabolism.get('clinical_note', 'N/A')}")
    
    # Excretion
    exc_status = excretion.get('excretion', 'Unknown')
    summary_parts.append(f"**Excretion**: {exc_status}")
    
    # Toxicity (hazard vs clinical risk)
    tox_classification = toxicity.get('toxicity_classification', 'Unknown')
    clinical_risk = toxicity.get('clinical_risk', 'Unknown')
    summary_parts.append(f"**Toxicity**: {tox_classification}")
    summary_parts.append(f"  Clinical Risk: {clinical_risk}")
    if not toxicity.get('ml_applicable', True):
        summary_parts.append(f"  ℹ️ {toxicity.get('override_reason', 'N/A')}")
    summary_parts.append(f"  💡 {toxicity.get('interpretation', 'Dose-dependent effects')}")
    
    return "\n".join(summary_parts)
