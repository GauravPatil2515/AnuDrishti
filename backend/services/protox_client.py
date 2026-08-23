#!/usr/bin/env python3
"""
ProTox-3.0 API Client
=====================
Thin, resilient client for the ProTox-3.0 acute-oral-toxicity (LD50) web service.

Reference:
  Banerjee P., Kemmler E., Dunkel M., Preissner R.:
  "ProTox 3.0: a webserver for the prediction of toxicity of chemicals."
  Nucleic Acids Res (Web server issue) 2024; 52(W1):W59-WW.
  doi:10.1093/nar/gkae303 — https://tox.charite.de/protox3/

API (per ProTox-3.0 FAQ): a simple POST interface that returns CSV. For a
canonical SMILES we submit:
    input=<smiles>
    input-type=smile
    model[]=ld50
and parse the acute-toxicity row (predicted LD50 in mg/kg, GHS toxicity class,
and a similarity-based prediction accuracy in 0-100%).

This client is intentionally defensive: the public server is rate-limited
(250 queries/day/IP, per-compound latency), may be unreachable from a
restricted sandbox, and returns CSV rather than JSON. Any transport, format,
or rate-limit failure raises ``ProToxUnavailable`` (or returns None), so the
caller can transparently fall back to a rule-based hypothesis generator.

GHS toxicity classes (authoritative, NAR 2024 FAQ):
    I   : LD50 <= 5      (fatal)
    II  : 5   < LD50 <= 50
    III : 50  < LD50 <= 300
    IV  : 300 < LD50 <= 2000
    V   : 2000 < LD50 <= 5000
    VI  : LD50 > 5000    (non-toxic)

DISCLAIMER: LD50 predictions are hypothesis generators derived from molecular
similarity to a reference dataset. They are NOT calibrated in-silico-to-in-vivo
equivalence and must NOT be used alone for regulatory submissions. Pair with
read-across, in vitro, and the applicability-domain gate in utils/ood_detector.py.
"""

import hashlib
import logging
import time
from typing import Dict, Any, Optional, Tuple

try:
    import requests  # type: ignore
    REQUESTS_AVAILABLE = True
except ImportError:  # pragma: no cover - requests is a transitive dep of the backend
    REQUESTS_AVAILABLE = False

logger = logging.getLogger('ProToxClient')

PROTOX3_URL = "https://tox.charite.de/protox3/target/result"
DEFAULT_TIMEOUT = 30.0
_MAX_RETRIES = 2

# GHS oral-toxicity class table (NAR 2024 / ProTox-3.0 FAQ)
_GHS_TABLE: Tuple[Tuple[float, str, str], ...] = (
    (5.0,    "I",   "Fatal / Toxicity Category 1"),
    (50.0,   "II",  "Fatal / Toxicity Category 2"),
    (300.0,  "III", "Toxic / Toxicity Category 3"),
    (2000.0, "IV",  "Harmful / Toxicity Category 4"),
    (5000.0, "V",   "May be harmful / Toxicity Category 5"),
    (float("inf"), "VI", "Non-toxic / Toxicity Category 6"),
)


class ProToxUnavailable(Exception):
    """Raised when the ProTox-3.0 service cannot be reached or parsed."""


# ─────────────────────────────────────────────────────────────────────────────
# In-memory cache keyed by canonical SMILES (InChIKey would be ideal, but we
# avoid an extra PubChem round-trip here; RDKit canonical SMILES is a stable key).
# ─────────────────────────────────────────────────────────────────────────────
_CACHE: Dict[str, Dict[str, Any]] = {}


def _cache_key(smiles: str) -> str:
    return hashlib.sha256(smiles.strip().encode("utf-8")).hexdigest()[:16]


def _ghs_from_ld50(ld50: Optional[float]) -> Dict[str, str]:
    """Map an LD50 value (mg/kg) to a GHS category/label."""
    if ld50 is None or ld50 < 0:
        return {"category": "VI", "label": "Non-toxic / Toxicity Category 6",
                "color": "GREEN"}
    for hi, cat, label in _GHS_TABLE:
        if ld50 <= hi:
            color = {"I": "RED", "II": "RED", "III": "ORANGE",
                     "IV": "YELLOW", "V": "YELLOW", "VI": "GREEN"}[cat]
            return {"category": cat, "label": label, "color": color}
    return {"category": "VI", "label": "Non-toxic / Toxicity Category 6",
            "color": "GREEN"}


def predict_ld50_protox3(
    smiles: str,
    timeout: float = DEFAULT_TIMEOUT,
    use_cache: bool = True,
) -> Dict[str, Any]:
    """Query ProTox-3.0 for the acute oral toxicity (LD50) of a SMILES string.

    Returns a dict shaped as::

        {
          "source": "ProTox-3.0 (NAR 2024)",
          "smiles": ...,
          "ld50_mg_per_kg": <float or None>,
          "ghs_class": {"category","label","color"},
          "toxicity_class": <int 1-6 or None>,
          "prediction_accuracy": <float 0-100 or None>,
          "confidence": "high|moderate|low",
          "confidence_note": "...",
          "note": "hypothesis generator; validate before regulatory use"
        }

    On ANY failure (no network, rate limit, parse error, RDKit unavailable for
    canonicalization) this function returns a compact ``error`` dict describing
    the fallback status — it never raises to the caller. The caller (species
    translation engine) should then use its rule-based estimator.
    """
    if not smiles or not isinstance(smiles, str):
        return {"source": "ProTox-3.0-fallback", "error": "empty SMILES",
                "confidence": "low"}

    try:
        from rdkit import Chem
        can = Chem.MolToSmiles(Chem.MolFromSmiles(smiles.strip()))
        if not can:
            return {"source": "ProTox-3.0-fallback", "error": "unparseable SMILES",
                    "confidence": "low"}
        smiles = can
    except Exception:
        smiles = smiles.strip()

    key = _cache_key(smiles)
    if use_cache and key in _CACHE:
        cached = dict(_CACHE[key])
        cached["cached"] = True
        return cached

    if not REQUESTS_AVAILABLE:
        return _fallback(smiles, "requests library not installed")

    payload = {
        "input": smiles,
        "input-type": "smile",
        "model[]": "ld50",
    }
    last_err: Optional[str] = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            resp = requests.post(
                PROTOX3_URL,
                data=payload,
                headers={"Accept": "text/csv,text/plain;q=0.9,*/*;q=0.8",
                         "User-Agent": "AnuDrishti-PharmaGuard-API/1.0"},
                timeout=timeout,
            )
            if not resp.ok:
                last_err = f"HTTP {resp.status_code}"
                # 429 = rate limited; brief backoff then one more try.
                if resp.status_code == 429 and attempt < _MAX_RETRIES:
                    time.sleep(1.0 * attempt)
                    continue
                break
            parsed = _parse_protox_csv(resp.text)
            if parsed is None:
                last_err = "CSV parse: no LD50 row returned"
                break

            ld50, tox_class, accuracy = parsed
            ghs = _ghs_from_ld50(ld50)
            result = {
                "source": "ProTox-3.0 (NAR 2024)",
                "smiles": smiles,
                "ld50_mg_per_kg": ld50,
                "ghs_class": ghs,
                "toxicity_class": tox_class,
                "prediction_accuracy": accuracy,
                "confidence": "moderate" if (accuracy or 0) >= 70 else "low",
                "confidence_note": (
                    "Source: ProTox-3.0 similarity-based ML model. Confidence "
                    "derived from reference-set similarity (NAR 2024). Not a "
                    "calibrated in-silico-to-in-vivo equivalence."
                ),
                "note": ("Hypothesis generator only; validate with read-across "
                         "and in vitro before any regulatory reliance."),
            }
            if use_cache:
                _CACHE[key] = {k: v for k, v in result.items()
                               if k not in ("cached",)}
            return result
        except requests.exceptions.Timeout:
            last_err = "request timeout"
            continue
        except Exception as e:  # network / parse any other failure
            last_err = str(e)
            break

    return _fallback(smiles, last_err or "unknown error")


def _fallback(smiles: str, reason: str) -> Dict[str, Any]:
    """Standard fallback record when ProTox-3.0 is unavailable."""
    return {
        "source": "ProTox-3.0-fallback",
        "smiles": smiles,
        "ld50_mg_per_kg": None,
        "ghs_class": _ghs_from_ld50(None),
        "toxicity_class": None,
        "prediction_accuracy": None,
        "confidence": "low",
        "confidence_note": (
            f"ProTox-3.0 service unavailable ({reason}). Falling back to the "
            "rule-based LD50 estimator — low confidence, hypothesis generator only."
        ),
        "note": ("Hypothesis generator only; validate with read-across and in "
                 "vitro before any regulatory reliance."),
    }


def _parse_protox_csv(text: str) -> Optional[Tuple[float, Optional[int], Optional[float]]]:
    """Extract (ld50, toxicity_class, accuracy%) from the ProTox-3.0 CSV.

    The ProTox-3.0 API (per NAR 2024 / FAQ) returns a column-oriented CSV:

        input,type,Target,Prediction,Probability
        CCO,acute_tox,LD50,1000,95.00
        CCO,acute_tox,tox_class,4,95.00

    where ``Target`` is either ``LD50`` or ``tox_class``, ``Prediction`` holds
    the value (mg/kg or class 1-6), and ``Probability`` is the similarity-based
    accuracy in %. We collect the LD50 row, the tox_class row, and the paired
    accuracy. Returns None if no LD50 row is present.
    """
    if not text:
        return None
    import csv as _csv
    reader = _csv.reader(text.splitlines())
    rows = [r for r in reader if any(c.strip() for c in r)]
    if not rows:
        return None

    header = [h.strip().lower() for h in rows[0]]
    ld50 = tox_class = accuracy = None
    idx_target = idx_pred = idx_prob = None
    for i, h in enumerate(header):
        if h == "target":
            idx_target = i
        elif h == "prediction":
            idx_pred = i
        elif h == "probability":
            idx_prob = i

    has_header = idx_target is not None and idx_pred is not None
    start = 1 if has_header else 0
    for row in rows[start:]:
        cells = [c.strip() for c in row]
        target = cells[idx_target] if idx_target is not None and idx_target < len(cells) else ""
        pred = cells[idx_pred] if idx_pred is not None and idx_pred < len(cells) else ""
        prob = cells[idx_prob] if idx_prob is not None and idx_prob < len(cells) else ""
        tgt_low = target.lower()
        if tgt_low == "ld50":
            try:
                ld50 = float(pred)
            except ValueError:
                pass
            try:
                accuracy = float(prob)
            except ValueError:
                pass
        elif tgt_low in ("tox_class", "toxicity class", "toxicity_class"):
            try:
                tox_class = int(pred)
            except ValueError:
                pass

    if ld50 is None:
        # Tolerate legacy label,value-per-line form: "LD50 (mg/kg),1000.0"
        for row in rows:
            cells = [c.strip() for c in row]
            joined = ",".join(cells).lower()
            if "ld50" in joined and len(cells) >= 2 and ld50 is None:
                try:
                    ld50 = float(cells[1])
                except ValueError:
                    pass
            elif ("toxicity class" in joined or "tox_class" in joined) and len(cells) >= 2 and tox_class is None:
                try:
                    tox_class = int(cells[1])
                except ValueError:
                    pass

    if ld50 is None:
        return None
    return ld50, tox_class, accuracy


def clear_cache() -> int:
    """Clear the in-memory ProTox cache; returns number of entries evicted."""
    n = len(_CACHE)
    _CACHE.clear()
    return n
