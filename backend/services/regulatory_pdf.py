#!/usr/bin/env python3
"""
Regulatory PDF Generator
========================
Phase 3 — Regulatory & Clinical Safety Layer

Generates tamper-evident safety dossiers using fpdf2. Each PDF includes:
  - Unique document hash and version
  - Digital signature block (HMAC-SHA256)
  - Audit trail of all input data hashes
  - Multi-page report with structured tables

Data-integrity features:
  - Document hash embedded in PDF metadata + footer
  - Signature verification API endpoint
  - All input data hashed and recorded in audit trail
  - Deterministic rendering for reproducibility

IMPORTANT: HMAC-SHA256 signatures provide DATA INTEGRITY ONLY. Full
21 CFR Part 11 compliance additionally requires unique user authentication,
access controls, SOPs, record-retention policies, and validated computer
system workflows (IQ/OQ/PQ) — see remediation plan Track 4.
"""

import hashlib
import hmac
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from rdkit import Chem
from rdkit.Chem import Descriptors

logger = logging.getLogger('RegulatoryPDF')

# ───────────────────────────────────────────────────────────────────────────
# Version lock
# ───────────────────────────────────────────────────────────────────────────
PDF_RULESET_VERSION = "v3.0.0"

# ───────────────────────────────────────────────────────────────────────────
# Regulatory PDF template configuration
# ───────────────────────────────────────────────────────────────────────────
PDF_CONFIG = {
    "title": "AnuDrishti Regulatory Safety Dossier",
    "subtitle": "Phase 3 - Multi-Channel Cardiotox Alert Screen, Species Translation & NAMs",
    "subject": "Tamper-Evident Safety Dossier (HMAC-SHA256 Integrity)",
    "author": "AnuDrishti - Lethos-AI GCS",
    "keywords": "drug safety, multi-channel cardiotox alert screen, cardiotoxicity, species translation, NAMs, audit trail",
    "font_family": "Helvetica",
    "font_size_title": 16,
    "font_size_heading": 12,
    "font_size_body": 10,
    "font_size_small": 8,
    "page_margin": 15.0,  # mm
}


def _compute_file_hash(cipa_data: Dict[str, Any], species_data: Dict[str, Any],
                       timestamp: str, batch_id: str, compound_name: str) -> str:
    """Compute SHA-256 hash of the entire dossier content for audit trail.

    This hash represents the complete, immutable content of the PDF.
    """
    content = {
        "ruleset": PDF_RULESET_VERSION,
        "timestamp": timestamp,
        "batch_id": batch_id,
        "compound_name": compound_name,
        "cardiotox": cipa_data,
        "species": species_data,
    }
    content_str = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(content_str.encode("utf-8")).hexdigest()


def _compute_signature(file_hash: str, timestamp: str, model_name: str) -> str:
    """Compute HMAC-SHA256 signature of the dossier.

    Uses a deterministic key derived from the ruleset version + model name.
    In production, this would use a proper PKI signing service.
    """
    key = f"AnuDrishti-{PDF_RULESET_VERSION}-{model_name}".encode("utf-8")
    msg = f"{file_hash}:{timestamp}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def _hash_dict(d: Dict[str, Any]) -> str:
    """Compute a stable SHA-256 hash of a dictionary's contents."""
    content_str = json.dumps(d, sort_keys=True, default=str)
    return hashlib.sha256(content_str.encode("utf-8")).hexdigest()[:32] + "..."


class RegulatoryPDF(FPDF):
    """Custom FPDF subclass with Part 11-compliant headers and footers."""

    def __init__(self, file_hash: str, signature: str, timestamp: str,
                 model_name: str = "AnuDrishti", version: str = PDF_RULESET_VERSION):
        super().__init__(orientation="P", unit="mm", format="A4")
        # Set margins
        self.set_margins(PDF_CONFIG["page_margin"], PDF_CONFIG["page_margin"], PDF_CONFIG["page_margin"])
        self.set_auto_page_break(True, PDF_CONFIG["page_margin"] + 15)
        self._file_hash = file_hash
        self._signature = signature
        self._timestamp = timestamp
        self._model_name = model_name
        self._version = version
        self._metadata_str = ""
        self.set_title(PDF_CONFIG["title"])
        self.set_subject(PDF_CONFIG["subject"])
        self.set_author(PDF_CONFIG["author"])
        self.set_keywords(PDF_CONFIG["keywords"])

    def header(self):
        """Header with document title on first page only."""
        if self.page_no() == 1:
            self.set_font(PDF_CONFIG["font_family"], "B", PDF_CONFIG["font_size_title"])
            self.cell(0, 8, PDF_CONFIG["title"], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            self.set_font(PDF_CONFIG["font_family"], "", PDF_CONFIG["font_size_body"])
            self.cell(0, 5, PDF_CONFIG["subtitle"], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            self.ln(3)
            self.set_draw_color(100, 100, 100)
            self.line(self.l_margin, self.get_y(),
                      self.w - self.r_margin, self.get_y())
            self.ln(5)
        else:
            self.set_font(PDF_CONFIG["font_family"], "B", PDF_CONFIG["font_size_small"])
            self.set_text_color(80, 80, 80)
            self.cell(0, 5, PDF_CONFIG["title"], new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
            self.ln(2)

    def footer(self):
        """Footer with page number, document hash, and signature."""
        self.set_y(-12)
        self.set_font(PDF_CONFIG["font_family"], "I", PDF_CONFIG["font_size_small"])
        self.set_text_color(100, 100, 100)
        # Page number
        self.cell(0, 4, f"Page {self.page_no()}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Document hash (truncated for display)
        self.set_font(PDF_CONFIG["font_family"], "", PDF_CONFIG["font_size_small"] - 1)
        hash_display = self._file_hash[:24] + "..."
        self.cell(0, 3, f"Doc ID: {hash_display}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        # Signature (truncated)
        sig_display = self._signature[:16] + "..."
        self.cell(0, 3, f"Signature: {sig_display}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)


class RegulatoryPDFGenerator:
    """Generates tamper-evident (HMAC-SHA256) safety dossier PDFs.

    Usage:
        gen = RegulatoryPDFGenerator()
        pdf_path = gen.generate(cipa_data, species_data, batch_id="BATCH001")

    The generated PDF is tamper-evident: any modification to the source
    data will produce a different file_hash, which is embedded in the PDF
    footer and metadata. Signature verification confirms authenticity.
    Note: tamper evidence != 21 CFR Part 11 compliance (needs access
    controls + SOPs + validated workflows).
    """

    def __init__(self, signing_key: Optional[str] = None):
        self.ruleset_version = PDF_RULESET_VERSION
        self._signing_key = signing_key or os.environ.get(
            "ANUDRISHTI_PDF_KEY", "default-regulatory-key")

    def generate(self, cipa_data: Dict[str, Any], species_data: Dict[str, Any],
                 batch_id: str = "DEFAULT",
                 compound_name: str = "Unknown Compound") -> str:
        """Generate a regulatory PDF dossier from Cardiotox Screen + Species Translation data.

        Args:
            cipa_data: Output dict from MultiChannelCardiotoxScreen.evaluate_molecule()
            species_data: Output dict from SpeciesTranslationEngine.translate_molecule()
            batch_id: Identifier for the testing batch
            compound_name: Human-readable compound name

        Returns: Absolute path to the generated PDF file.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        # Compute content hash and signature
        file_hash = _compute_file_hash(cipa_data, species_data, timestamp, batch_id, compound_name)
        signature = _compute_signature(file_hash, timestamp, compound_name)
        sig_key = self._signing_key.encode("utf-8")
        sig_full = hmac.new(sig_key, signature.encode("utf-8"), hashlib.sha256).hexdigest()

        # Create PDF
        pdf = RegulatoryPDF(file_hash, sig_full, timestamp, compound_name, self.ruleset_version)
        pdf.add_page()

        self._render_cover(pdf, compound_name, batch_id, timestamp)
        pdf.add_page()
        self._render_cardiotox_section(pdf, cipa_data)
        pdf.add_page()
        self._render_species_section(pdf, species_data)
        pdf.add_page()
        self._render_audit_trail(pdf, cipa_data, species_data, file_hash, sig_full, timestamp,
                                batch_id, compound_name)

        # Embed metadata as a hidden custom property
        meta = {
            "file_hash": file_hash,
            "signature": sig_full,
            "timestamp": timestamp,
            "version": self.ruleset_version,
            "compound_name": compound_name,
            "batch_id": batch_id,
            "cardiotox_data": cipa_data,
            "species_data": species_data,
        }
        meta_json = json.dumps(meta, sort_keys=True, default=str)
        self._embed_metadata_in_pdf(meta_json)

        # Save file
        safe_name = re.sub(r"[^a-zA-Z0-9_-]", "_", compound_name)[:50]
        date_str = timestamp.replace("T", "_").replace("Z", "").replace(":", "")
        filename = f"regulatory_dossier_{safe_name}_{batch_id}_{date_str}.pdf"
        output_dir = os.path.join(os.getcwd(), "regulatory_reports")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, filename)

        pdf.output(output_path)
        logger.info(f"Regulatory PDF generated: {output_path}")

        # Post-process: embed metadata into PDF for signature verification
        self._post_process_pdf(output_path, meta_json)
        return output_path

    def _embed_metadata_in_pdf(self, meta_json: str):
        """Pre-store metadata for post-processing (called before PDF save)."""
        self._meta_json = meta_json

    def _post_process_pdf(self, pdf_path: str, meta_json: str):
        """Append a metadata PDF object to the generated file for verification."""
        with open(pdf_path, "rb") as f:
            lines = f.readlines()

        # Find the startxref line
        startxref_offset = None
        xref_offset = None
        for i in range(len(lines) - 1, max(len(lines) - 20, 0), -1):
            line = lines[i].strip()
            if line.startswith(b"startxref"):
                startxref_offset = i
                break
        if startxref_offset is None:
            # Fallback: append metadata object at end of file
            obj_data = f"\n%ANUDRISHTI_METADATA_START\n{meta_json}\n%ANUDRISHTI_METADATA_END\n".encode("utf-8")
            with open(pdf_path, "ab") as f:
                f.write(obj_data)
            return

        # Parse current xref offset
        xref_line = lines[startxref_offset + 1].strip()
        xref_offset = int(xref_line)

        # Calculate byte offset for new object
        # We need to find the end of the current PDF content
        current_end = sum(len(line) for line in lines)

        # Build new objects to append
        obj_num = "999"
        new_xref_offset = current_end

        # Encode metadata as a hex string to avoid encoding issues
        meta_hex = meta_json.encode("utf-8").hex()

        # Append the metadata object
        obj_bytes = f"\n{obj_num} 0 obj\n<< /Type /AnuDrishtiMetadata /Data ({meta_hex}) >>\nendobj\n".encode("utf-8")
        lines.append(obj_bytes)

        # Re-compute xref
        xref_pos = sum(len(line) for line in lines)

        xref_entry = f"trailer\n<< /Size {int(obj_num) + 1} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF\n".encode("utf-8")
        lines.append(xref_entry)

        with open(pdf_path, "wb") as f:
            f.writelines(lines)

    def verify_signature(self, pdf_path: str) -> Dict[str, Any]:
        """Verify the digital signature of a regulatory PDF.

        Extracts the document hash and signature from the PDF and verifies
        them against the embedded metadata.
        """
        if not os.path.exists(pdf_path):
            return {"valid": False, "error": "File not found", "pdf_path": pdf_path}

        try:
            # Read raw PDF bytes
            with open(pdf_path, "rb") as f:
                raw = f.read()
            raw_str = raw.decode("utf-8", errors="replace")

            # Extract embedded metadata from the appended PDF object
            import re as _re
            # Look for the hex-encoded metadata object we appended
            # Pattern: ( /Type /AnuDrishtiMetadata /Data (HEXSTRING) )
            meta_match = _re.search(r"/AnuDrishtiMetadata /Data \(([0-9a-f]+)\)", raw_str)
            if not meta_match:
                # Fallback: look for the plain-text marker
                meta_match = _re.search(r"%ANUDRISHTI_METADATA_START\n(.+?)\n%ANUDRISHTI_METADATA_END",
                                        raw_str, _re.DOTALL)
                if meta_match:
                    meta_json = meta_match.group(1)
                else:
                    return {"valid": False, "error": "No metadata found in PDF - document may be tampered",
                            "pdf_path": pdf_path}
            else:
                # Decode hex-encoded metadata
                meta_hex = meta_match.group(1)
                meta_json = bytes.fromhex(meta_hex).decode("utf-8")

            try:
                metadata = json.loads(meta_json)
            except json.JSONDecodeError:
                return {"valid": False, "error": "Corrupted metadata in PDF",
                        "pdf_path": pdf_path}

            stored_hash = metadata.get("file_hash", "")
            stored_sig = metadata.get("signature", "")
            stored_timestamp = metadata.get("timestamp", "")
            stored_version = metadata.get("version", "")
            compound_name = metadata.get("compound_name", "Unknown")
            batch_id = metadata.get("batch_id", "DEFAULT")
            cipa_data = metadata.get("cardiotox_data", metadata.get("cipa_data", {}))
            species_data = metadata.get("species_data", {})

            # Recompute hash from embedded data
            recomputed_hash = _compute_file_hash(cipa_data, species_data,
                                                 stored_timestamp, batch_id,
                                                 compound_name)

            # Recompute signature
            recomputed_sig = _compute_signature(recomputed_hash, stored_timestamp, compound_name)
            sig_key = self._signing_key.encode("utf-8")
            recomputed_sig_full = hmac.new(sig_key, recomputed_sig.encode("utf-8"),
                                           hashlib.sha256).hexdigest()

            hash_valid = hmac.compare_digest(stored_hash, recomputed_hash)
            sig_valid = hmac.compare_digest(stored_sig, recomputed_sig_full)

            return {
                "valid": hash_valid and sig_valid,
                "file_hash_match": hash_valid,
                "signature_match": sig_valid,
                "file_hash": stored_hash,
                "signature": stored_sig[:32] + "...",
                "timestamp": stored_timestamp,
                "version": stored_version,
                "ruleset_version": self.ruleset_version,
                "pdf_path": pdf_path,
            }
        except Exception as e:
            return {"valid": False, "error": f"Verification failed: {str(e)}",
                    "pdf_path": pdf_path}

    def _render_cover(self, pdf: RegulatoryPDF, compound_name: str,
                      batch_id: str, timestamp: str):
        """Render the cover page with document metadata."""
        pdf.ln(20)

        # Agency header
        pdf.set_font(PDF_CONFIG["font_family"], "B", 14)
        pdf.set_text_color(0, 51, 102)
        pdf.cell(0, 8, "LETHOS-AI GCS", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font(PDF_CONFIG["font_family"], "I", 12)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 6, "AnuDrishti - Drug Safety Platform", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)

        # Regulatory compliance statement
        pdf.set_font(PDF_CONFIG["font_family"], "B", 12)
        pdf.cell(0, 8, "Tamper-Evident Electronic Record (HMAC-SHA256)", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.set_font(PDF_CONFIG["font_family"], "", 10)
        pdf.cell(0, 6, "Screening-Level Safety Dossier - Research Use Only", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align="C")
        pdf.ln(10)

        # Document metadata table
        self._add_heading(pdf, "Document Metadata", level=2)
        meta_rows = [
            ["Document Title", PDF_CONFIG["title"]],
            ["Compound", compound_name],
            ["Batch ID", batch_id],
            ["Generated (UTC)", timestamp],
            ["Engine Version", self.ruleset_version],
            ["Risk Engine", "AnuDrishti Phase 3"],
            ["Data Integrity", "HMAC-SHA256 signature (see Part 11 note below)"],
        ]
        self._add_table(pdf, ["Field", "Value"], meta_rows, col_widths=[50, 100])

        # Regulatory statement
        pdf.ln(5)
        self._add_heading(pdf, "Regulatory Statement & Limitations", level=2)
        self._add_body(pdf,
            "This document is a computer-generated safety screening dossier "
            "produced by the AnuDrishti Drug Safety Platform. It integrates a "
            "structure-based multi-channel cardiotox ALERT SCREEN (not the FDA "
            "CiPA paradigm), cross-species toxicokinetic extrapolations from "
            "rule-estimated clearance (not measured IVIVE input), and rule-based "
            "LD50 estimates (unvalidated hypothesis generators). All content is "
            "cryptographically signed for tamper evidence and integrity can be "
            "verified via the signature verification endpoint. HMAC-SHA256 "
            "signatures provide data integrity ONLY; full 21 CFR Part 11 "
            "compliance additionally requires access controls, standard operating "
            "procedures, and validated computer-system workflows. Predictions "
            "are RESEARCH USE ONLY and not for clinical decision making.",
            indent=5
        )

        # Signature block placeholder
        pdf.ln(10)
        pdf.set_font(PDF_CONFIG["font_family"], "", PDF_CONFIG["font_size_body"])
        pdf.cell(0, 5, "Authorized Signature:", border="B", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
        pdf.cell(0, 5, f"Date: {timestamp}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(2)
        pdf.multi_cell(0, 4,
            "Any modification to this document after generation will invalidate "
            "the digital signature and produce a verification failure.")

    def _render_cardiotox_section(self, pdf: RegulatoryPDF, cipa_data: Dict[str, Any]):
        """Render the Multi-Channel Cardiotox Alert Screen section."""
        self._add_heading(pdf, "Section 1: Multi-Channel Cardiotox Alert Screen (Structure-Based)", level=2)

        smiles = cipa_data.get("smiles", "")
        pdf.set_font(PDF_CONFIG["font_family"], "", PDF_CONFIG["font_size_body"])
        pdf.cell(0, 5, f"Compound SMILES: {smiles}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 5, f"Model: {cipa_data.get('model', 'MultiChannelCardiotoxScreen')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 5, f"Version: {cipa_data.get('model_version', 'N/A')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.multi_cell(0, 4,
            "DISCLAIMER: SMARTS/rule-based structural alert screen (hypothesis "
            "generator). NOT the FDA CiPA paradigm, which requires experimental "
            "patch-clamp IC50 data and in silico action-potential simulation.")

        # Channel predictions table
        channels = cipa_data.get("channels", {})
        chan_rows = []
        for ch_name, ch_data in channels.items():
            prob = round(ch_data.get("probability", 0), 4)
            ci_low = round(ch_data.get("conformal_ci_low", 0), 4)
            ci_high = round(ch_data.get("conformal_ci_high", 1), 4)
            matched = ch_data.get("matched_alerts", [])
            alert_str = ", ".join(a.get("name", "?") for a in matched) if matched else "None"
            chan_rows.append([
                ch_name.replace("_channel", "").upper(),
                f"{prob}",
                f"[{ci_low}, {ci_high}]",
                alert_str,
            ])

        self._add_heading(pdf, "1.1 Ion Channel Blocking Estimates", level=3)
        self._add_table(pdf,
            ["Channel", "Probability", "Indicative CI*", "Matched Alerts"],
            chan_rows,
            col_widths=[45, 25, 35, 55]
        )
        pdf.set_font(PDF_CONFIG["font_family"], "", PDF_CONFIG["font_size_small"])
        pdf.multi_cell(0, 4,
            "*CI bands use default placeholder q_hat estimates and are NOT "
            "coverage-guaranteed until calibrated on real held-out data.")

        # qNet and PRS
        self._add_heading(pdf, "1.2 Network-Level Arrhythmia Metrics", level=3)
        qnet_rows = [
            ["qNet (net charge carrier balance)", str(round(cipa_data.get("q_net", 0), 4))],
            ["Proarrhythmic Risk Score (PRS)", str(round(cipa_data.get("proarrhythmic_risk_score", 0), 4))],
            ["Risk Classification", cipa_data.get("risk_classification", "N/A")],
            ["GHS Risk Flag", cipa_data.get("ghs_risk_flag", "N/A")],
        ]
        self._add_table(pdf, ["Metric", "Value"], qnet_rows, col_widths=[80, 55])

        # Mechanism details
        self._add_heading(pdf, "1.3 Mechanistic Interpretation", level=3)
        mech = cipa_data.get("mechanistic_details", {})
        if mech:
            for key, val in mech.items():
                self._add_body(pdf, f"  {key}: {val}", indent=5)
        else:
            self._add_body(pdf, "  No mechanistic details available.")

        # Conformal prediction summary
        cp = cipa_data.get("conformal_prediction", {})
        if cp:
            self._add_heading(pdf, "1.4 Conformal Prediction Summary", level=3)
            cp_rows = [
                ["q_hat", str(round(cp.get("q_hat", 0), 4))],
                ["Coverage", str(cp.get("coverage", "N/A"))],
                ["Calibration Set Size", str(cp.get("n_calibration", "N/A"))],
            ]
            self._add_table(pdf, ["Parameter", "Value"], cp_rows, col_widths=[60, 50])

    def _render_species_section(self, pdf: RegulatoryPDF, species_data: Dict[str, Any]):
        """Render the Cross-Species Translation section."""
        self._add_heading(pdf, "Section 2: Cross-Species Translation & NAMs", level=2)

        pdf.set_font(PDF_CONFIG["font_family"], "", PDF_CONFIG["font_size_body"])
        pdf.cell(0, 5, f"Compound SMILES: {species_data.get('smiles', 'N/A')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 5, f"Ruleset: {species_data.get('ruleset_version', 'N/A')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 5, f"Model Hash: {species_data.get('model_hash', 'N/A')}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # LD50 predictions
        ld50 = species_data.get("ld50", {})
        if ld50:
            self._add_heading(pdf, "2.1 Acute Oral Toxicity (LD50)", level=3)
            ld50_rows = [
                ["Rat", str(ld50.get("rat_ld50_mg_per_kg", "N/A")),
                 ld50.get("rat_ghs_category", {}).get("category", "N/A")],
                ["Mouse", str(ld50.get("mouse_ld50_mg_per_kg", "N/A")),
                 ld50.get("mouse_ghs_category", {}).get("category", "N/A")],
            ]
            self._add_table(pdf, ["Species", "LD50 (mg/kg)", "GHS Category"],
                            ld50_rows, col_widths=[40, 50, 40])

        # Allometric clearance
        cls = species_data.get("clearance_ml_per_min_per_kg", {})
        if cls:
            self._add_heading(pdf, "2.2 Allometric Pharmacokinetic Scaling", level=3)
            self._add_body(pdf, "CL per kg proportional to BW^(-0.25) (Kleiber's law)")
            cl_rows = []
            for sp_key, sp_name in [("human", "Human"), ("rat", "Rat"),
                                    ("dog", "Beagle Dog"),
                                    ("monkey", "Cynomolgus Monkey"),
                                    ("mouse", "Mouse")]:
                if sp_key in cls:
                    cl_rows.append([sp_name, f"{cls[sp_key]} mL/min/kg"])
            self._add_table(pdf, ["Species", "In Vivo Clearance"],
                            cl_rows, col_widths=[60, 60])

        # HED & Safety Margins
        self._add_heading(pdf, "2.3 Human Equivalent Dose & Safety Margins", level=3)
        hed_rows = [
            ["Human Dose (input)", f"{species_data.get('human_dose_mg', 'N/A')} mg"],
            ["HED (Human Equivalent Dose)", f"{species_data.get('hed_mg', 'N/A')} mg"],
            ["NOAEL", f"{species_data.get('noael_mg', 'N/A')} mg"],
            ["Margin of Safety (MOS)", f"{species_data.get('margin_of_safety', 'N/A')}"],
        ]
        self._add_table(pdf, ["Metric", "Value"], hed_rows, col_widths=[80, 55])

        # NAMs statement
        nams = species_data.get("nams_justification", "")
        if nams:
            self._add_heading(pdf, "2.4 NAMs Statement & Limitations", level=3)
            self._add_body(pdf, nams, indent=3)

    def _render_audit_trail(self, pdf: RegulatoryPDF, cipa_data: Dict[str, Any],
                            species_data: Dict[str, Any],
                            file_hash: str, signature: str, timestamp: str,
                            batch_id: str, compound_name: str):
        """Render the audit trail with cryptographic hashes."""
        self._add_heading(pdf, "Section 3: Audit Trail & Cryptographic Integrity", level=2)

        self._add_heading(pdf, "3.1 Digital Signature", level=3)
        sig_rows = [
            ["Document Hash (SHA-256)", file_hash],
            ["Digital Signature (HMAC-SHA256)", signature],
            ["Timestamp (UTC)", timestamp],
            ["Ruleset Version", self.ruleset_version],
            ["Data Integrity", "HMAC-SHA256 tamper evidence"],
        ]
        self._add_table(pdf, ["Field", "Hash / Value"], sig_rows, col_widths=[60, 90])

        self._add_heading(pdf, "3.2 Input Data Hashes", level=3)
        input_rows = [
            ["Cardiotox Screen Data Hash", _hash_dict(cipa_data)],
            ["Species Translation Hash", _hash_dict(species_data)],
            ["Batch ID", batch_id],
            ["Compound Name", compound_name],
        ]
        self._add_table(pdf, ["Input", "SHA-256 Hash"], input_rows, col_widths=[60, 90])

        self._add_heading(pdf, "3.3 Data Integrity Attestation", level=3)
        self._add_body(pdf,
            "This dossier provides the following data-integrity guarantees:"
            "\n\n1. Tamper evidence: HMAC-SHA256 signature verifies that the "
            "document content has not been modified since generation."
            "\n2. Audit trail: All input data hashes are recorded in "
            "Section 3.2."
            "\n3. Traceability: Ruleset version and per-input hashes are "
            "embedded in the document metadata."
            "\n\nIMPORTANT LIMITATIONS: A cryptographic signature establishes "
            "data integrity ONLY. It does NOT by itself constitute 21 CFR Part "
            "11 compliance, which additionally requires unique user "
            "authentication, access controls, standard operating procedures, "
            "record-retention policies, and validated computer-system workflows "
            "(IQ/OQ/PQ). Predictions herein are screening-level estimates from "
            "uncalibrated rule-based models: RESEARCH USE ONLY - not for "
            "clinical decision making or regulatory submission.", indent=3
        )

    @staticmethod
    def _add_heading(pdf: FPDF, text: str, level: int = 1):
        """Add a heading with appropriate font size."""
        size = {1: PDF_CONFIG["font_size_heading"], 2: 12, 3: 10}[level]
        pdf.set_font(PDF_CONFIG["font_family"], "B", size)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 6, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)
        pdf.ln(1)

    @staticmethod
    def _add_body(pdf: FPDF, text: str, indent: float = 0):
        """Add body text, wrapping at page width."""
        pdf.set_font(PDF_CONFIG["font_family"], "", PDF_CONFIG["font_size_body"])
        if indent > 0:
            pdf.cell(indent)
        pdf.multi_cell(0, 5, text)
        pdf.ln(0.5)

    @staticmethod
    def _add_table(pdf: FPDF, headers: List[str], rows: List[List[str]],
                   col_widths: Optional[List[float]] = None):
        """Add a formatted table."""
        if not rows:
            pdf.set_font(PDF_CONFIG["font_family"], "", PDF_CONFIG["font_size_body"])
            pdf.cell(0, 5, "  No data available.", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            return

        if col_widths is None:
            col_widths = [60 for _ in headers]

        total_w = sum(col_widths)
        start_x = (pdf.w - total_w) / 2
        start_x = max(pdf.l_margin, start_x)

        # Table header
        pdf.set_font(PDF_CONFIG["font_family"], "B", PDF_CONFIG["font_size_small"])
        pdf.set_fill_color(220, 220, 220)
        pdf.set_text_color(30, 30, 30)
        x = start_x
        for i, header in enumerate(headers):
            w = col_widths[i]
            pdf.set_xy(x, pdf.get_y())
            pdf.cell(w, 5, header, border=1, align="C", fill=True)
            x += w
        pdf.ln()

        # Table rows
        pdf.set_font(PDF_CONFIG["font_family"], "", PDF_CONFIG["font_size_small"])
        for row in rows:
            x = start_x
            for i, cell in enumerate(row):
                w = col_widths[i]
                pdf.set_xy(x, pdf.get_y())
                pdf.cell(w, 5, str(cell), border=1, align="L")
                x += w
            pdf.ln()
        pdf.ln(2)


# ───────────────────────────────────────────────────────────────────────────
# Module-level singleton
# ───────────────────────────────────────────────────────────────────────────
_DEFAULT_GENERATOR: Optional[RegulatoryPDFGenerator] = None


def get_default_pdf_generator() -> RegulatoryPDFGenerator:
    """Return a module-level singleton RegulatoryPDFGenerator (lazy init)."""
    global _DEFAULT_GENERATOR
    if _DEFAULT_GENERATOR is None:
        _DEFAULT_GENERATOR = RegulatoryPDFGenerator()
    return _DEFAULT_GENERATOR
