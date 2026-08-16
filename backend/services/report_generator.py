#!/usr/bin/env python3
"""
PDF Report Generation Service
==============================
Generates structured PDF reports from PharmaGuard analysis results using
pdfkit (WeasyPrint/wkhtmltopdf) and a template engine.

Phase 3 feature for SIH 2026.
"""

import os
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Use pdfkit with wkhtmltopdf for reliable HTML-to-PDF
try:
    import pdfkit
    HAS_PDFKIT = True
except ImportError:
    HAS_PDFKIT = False
    print("⚠️ pdfkit not available - PDF generation disabled")

# Fallback: Try fpdf
FPDF = None
HAS_FPDF = False
try:
    from fpdf import FPDF
    HAS_FPDF = True
except ImportError:
    pass

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body { font-family: 'Helvetica', sans-serif; margin: 30px; color: #333; }
        .header { text-align: center; border-bottom: 3px solid #6366f1; padding-bottom: 15px; margin-bottom: 25px; }
        .header h1 { color: #4338ca; font-size: 24px; margin: 0; }
        .header .subtitle { color: #6b7280; font-size: 12px; margin-top: 5px; }
        .section { margin-bottom: 25px; page-break-inside: avoid; }
        .section h2 { color: #6366f1; border-left: 4px solid #6366f1; padding-left: 10px; font-size: 16px; }
        .metric-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-top: 10px; }
        .metric-card { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px; padding: 10px; }
        .metric-label { font-weight: bold; color: #374151; font-size: 11px; text-transform: uppercase; }
        .metric-value { font-size: 14px; color: #111827; margin-top: 3px; }
        .toxicity-bar { height: 20px; background: linear-gradient(to right, #10b981 0%, #fbbf24 50%, #ef4444 100%); border-radius: 10px; margin: 8px 0; position: relative; }
        .toxicity-marker { position: absolute; top: -3px; width: 3px; height: 26px; background: #1e293b; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 11px; }
        th, td { border: 1px solid #d1d5db; padding: 6px 8px; text-align: left; }
        th { background: #f3f4f6; font-weight: bold; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 10px; font-weight: bold; text-transform: uppercase; }
        .badge-toxic { background: #fee2e2; color: #991b2b; }
        .badge-safe { background: #dcfce8; color: #166534; }
        .confidence-high { color: #166534; }
        .confidence-medium { color: #92400e; }
        .confidence-low { color: #991b2b; }
        .footer { text-align: center; margin-top: 30px; padding-top: 15px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>PharmaGuard AI - Molecular Safety Report</h1>
        <div class="subtitle">Explainable AI for Molecular Toxicity Prediction | Generated: {timestamp}</div>
    </div>

    <div class="section">
        <h2>1. Molecule Overview</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">SMILES</div>
                <div class="metric-value" style="font-family: monospace; font-size: 12px;">{smiles}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Overall Assessment</div>
                <div class="metric-value">{assessment}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>2. Toxicity Probability</h2>
        <div class="toxicity-bar">
            <div class="toxicity-marker" style="left: {toxicity_pct}%"></div>
        </div>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Mean Toxicity Probability</div>
                <div class="metric-value">{mean_toxicity}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">95% Confidence Interval</div>
                <div class="metric-value">[{ci_low}, {ci_high}]</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>3. Endpoint Predictions</h2>
        <table>
            <thead>
                <tr>
                    <th>Endpoint</th>
                    <th>Probability</th>
                    <th>Prediction</th>
                    <th>Confidence</th>
                    <th>Source</th>
                </tr>
            </thead>
            <tbody>
                {endpoint_rows}
            </tbody>
        </table>
    </div>

    <div class="section">
        <h2>4. Model Ensemble</h2>
        <table>
            <thead>
                <tr>
                    <th>Model</th>
                    <th>Role</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                {model_rows}
            </tbody>
        </table>
    </div>

    {explanation_section}

    <div class="section">
        <h2>5. Key Statistics</h2>
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-label">Total Endpoints</div>
                <div class="metric-value">{num_endpoints}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Toxic Endpoints</div>
                <div class="metric-value">{toxic_endpoints}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">OOD Score</div>
                <div class="metric-value">{ood_score}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Faithfulness Score</div>
                <div class="metric-value">{faithfulness_score}</div>
            </div>
        </div>
    </div>

    <div class="footer">
        PharmaGuard AI - Explainable AI for Molecular Toxicity Prediction
        <div>This report was generated by the Faithful-LLM-Augmented Explainability pipeline.</div>
        <div>SIH 2026 | Defense-grade AI for molecular safety assessment.</div>
    </div>
</body>
</html>
"""

# Fallback pure-Python PDF generator
class _NoFPDF:
    """Placeholder when FPDF is not available."""
    def __init__(self, *args, **kwargs):
        pass
    def __getattr__(self, name):
        return lambda *args, **kwargs: None

_FP = FPDF if FPDF is not None else _NoFPDF

class SimplePDF(_FP):
    """Simple PDF generator fallback when pdfkit is not available."""
    
    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(67, 56, 200)
        self.cell(0, 10, 'PharmaGuard AI - Molecular Safety Report', border='B', ln=True, align='C')
        self.ln(5)
    
    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(99, 102, 241)
        self.cell(0, 10, title, ln=True)
        self.ln(2)
    
    def chapter_body(self, body):
        self.set_font('Helvetica', '', 10)
        self.set_text_color(51, 51, 51)
        self.multi_cell(0, 6, body)
        self.ln(1)
    
    def metric_card(self, label, value):
        self.set_font('Helvetica', 'B', 9)
        self.set_text_color(55, 65, 85)
        self.cell(0, 5, f'{label}:', ln=True)
        self.set_font('Helvetica', '', 10)
        self.set_text_color(17, 24, 39)
        self.cell(0, 6, str(value), ln=True)
        self.ln(1)


def get_pdf_generator():
    """Return the best available PDF generator."""
    if HAS_PDFKIT:
        return 'pdfkit'
    elif HAS_FPDF:
        return 'fpdf'
    else:
        raise ImportError("No PDF generation library available. Install pdfkit + wkhtmltopdf, or fpdf.")


def generate_pdf_report(results: Dict[str, Any]) -> bytes:
    """
    Generate a PDF report from analysis results.
    
    Args:
        results: Dictionary containing analysis results from /api/analyze
    
    Returns:
        PDF file content as bytes
    """
    generator = get_pdf_generator()
    
    if generator == 'pdfkit':
        return _generate_pdfkit_report(results)
    else:
        return _generate_fpdf_report(results)


def _generate_pdfkit_report(results: Dict[str, Any]) -> bytes:
    """Generate PDF using pdfkit (WeasyPrint/wkhtmltopdf)."""
    
    # Ensure wkhtmltopdf is available
    config = pdfkit.configuration(wkhtmltopdf='/usr/bin/wkhtmltopdf') if HAS_PDFKIT else None
    
    # Build HTML
    html = _build_html_report(results)
    
    # Generate PDF
    pdf_bytes = pdfkit.from_string(html, configuration=config)
    return pdf_bytes


def _generate_fpdf_report(results: Dict[str, Any]) -> bytes:
    """Generate PDF using fpdf as a fallback."""
    
    pdf = SimplePDF()
    pdf.add_page()
    
    # Title
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(67, 56, 200)
    pdf.cell(0, 15, 'PharmaGuard AI - Molecular Safety Report', ln=True, align='C')
    pdf.ln(5)
    
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(107, 115, 128)
    pdf.cell(0, 5, f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', ln=True, align='C')
    pdf.ln(10)
    
    # Section 1: Molecule Overview
    pdf.chapter_title('1. Molecule Overview')
    pdf.metric_card('SMILES', results.get('smiles', 'N/A'))
    
    summary = results.get('summary', {})
    assessment = summary.get('overall_assessment', 'Unknown')
    pdf.metric_card('Overall Assessment', assessment)
    
    # Section 2: Toxicity Probability
    pdf.chapter_title('2. Toxicity Probability')
    mean_toxicity = summary.get('average_toxicity_probability', 0.5)
    ci_low = summary.get('toxicity_ci_low', 0.5)
    ci_high = summary.get('toxicity_ci_high', 0.5)
    pdf.metric_card('Mean Toxicity Probability', f'{mean_toxicity:.4f}')
    pdf.metric_card('95% CI', f'[{ci_low:.4f}, {ci_high:.4f}]')
    
    # Section 3: Endpoint Predictions
    pdf.chapter_title('3. Endpoint Predictions')
    predictions = results.get('predictions', {})
    for endpoint, pred in predictions.items():
        if isinstance(pred, dict) and 'probability' in pred:
            pdf.metric_card(
                endpoint,
                f"Prob: {pred['probability']:.4f} | {pred.get('prediction', 'N/A')} | Source: {pred.get('source', 'N/A')}"
            )
    
    # Section 4: Model Ensemble
    pdf.chapter_title('4. Model Ensemble')
    pdf.metric_card('Attention-GIN (Tox21)', 'Primary model - 12 endpoints (ROC-AUC 0.8368)')
    pdf.metric_card('XGBoost (NR)', 'Secondary - 5 NR endpoints')
    pdf.metric_card('ChemBERTa', 'Phase 3 - SMILES encoder (768-dim embeddings)')
    pdf.metric_card('GPS Graph Transformer', 'Phase 3 - Graph transformer')
    pdf.metric_card('TDC Models', 'Phase 3 - hERG, DILI, Ames (placeholder)')
    
    # Section 5: Statistics
    pdf.chapter_title('5. Key Statistics')
    pdf.metric_card('Total Endpoints', summary.get('num_endpoints', 'N/A'))
    pdf.metric_card('Toxic Endpoints', summary.get('toxic_endpoints', 'N/A'))
    pdf.metric_card('Std Deviation', f"{summary.get('toxicity_std', 0):.4f}")
    
    # Footer
    pdf.ln(10)
    pdf.set_font('Helvetica', '', 8)
    pdf.set_text_color(153, 159, 175)
    pdf.multi_cell(0, 4, 'PharmaGuard AI - Explainable AI for Molecular Toxicity Prediction\nSIH 2026 | Defense-grade AI for molecular safety assessment.')
    
    # Output to bytes
    return pdf.output(dest=bytearray())


def _build_html_report(results: Dict[str, Any]) -> str:
    """Build HTML string for PDF generation."""
    
    summary = results.get('summary', {})
    predictions = results.get('predictions', {})
    
    # Build endpoint rows
    endpoint_rows = ""
    for endpoint, pred in predictions.items():
        if isinstance(pred, dict) and 'probability' in pred:
            prob = pred['probability']
            is_toxic = prob > 0.5
            badge_class = 'badge-toxic' if is_toxic else 'badge-safe'
            badge_text = 'Toxic' if is_toxic else 'Safe'
            confidence = pred.get('confidence', 'Unknown')
            confidence_class = f'confidence-{confidence.lower()}' if confidence != 'Unknown' else ''
            
            endpoint_rows += f"""
            <tr>
                <td>{endpoint}</td>
                <td>{prob:.4f}</td>
                <td><span class="badge {badge_class}">{badge_text}</span></td>
                <td class="{confidence_class}">{confidence}</td>
                <td>{pred.get('source', 'N/A')}</td>
            </tr>"""
    
    # Build model rows
    model_rows = """
        <tr><td>Attention-GIN</td><td>Tox21 (12 endpoints)</td><td>✅ Active (ROC-AUC 0.8368)</td></tr>
        <tr><td>XGBoost</td><td>NR endpoints (5)</td><td>✅ Active</td></tr>
        <tr><td>ChemBERTa</td><td>SMILES encoder (768-dim)</td><td>✅ Phase 3</td></tr>
        <tr><td>GPS Graph Transformer</td><td>Tox21 (ensemble)</td><td>✅ Phase 3</td></tr>
        <tr><td>TDC Models</td><td>hERG, DILI, Ames</td><td>⚠️ Placeholder</td></tr>"""
    
    # Build explanation section if available
    explanation_section = ""
    if 'explanation' in results:
        explanation = results['explanation']
        explanation_section = f"""
        <div class="section">
            <h2>6. Explanation &amp; Rationale</h2>
            <div class="metric-card">
                <div class="metric-label">LLM Explanation</div>
                <div class="metric-value" style="white-space: pre-wrap; font-size: 11px;">{explanation}</div>
            </div>
        </div>
        """
    
    # Calculate toxicity bar position
    toxicity_pct = int(summary.get('average_toxicity_probability', 0.5) * 100)
    
    html = HTML_TEMPLATE.format(
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        smiles=results.get('smiles', 'N/A'),
        assessment=summary.get('overall_assessment', 'Unknown'),
        toxicity_pct=toxicity_pct,
        mean_toxicity=f"{summary.get('average_toxicity_probability', 0.5):.4f}",
        ci_low=f"{summary.get('toxicity_ci_low', 0.5):.4f}",
        ci_high=f"{summary.get('toxicity_ci_high', 0.5):.4f}",
        endpoint_rows=endpoint_rows,
        model_rows=model_rows,
        explanation_section=explanation_section,
        num_endpoints=summary.get('num_endpoints', 'N/A'),
        toxic_endpoints=summary.get('toxic_endpoints', 'N/A'),
        ood_score=f"{results.get('ood_score', 'N/A')}",
        faithfulness_score=f"{results.get('faithfulness', {}).get('faithfulness_score', 'N/A')}"
    )
    
    return html


def save_report(results: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Generate and save a PDF report.
    
    Args:
        results: Analysis results dictionary
        output_path: Optional path to save. If None, creates temp file.
    
    Returns:
        Path to the saved PDF file
    """
    if output_path is None:
        output_path = os.path.join(tempfile.gettempdir(), f"pharmaguard_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
    
    pdf_bytes = generate_pdf_report(results)
    
    with open(output_path, 'wb') as f:
        f.write(pdf_bytes)
    
    print(f"✅ PDF report saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # Test with sample results
    sample_results = {
        'smiles': 'Cn1cnc2c1c(=O)n(c(=O)n2C)C',
        'summary': {
            'average_toxicity_probability': 0.6842,
            'toxicity_ci_low': 0.6512,
            'toxicity_ci_high': 0.7183,
            'toxicity_std': 0.0341,
            'num_endpoints': 12,
            'toxic_endpoints': 8,
            'overall_assessment': 'HIGH TOXICITY ⚠️'
        },
        'predictions': {
            'NR-AR': {'probability': 0.72, 'prediction': 'Toxic', 'confidence': 'High', 'source': 'Attention-GIN'},
            'NR-AhR': {'probability': 0.68, 'prediction': 'Toxic', 'confidence': 'Medium', 'source': 'XGBoost'},
            'SR-MMP': {'probability': 0.35, 'prediction': 'Non-toxic', 'confidence': 'Low', 'source': 'Attention-GIN'},
        },
        'ood_score': 0.18,
        'faithfulness': {'faithfulness_score': 0.82},
        'explanation': 'The molecule shows high toxicity probability across multiple nuclear receptors.'
    }
    
    try:
        path = save_report(sample_results)
        print(f"Report generated: {path}")
    except Exception as e:
        print(f"Error generating report: {e}")