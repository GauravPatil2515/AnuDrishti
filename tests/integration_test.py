#!/usr/bin/env python3
"""
Integration tests for full API pipeline (requires running backend server).
Run with: python tests/integration_test.py  (server must be running)
"""
import requests

BASE = 'http://localhost:5000/api'

def test_health_check():
    r = requests.get(f'{BASE}/health')
    assert r.status_code == 200
    assert r.json()['predictor_loaded'] == True
    print('✅ Health check passed')

def test_demo_endpoint():
    r = requests.get(f'{BASE}/demo')
    assert r.status_code == 200
    data = r.json()
    assert data['success'] == True
    assert len(data['results']) == 2
    assert data['results'][0]['triage']['category'] == 'GREEN'
    assert data['results'][1]['triage']['category'] == 'RED'
    print('✅ Demo endpoint passed')

def test_smiles_lookup():
    r = requests.post(f'{BASE}/lookup/smiles', json={'name': 'Aspirin'})
    assert r.status_code == 200
    data = r.json()
    assert data['success'] == True
    print('✅ SMILES lookup passed')

def test_single_molecule_analysis():
    r = requests.post(f'{BASE}/analyze/single', json={'smiles': 'CC(=O)NC1=CC=C(C=C1)O', 'include_explanation': True})
    assert r.status_code == 200
    data = r.json()
    assert data['success'] == True
    assert 'analysis' in data
    assert 'toxicity_probability' in data['analysis']
    assert 'explanation' in data['analysis']
    assert 'faithfulness_score' in data['analysis']['explanation']
    assert 'triage' in data['analysis']
    assert 'ood' in data['analysis']
    print('✅ Single molecule analysis passed')

def test_ood_detection():
    r = requests.post(f'{BASE}/analyze/single', json={'smiles': 'O=[N+]([O-])c1ccccc1'})
    assert r.status_code == 200
    data = r.json()
    assert 'ood' in data['analysis']
    print('✅ OOD detection passed')

def test_faithfulness_verification():
    r = requests.post(f'{BASE}/explain/verify', json={'smiles': 'CC(=O)NC1=CC=C(C=C1)O', 'inject_hallucination': False})
    assert r.status_code == 200
    data = r.json()
    assert 'faithfulness' in data
    assert 'status' in data
    print('✅ Faithfulness verification passed')

def test_whatif_optimization():
    r = requests.post(f'{BASE}/optimize/what-if', json={'smiles': 'O=[N+]([O-])c1ccccc1', 'n_variants': 2})
    assert r.status_code == 200
    data = r.json()
    assert 'candidates' in data
    print('✅ What-if optimization passed')

def test_batch_analysis():
    r = requests.post(f'{BASE}/analyze/batch', json={'smiles_list': ['CCO', 'c1ccccc1'], 'include_explanation': False})
    assert r.status_code == 200
    data = r.json()
    assert data['total_processed'] == 2
    print('✅ Batch analysis passed')

def test_attention_heatmap():
    r = requests.post(f'{BASE}/visualize/attention-heatmap', json={'smiles': 'CC(=O)NC1=CC=C(C=C1)O'})
    assert r.status_code == 200
    data = r.json()
    assert 'svg' in data
    assert data['attention_source'] == 'gnn_attention'
    print('✅ Attention heatmap passed')

def test_report_export():
    r = requests.post(f'{BASE}/report/export', json={'smiles': 'CC(=O)NC1=CC=C(C=C1)O', 'format': 'json'})
    assert r.status_code == 200
    data = r.json()
    assert data['platform'] == 'PharmaGuard AI'
    print('✅ Report export passed')

if __name__ == '__main__':
    print('Running integration tests against http://localhost:5000...\n')
    test_health_check()
    test_demo_endpoint()
    test_smiles_lookup()
    test_single_molecule_analysis()
    test_ood_detection()
    test_faithfulness_verification()
    test_whatif_optimization()
    test_batch_analysis()
    test_attention_heatmap()
    test_report_export()
    print('\n🎉 ALL INTEGRATION TESTS PASSED!')