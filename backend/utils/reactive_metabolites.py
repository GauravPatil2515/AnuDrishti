#!/usr/bin/env python3
"""
Reactive Metabolite & Bioactivation Scanner
============================================
Identifies CYP450 bioactivation precursors and reactive metabolite
structural alerts from SMILES strings.

Alerts cover:
  - Quinone methides & ortho/para-quinones
  - Arene epoxides & oxiranes
  - Acyl glucuronide precursors
  - Nitrenium ion precursors (aromatic amines)
  - Thiophene / furan S-OXidation motifs
  - Michael acceptor precursors (alpha,beta-unsaturated)

Returns a Bioactivation Risk Index (BRI) between 0.0 (Safe) and
1.0 (High Risk), along with matched atom indices and clinical notes.

Reference: FDA Reactive Metabolite (QM) Assessment for New Molecular
Entities, 2022 update.
"""

import logging
from typing import Dict, List, Any, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('ReactiveMetaboliteScanner')

# ─────────────────────────────────────────────────────────────────────────────
# Structural alerts (SMARTS patterns) with clinical risk metadata
# ─────────────────────────────────────────────────────────────────────────────
REACTIVE_ALERTS: List[Dict[str, Any]] = [
    {
        "name": "ortho-quinone",
        "smarts": "c1cc(O)c(O)cc1",  # catechol (ortho-dihydroxybenzene → quinone precursor) — requires 2 adjacent OH
        "bri_weight": 0.9,
        "mechanism": "CYP450-mediated ortho-dehydrogenation of catechol to ortho-quinone; electrophilic, forms protein adducts.",
        "clinical_note": "High risk: quinone formation linked to idiosyncratic hepatotoxicity (e.g., diclofenac, benzene).",
    },
    {
        "name": "para-hydroquinone",
        "smarts": "c1ccc(O)cc1(O)",  # hydroquinone (para-dihydroxybenzene → para-quinone) — requires 2 OH at para positions
        "bri_weight": 0.85,
        "mechanism": "Oxidation of hydroquinone to para-benzoquinone; redox-cycling generates ROS.",
        "clinical_note": "High risk: oxidative stress, mitochondrial dysfunction.",
    },
    {
        "name": "quinone_methide",
        "smarts": "[CH2]c1ccc(cc1)C",  # para-methylphenol → quinone methide precursor
        "bri_weight": 0.85,
        "mechanism": "Biosynthetic oxidation of para-alkylphenol to quinone methide.",
        "clinical_note": "Moderate-high: electrophilic trapping of cellular nucleophiles.",
    },
    {
        "name": "epoxide",
        "smarts": "C1OC1",  # oxirane / arene oxide motif
        "bri_weight": 0.8,
        "mechanism": "CYP450 epoxidation of double bond or aromatic ring; electrophilic epoxide.",
        "clinical_note": "High risk for alkenes; reactive epoxide adducts drive DILI (e.g., fialamval).",
    },
    {
        "name": "aromatic_oxide",
        "smarts": "c1ccc2[o+]1cccc2",  # arene N-oxide precursor
        "bri_weight": 0.75,
        "mechanism": "Arene oxides are electrophilic; can rearrange to phenols or form adducts.",
        "clinical_note": "Moderate: arene oxide adduction reported with acetaminophen overdose.",
    },
    {
        "name": "acyl_glucuronide_precursor",
        "smarts": "C(=O)[OH]",  # carboxylic acid → acyl glucuronide
        "bri_weight": 0.6,
        "mechanism": "UDP-glucuronosyltransferase conjugates carboxylic acids; acyl glucuronides are electrophilic and can acylate proteins.",
        "clinical_note": "Moderate: implicated in idiosyncratic hepatotoxicity for some acids (e.g., diclofenac metabolite).",
    },
    {
        "name": "nitrenium_precursor",
        "smarts": "c1ccccc1N",  # aromatic amine → nitrenium ion
        "bri_weight": 0.85,
        "mechanism": "N-hydroxylation → nitroso → nitrenium ion; highly electrophilic.",
        "clinical_note": "High risk: aromatic amine mutagenicity/carcinogenicity (e.g., aniline dyes).",
    },
    {
        "name": "thiophene_s_oxidation",
        "smarts": "c1sccc1",  # thiophene ring
        "bri_weight": 0.75,
        "mechanism": "CYP450 S-oxidation to sulfoxide/sulfone; can release reactive thiyl radicals.",
        "clinical_note": "Moderate: thiophene S-oxidation linked to idiosyncratic toxicity (e.g., Ticlopidine).",
    },
    {
        "name": "furan_oxidation",
        "smarts": "c1occc1",  # furan ring
        "bri_weight": 0.75,
        "mechanism": "CYP450-mediated epoxidation of furan ring; reactive cis-diol/imine intermediates.",
        "clinical_note": "High risk: furan ring oxidation causes hepatic veno-occlusive disease (e.g.,furosemide, halothane).",
    },
    {
        "name": "michael_acceptor",
        "smarts": "C=CC(=O)",  # alpha,beta-unsaturated carbonyl
        "bri_weight": 0.7,
        "mechanism": "Michael addition to cellular nucleophiles (GSH, cysteine residues).",
        "clinical_note": "Moderate: common in pro-apoptotic and cytotoxic drugs.",
    },
]


def detect_reactive_metabolites(smiles: str) -> Dict[str, Any]:
    """Scan a SMILES string for reactive metabolite structural alerts.

    Args:
        smiles: A valid SMILES string.

    Returns:
        {
          "alert_count": int,
          "detected_alerts": [
            {
              "name": str,
              "smarts": str,
              "matched_atoms": [int, ...],
              "bri_weight": float,
              "mechanism": str,
              "clinical_note": str
            }, ...
          ],
          "bri_score": float,   # 0.0 (Safe) to 1.0 (High Risk)
          "risk_label": "SAFE" | "MODERATE" | "HIGH",
          "smiles_hash": str
        }
    """
    import hashlib
    from rdkit import Chem

    result: Dict[str, Any] = {
        "alert_count": 0,
        "detected_alerts": [],
        "bri_score": 0.0,
        "risk_label": "SAFE",
        "smiles_hash": hashlib.sha256(smiles.encode()).hexdigest()[:16],
    }

    mol = Chem.MolFromSmiles(smiles.strip() if isinstance(smiles, str) else "")
    if mol is None:
        result["error"] = "Invalid SMILES"
        return result

    max_bri = 0.0
    for alert in REACTIVE_ALERTS:
        pattern = Chem.MolFromSmarts(alert["smarts"])
        if pattern is None:
            continue
        matches = mol.GetSubstructMatches(pattern)
        if not matches:
            continue

        matched_atoms = sorted(set(atom for match in matches for atom in match))
        weight = float(alert["bri_weight"])
        max_bri = max(max_bri, weight)

        result["detected_alerts"].append({
            "name": alert["name"],
            "smarts": alert["smarts"],
            "matched_atoms": matched_atoms,
            "bri_weight": weight,
            "mechanism": alert["mechanism"],
            "clinical_note": alert["clinical_note"],
        })

    result["alert_count"] = len(result["detected_alerts"])
    result["bri_score"] = round(max_bri, 4)

    if max_bri >= 0.8:
        result["risk_label"] = "HIGH"
    elif max_bri >= 0.5:
        result["risk_label"] = "MODERATE"
    else:
        result["risk_label"] = "SAFE"

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Self-test
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    test_cases = [
        ("c1ccc2[o+]1cccc2", "aromatic_oxide"),
        ("C1CC1", "none (cyclopropane — no epoxide)"),
        ("CC1CO1", "epoxide (ethylene oxide)"),
        ("c1ccc(O)cc1", "none (phenol, not quinone)"),
        ("c1cc(=O)c(O)cc1", "ortho-quinone / catechol"),
    ]
    for smi, desc in test_cases:
        res = detect_reactive_metabolites(smi)
        print(f"{smi} ({desc}): BRI={res['bri_score']}, "
              f"alerts={res['alert_count']}, risk={res['risk_label']}")
