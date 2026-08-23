import sys
sys.path.insert(0, '.')

from services.report_generator import generate_pdf_report

# Sample analysis results (mimicking what _build_pharmaguard_analysis returns)
sample_results = {
    'smiles': 'Cn1cnc2c1c(=O)n(c(=O)n2C)C',  # caffeine
    'summary': {
        'average_toxicity_probability': 0.15,
        'toxicity_ci_low': 0.10,
        'toxicity_ci_high': 0.20,
        'toxicity_std': 0.05,
        'num_endpoints': 12,
        'toxic_endpoints': 2,
        'overall_assessment': 'VERY LOW TOXICITY ✅'
    },
    'predictions': {
        'NR-AR': {'probability': 0.12, 'prediction': 'Non-toxic', 'confidence': 'High', 'source': 'Attention-GIN'},
        'NR-AhR': {'probability': 0.18, 'prediction': 'Non-toxic', 'confidence': 'Medium', 'source': 'Attention-GIN'},
        'SR-MMP': {'probability': 0.08, 'prediction': 'Non-toxic', 'confidence': 'Low', 'source': 'Attention-GIN'},
        # Add a few more to have a table
        'SR-ARE': {'probability': 0.22, 'prediction': 'Non-toxic', 'confidence': 'Medium', 'source': 'Attention-GIN'},
        'SR-ATAD5': {'probability': 0.15, 'prediction': 'Non-toxic', 'confidence': 'Low', 'source': 'Attention-GIN'},
        'SR-HSE': {'probability': 0.10, 'prediction': 'Non-toxic', 'confidence': 'Low', 'source': 'Attention-GIN'},
        'SR-MMP': {'probability': 0.08, 'prediction': 'Non-toxic', 'confidence': 'Low', 'source': 'Attention-GIN'},
        'SR-p53': {'probability': 0.05, 'prediction': 'Non-toxic', 'confidence': 'Low', 'source': 'Attention-GIN'},
    },
    'ood': {'is_ood': False, 'confidence_modifier': 0.95, 'nearest_neighbor_similarity': 0.91},
    'explanation': {
        'smiles': 'Cn1cnc2c1c(=O)n(c(=O)n2C)C',
        'prediction': 0.15,
        'executive_summary': 'Model predicts LOW overall toxicity risk (p=0.15). The highest-attention substructures are the phenol ring and the acetamide group, both well-characterised as low-risk in standard therapeutics.',
        'mechanism': 'Attention-weighted readout of the GNN concentrates on benign aromatic/amide features; no high-risk toxicophore is isolated.',
        'identified_toxicophores': [],
        'faithfulness_score': 0.92,
        'validation_passed': True,
        'rejection_reason': None,
        'llm_generated': False,
        'faithfulness_details': {'demo': True, 'note': 'Illustrative demo record — not a live model prediction.'}
    }
}

try:
    pdf_bytes = generate_pdf_report(sample_results)
    print(f'PDF generated successfully. Size: {len(pdf_bytes)} bytes')
    # Check that it starts with %PDF
    if pdf_bytes.startswith(b'%PDF'):
        print('PDF header is correct.')
    else:
        print('WARNING: PDF header not found. Output might not be a valid PDF.')
        print(f'First 20 bytes: {pdf_bytes[:20]}')
except Exception as e:
    print(f'Error generating PDF: {e}')
    import traceback
    traceback.print_exc()
