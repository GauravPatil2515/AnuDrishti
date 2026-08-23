#!/usr/bin/env python3
"""
Species Translation Engine
==========================
Phase 3 - Regulatory & Clinical Safety Layer

Cross-species in-silico to in-vivo translation using New Approach
Methodologies (NAMs) per FDA Modernization Act 2.0/3.0.

Two-stage model:
  Stage 1: Acute Oral Toxicity (LD50)
    - Estimates Rat and Mouse LD50 (mg/kg) from structural descriptors using
      an EXPERIMENTAL rule-based fragment model - NOT a validated QSAR.
      Treat output as a hypothesis generator; see Track 3 plan to replace
      with ProTox-3.0 / trained ML models before any regulatory use.
    - Maps to EPA/GHS Toxicity Categories
  Stage 2: Allometric Pharmacokinetic Scaling
    - Extrapolates in vitro intrinsic clearance to in vivo clearance
      for 5 species: Human, Rat, Beagle Dog, Cynomolgus Monkey, Mouse
    - Uses standard physiological exponent scaling (Y = a * W^b)
    - Computes Human Equivalent Dose (HED) and NOAEL safety margins

Species database (standard regulatory species):
  | Species        | Common Name     | BW (kg) |
  |----------------|-----------------|---------|
  | Human          | Homo sapiens    | 70.0    |
  | Rat            | R. norvegicus   | 0.25    |
  | Mouse          | M. musculus     | 0.03    |
  | Dog            | Canis familiaris| 10.0    |
  | Monkey         | Macaca fasc.    | 3.0     |

References:
  - FDA. "Draft Guidance on Use of In Vitro-Derived tissue Models..."
  - EPA. "Ecological Effects Test Guidelines OPPTS 850.1300"
  - FDA Modernization Act 2.0 / 3.0 (2022, 2024)
  - FDA. "Obesity and Weight-Associated Diseases." (HED scaling guidance)
"""

import hashlib
import logging
from typing import Dict, Any, List, Optional

import numpy as np
from rdkit import Chem
from rdkit.Chem import Descriptors, rdMolDescriptors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('SpeciesTranslation')

# ───────────────────────────────────────────────────────────────────────────
# Version lock - bump when scaling coefficients or LD50 model changes
# ───────────────────────────────────────────────────────────────────────────
TRANSLATION_RULESET_VERSION = "v3.0.0"

# ───────────────────────────────────────────────────────────────────────────
# Species database - standard regulatory toxicology species with body weights
# Reference: FDA, EPA, and ICH harmonized tripartite guidelines
# ───────────────────────────────────────────────────────────────────────────
SPECIES_DB = {
    "human": {"common": "Human", "scientific": "Homo sapiens", "bw_kg": 70.0,
              "cl_exponent": 0.75, "vd_exponent": 1.0, "unit": "L/hr"},
    "rat": {"common": "Rat", "scientific": "Rattus norvegicus", "bw_kg": 0.25,
            "cl_exponent": 0.75, "vd_exponent": 1.0, "unit": "mL/min/kg"},
    "mouse": {"common": "Mouse", "scientific": "Mus musculus", "bw_kg": 0.03,
              "cl_exponent": 0.75, "vd_exponent": 1.0, "unit": "mL/min/kg"},
    "dog": {"common": "Beagle Dog", "scientific": "Canis familiaris", "bw_kg": 10.0,
            "cl_exponent": 0.75, "vd_exponent": 1.0, "unit": "mL/min/kg"},
    "monkey": {"common": "Cynomolgus Monkey", "scientific": "Macaca fascicularis", "bw_kg": 3.0,
               "cl_exponent": 0.75, "vd_exponent": 1.0, "unit": "mL/min/kg"},
}

# ───────────────────────────────────────────────────────────────────────────
# GHS / EPA Acute Toxicity Categories (oral LD50, mg/kg)
# Reference: EPA OPPTS 850.1300, OECD TG 401
# ──────────────────────────────────────────────────────────────────────────
GHS_CATEGORIES = [
    {"category": "I", "range": (0, 50), "label": "Fatal / Toxicity Category 1", "color": "RED"},
    {"category": "II", "range": (50, 500), "label": "Toxicity Category 2", "color": "ORANGE"},
    {"category": "III", "range": (500, 5000), "label": "Toxicity Category 3", "color": "YELLOW"},
    {"category": "IV", "range": (5000, float("inf")), "label": "Toxicity Category 4", "color": "GREEN"},
]


def _classify_ghs(ld50: float) -> Dict[str, Any]:
    """Map an LD50 value to GHS/EPA toxicity category."""
    for cat in GHS_CATEGORIES:
        if cat["range"][0] <= ld50 < cat["range"][1]:
            return {"category": cat["category"], "label": cat["label"], "color": cat["color"]}
    return {"category": "IV", "label": "Toxicity Category 4", "color": "GREEN"}


# ───────────────────────────────────────────────────────────────────────────
# LD50 prediction — ProTox-3.0 primary, rule-based fallback
# ───────────────────────────────────────────────────────────────────────────
# Primary: ProTox-3.0 (Banerjee et al., NAR 2024) — similarity-based ML model,
# queried via services/protox_client.py.
# Fallback: the EXPERIMENTAL rule-based fragment model below (UNVALIDATED),
# used only when the ProTox-3.0 service is unreachable/parse-failing.
# ───────────────────────────────────────────────────────────────────────────
# Fragment contributions to log(LD50) (mg/kg) — EXPERIMENTAL rule-based estimates.
# DISCLAIMER: These weights are APPROXIMATE and NOT calibrated against published
# data. Used only as a last-resort fallback. DO NOT use for regulatory
# submissions. See Track 3 for ProTox-3.0 integration to replace this.
_FRAG_CONTRIB = {
    "C": 0.002,    # alkyl C
    "c": 0.015,    # aromatic C (higher toxicity risk)
    "N": 0.025,    # amine N (basic amines increase toxicity)
    "O": 0.010,    # oxygen
    "Cl": 0.150,   # chlorine (halogenation increases toxicity)
    "Br": 0.250,   # bromine
    "F": 0.100,    # fluorine
    "S": 0.080,    # sulfur
    "P": 0.120,    # phosphorus
    "n": 0.020,    # aromatic N
    "N+": 0.300,   # charged amine (e.g., quaternary ammonium)
    "[N+]": 0.300, # charged amine
}

# Species-specific LD50 scaling factors (relative to rat)
# Mouse is typically 2-3x more sensitive than rat for many compounds
_SPECIES_LD50_ADJUST = {
    "rat": 1.0,
    "mouse": 1.2,    # mouse LD50 is typically ~1.2x rat (slightly more sensitive)
}


def _predict_ld50_rule_based(smiles: str) -> Optional[float]:
    """Rule-based LD50 (mg/kg) fallback for rat — UNVALIDATED hypothesis generator.

    log(LD50) = base + sum(fragment_contributions) - f(mol_weight, logP, TPSA)

    Returns the rat LD50 in mg/kg (or None if unparseable). Used ONLY when the
    ProTox-3.0 service is unavailable.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    mw = float(Descriptors.MolWt(mol))
    logp = float(Descriptors.MolLogP(mol))
    tpsa = float(Descriptors.TPSA(mol))
    n_heavy = mol.GetNumHeavyAtoms()

    # Base log LD50 (reference: ~2000 mg/kg median)
    log_ld50 = 3.3

    # Fragment contributions
    frag_sum = 0.0
    for atom in mol.GetAtoms():
        sym = atom.GetSymbol()
        charge = atom.GetFormalCharge()
        if sym == "N" and charge > 0:
            frag_sum += _FRAG_CONTRIB.get("N+", 0.300)
        else:
            frag_sum += _FRAG_CONTRIB.get(sym, 0.010)

    # Normalize by heavy atom count (per-atom average)
    frag_norm = frag_sum / n_heavy if n_heavy > 0 else 0.0

    # Physicochemical corrections
    # High MW → lower bioavailability → higher LD50 (less toxic per mg)
    mw_penalty = max(0, (mw - 200) * 0.0002)
    # High logP → more lipophilic → higher tissue penetration → lower LD50 (more toxic)
    logp_factor = logp * -0.05
    # High TPSA → lower membrane permeability → higher LD50
    tpsa_factor = max(0, (tpsa - 60) * 0.002)

    log_ld50 = log_ld50 + frag_norm + mw_penalty + logp_factor - tpsa_factor
    base_ld50 = 10 ** log_ld50
    rat_ld50 = round(max(5, min(50000, base_ld50 / _SPECIES_LD50_ADJUST["rat"])), 2)
    return rat_ld50


def _predict_ld50(smiles: str) -> Dict[str, Any]:
    """Predict rat/mouse LD50 (mg/kg) + GHS categories, primary = ProTox-3.0.

    Primary source: ProTox-3.0 (Banerjee et al., NAR 2024), a similarity-based
    ML model queried via services/protox_client.py. Mouse LD50 is derived from
    the rat LD50 using the standard mouse/rat sensitivity ratio from
    _SPECIES_LD50_ADJUST (documented, not a separate model).

    If the ProTox-3.0 service is unavailable, parse-failing, or rate-limited,
    falls back to the UNVALIDATED rule-based fragment model below — and the
    result is tagged ``rule_based_fallback`` with low confidence.
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"error": "Cannot parse SMILES for LD50 prediction"}

    protox_result: Optional[Dict[str, Any]] = None
    try:
        from services.protox_client import predict_ld50_protox3
        protox_result = predict_ld50_protox3(smiles)
    except Exception as e:
        print(f"⚠️ ProTox-3.0 import/query failed: {e}")

    source = "ProTox-3.0-fallback"
    confidence = "low"
    confidence_note = (
        "ProTox-3.0 unavailable; using UNVALIDATED rule-based fragment model."
    )
    rat_ld50 = _predict_ld50_rule_based(smiles)

    if (protox_result and protox_result.get("ld50_mg_per_kg") is not None
            and protox_result.get("source", "").startswith("ProTox-3.0")):
        rat_ld50 = round(float(protox_result["ld50_mg_per_kg"]), 2)
        source = protox_result["source"]
        confidence = protox_result.get("confidence", "low")
        confidence_note = protox_result.get("confidence_note", confidence_note)

    if rat_ld50 is None:
        return {"error": "LD50 estimation failed for SMILES"}

    # Mouse extrapolation from rat (documented ratio; ProTox does not provide
    # mouse LD50). Mouse is typically ~1.2x more sensitive => lower LD50.
    mouse_factor = _SPECIES_LD50_ADJUST.get("mouse", 1.2) / _SPECIES_LD50_ADJUST.get("rat", 1.0)
    mouse_ld50 = round(max(5, min(50000, rat_ld50 / mouse_factor)), 2)

    return {
        "rat_ld50_mg_per_kg": rat_ld50,
        "mouse_ld50_mg_per_kg": mouse_ld50,
        "rat_ghs_category": _classify_ghs(rat_ld50),
        "mouse_ghs_category": _classify_ghs(mouse_ld50),
        "ld50_source": source,
        "ld50_confidence": confidence,
        "ld50_confidence_note": confidence_note,
        "ld50_note": ("Hypothesis generator only (ProTox-3.0 similarity ML); "
                      "validate before any regulatory reliance."),
    }


# ───────────────────────────────────────────────────────────────────────────
# Allometric scaling constants
# Reference: FDA guidance "Exponent-Based Scaling in Toxicology"
# Y = a * W^b  where W = body weight (kg)
# ───────────────────────────────────────────────────────────────────────────
_ALLOMETRIC_PARAMS = {
    "clearance": {"a": 0.08, "b": 0.75},       # CL (mL/min) ∝ W^0.75 (Kleiber's law)
    "volume_distribution": {"a": 0.5, "b": 1.0},  # Vd (L) ∝ W^1.0
    "cardiac_output": {"a": 0.2, "b": 0.75},    # CO (L/min) ∝ W^0.75
}


def _allometric_scale(prop: str, bw_kg: float, a: float = None, b: float = None) -> float:
    """Compute allometric scaling Y = a * W^b."""
    params = _ALLOMETRIC_PARAMS.get(prop, {})
    a = a if a is not None else params.get("a", 1.0)
    b = b if b is not None else params.get("b", 0.75)
    return a * (bw_kg ** b)


def _predict_clearance(mol: Chem.Mol, smiles: str) -> Dict[str, float]:
    """Predict in vitro intrinsic clearance, then scale to in vivo for each species.

    Returns per-species CL_int (mL/min/kg) using allometric scaling.
    CL/kg ∝ BW^(b-1) = BW^(-0.25) for b=0.75 (Kleiber's law), so smaller
    species have higher clearance per kg.
    """
    mw = float(Descriptors.MolWt(mol))
    logp = float(Descriptors.MolLogP(mol))
    tpsa = float(Descriptors.TPSA(mol))

    # Base intrinsic clearance for human (mL/min/kg) - rule-based estimate
    base_cl = 15.0  # mL/min/kg reference for 70kg human
    logp_factor = 1.0 + (logp - 2.5) * 0.15   # logP 2.5 = neutral
    tpsa_factor = 1.0 - max(0, tpsa - 80) * 0.005  # TPSA > 80 reduces CL
    mw_factor = 1.0 - max(0, mw - 300) * 0.0005  # MW > 300 reduces CL

    human_cl = base_cl * logp_factor * tpsa_factor * mw_factor
    human_cl = max(1.0, min(200.0, human_cl))

    # Allometric scaling: CL_species = CL_human * (BW_species / BW_human)^(b-1)
    # Since CL is per-kg, the exponent is (b - 1) = -0.25
    # Smaller animals → higher CL/kg
    human_bw = SPECIES_DB["human"]["bw_kg"]
    exponent = SPECIES_DB["human"]["cl_exponent"] - 1.0  # -0.25

    results = {}
    for sp_key, sp in SPECIES_DB.items():
        bw = sp["bw_kg"]
        scale_factor = (bw / human_bw) ** exponent
        if sp_key == "human":
            cl = human_cl
        else:
            cl = human_cl * scale_factor
        results[sp_key] = round(cl, 4)

    return results


def _predict_vd(mol: Chem.Mol) -> Dict[str, float]:
    """Predict volume of distribution per species via allometric scaling.

    Vd (L) ∝ W^1.0 (linear with body weight)
    Adjusted by lipophilicity (logP) and polarity (TPSA).
    """
    logp = float(Descriptors.MolLogP(mol))
    tpsa = float(Descriptors.TPSA(mol))

    # Base Vd fraction: moderate lipophilicity increases Vd
    vd_frac = 0.3 + logp * 0.05 - tpsa * 0.002
    vd_frac = max(0.05, min(1.5, vd_frac))

    results = {}
    for sp_key, sp in SPECIES_DB.items():
        bw = sp["bw_kg"]
        # Vd ∝ BW^1.0
        vd = vd_frac * bw
        results[sp_key] = round(vd, 4)

    return results


def _model_hash(smiles: str) -> str:
    """Deterministic SHA-256 hash for traceability."""
    raw = f"SpeciesTranslation-{TRANSLATION_RULESET_VERSION}-{smiles}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class SpeciesTranslationEngine:
    """Cross-species in-silico to in-vivo translation engine (SCREENING GRADE).

    Implements:
    1. Rule-based acute oral toxicity (LD50) estimation for Rat and Mouse
       - UNVALIDATED, hypothesis generator only
    2. Allometric PK scaling (clearance, Vd) across 5 species from a
       rule-estimated human clearance anchor (not measured IVIVE input)
    3. Screening-level Human Equivalent Dose (HED) calculation
    4. Margin of Safety (MOS) and NOAEL safety margin computation
    5. Honest NAMs statement with explicit limitations (NOT a regulatory
       justification document)

    A versioned model hash is included for traceability; traceability alone
    does not make this module 21 CFR Part 11 compliant.
    """

    def __init__(self):
        self.ruleset_version = TRANSLATION_RULESET_VERSION
        self.species_db = SPECIES_DB
        self.q_hat = {"ld50": 0.25, "clearance": 0.30}

    def translate_molecule(self, smiles: str, human_clearance: Optional[float] = None,
                           dose_mg: Optional[float] = None) -> Dict[str, Any]:
        """Full cross-species translation for a single SMILES.

        Args:
            smiles: Molecule SMILES string
            human_clearance: Optional human in vitro intrinsic clearance (mL/min/10^6 cells)
            dose_mg: Optional human dose (mg) for HED/MOS calculation

        Returns structured dict with LD50, allometric clearance, HED, MOS, NAMs.
        """
        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return {"error": "Invalid SMILES string", "smiles": smiles}

        # Stage 1: LD50 prediction
        ld50_result = _predict_ld50(smiles)

        # Stage 2: Allometric scaling
        cl_results = _predict_clearance(mol, smiles)
        vd_results = _predict_vd(mol)

        # If user provided human clearance, use it as anchor for human
        if human_clearance is not None and human_clearance > 0:
            human_bw = SPECIES_DB["human"]["bw_kg"]
            exponent = SPECIES_DB["human"]["cl_exponent"] - 1.0  # -0.25
            cl_results["human"] = round(human_clearance, 4)
            for sp_key in cl_results:
                if sp_key == "human":
                    continue
                bw = SPECIES_DB[sp_key]["bw_kg"]
                scale_factor = (bw / human_bw) ** exponent
                cl_results[sp_key] = round(human_clearance * scale_factor, 4)

        # Compute HED / Safety Margins if dose_mg provided
        # HED: Human Equivalent Dose - converts animal dose to human equivalent
        # using allometric scaling: HED_mg = Animal_dose_mg * (BW_animal/BW_human)^0.33
        # Here dose_mg is the human dose; we compute the animal-equivalent dose
        # and then the NOAEL/MOS.
        hed = None
        noael = None
        mos = None
        if dose_mg is not None and dose_mg > 0:
            rat_bw = SPECIES_DB["rat"]["bw_kg"]
            human_bw = SPECIES_DB["human"]["bw_kg"]
            # Animal-equivalent dose (mg/kg) for rat
            human_dose_per_kg = dose_mg / human_bw
            rat_dose_per_kg = human_dose_per_kg * (human_bw / rat_bw) ** 0.33
            # NOAEL (mg/kg) = 10x rat dose (standard safety factor for animal→human)
            noael_per_kg = rat_dose_per_kg * 10
            noael = round(noael_per_kg * human_bw, 2)
            # HED (mg) = NOAEL_rat * (BW_rat/BW_human)^0.33 * BW_human
            hed = round(noael_per_kg * (rat_bw / human_bw) ** 0.33 * human_bw, 2)
            mos = round(noael / max(hed, 0.01), 2)

        # Generate NAMs justification (FDA Modernization Act 2.0/3.0)
        nams_statement = self._generate_nams_justification(smiles, ld50_result, cl_results)

        return {
            "success": True,
            "engine": "SpeciesTranslation",
            "ruleset_version": self.ruleset_version,
            "smiles": smiles,
            "molecular_weight": round(float(Descriptors.MolWt(mol)), 4),
            "logp": round(float(Descriptors.MolLogP(mol)), 4),
            "tpsa": round(float(Descriptors.TPSA(mol)), 4),
            "ld50": ld50_result,
            "clearance_ml_per_min_per_kg": cl_results,
            "volume_of_distribution_l": vd_results,
            "species_checked": list(SPECIES_DB.keys()),
            "human_clearance_provided": human_clearance,
            "hed_mg": hed,
            "noael_mg": noael,
            "margin_of_safety": mos,
            "pk_scaling_method": "simple_allometry",
            "pk_disclaimer": (
                "Allometric scaling (b=0.75, Kleiber's law) from rule-estimated human CL. "
                "This is a starting hypothesis only. FDA recommends IVIVE (in vitro clearance "
                "from microsomal assays) for regulatory submissions. Typical accuracy: 2-3 fold."
            ),
            "hed_calculation": "FDA Guidance: HED = NOAEL_animal x (BW_animal/BW_human)^0.33",
            "nams_justification": nams_statement,
            "model_hash": _model_hash(smiles),
        }

    @staticmethod
    def _generate_nams_justification(smiles: str, ld50_result: Dict, cl_results: Dict) -> str:
        """Generate an honest NAMs (New Approach Methodologies) statement.

        This paragraph describes what was done AND its limitations. It must
        NOT be pasted into a regulatory submission as-is: the LD50 model is
        an unvalidated rule-based estimator and human clearance is
        rule-estimated rather than measured in vitro.
        """
        mol = Chem.MolFromSmiles(smiles)
        mw = round(float(Descriptors.MolWt(mol)), 1) if mol else 0
        logp = round(float(Descriptors.MolLogP(mol)), 2) if mol else 0
        rat_ld50 = ld50_result.get("rat_ld50_mg_per_kg", "N/A")
        rat_cat = ld50_result.get("rat_ghs_category", {}).get("category", "N/A")
        human_cl = cl_results.get("human", "N/A")

        return (
            f"This assessment used New Approach Methodologies (NAMs) in the spirit "
            f"of the FDA Modernization Act 2.0/3.0 (H.R.4381, 2024) for the in-silico "
            f"toxicokinetic screening of the test article (MW={mw} g/mol, logP={logp}). "
            f"IMPORTANT LIMITATIONS - READ BEFORE RELYING ON THESE OUTPUTS: "
            f"(1) The acute oral toxicity estimate is produced by an UNVALIDATED "
            f"rule-based fragment model, not a validated QSAR; it is a hypothesis "
            f"generator only and must not be used for regulatory submissions. It "
            f"suggests a Rat LD50 of {rat_ld50} mg/kg (GHS Category {rat_cat}) and a "
            f"Mouse LD50 of {ld50_result.get('mouse_ld50_mg_per_kg', 'N/A')} mg/kg, "
            f"which should be confirmed with a validated model (e.g., ProTox-3.0) or "
            f"in vivo data. (2) Allometric pharmacokinetic scaling (Y = a * W^0.75, "
            f"Kleiber's law) is a standard cross-species extrapolation, but the "
            f"clearance anchor here is RULE-ESTIMATED from logP/MW/TPSA rather than "
            f"derived from in vitro microsomal clearance (IVIVE); typical accuracy of "
            f"such estimates is 2-3 fold at best. Human CL used: {human_cl} mL/min/kg. "
            f"(3) HED/NOAEL/Margin-of-Safety outputs inherit both limitations and are "
            f"screening-level estimates only. For regulatory use, replace with "
            f"experimentally derived CLint (IVIVE), validated QSAR toxicity models, "
            f"and documented applicability-domain checks. No animals were used in "
            f"this assessment."
        )


# ───────────────────────────────────────────────────────────────────────────
# Module-level singleton (consistent with project patterns)
# ──────────────────────────────────────────────────────────────────────────
_DEFAULT_ENGINE: Optional["SpeciesTranslationEngine"] = None


def get_default_translation_engine() -> "SpeciesTranslationEngine":
    """Return a module-level singleton SpeciesTranslationEngine (lazy init)."""
    global _DEFAULT_ENGINE
    if _DEFAULT_ENGINE is None:
        _DEFAULT_ENGINE = SpeciesTranslationEngine()
    return _DEFAULT_ENGINE
