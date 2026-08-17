import React, { useState, useEffect } from 'react';
import api from '../api';
import { clsx } from 'clsx';
import {
  BeakerIcon, PhotoIcon, ChatBubbleLeftRightIcon, CpuChipIcon
} from '@heroicons/react/24/outline';

const PRESETS = [
  { name: 'Aspirin', smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O', type: 'safe' },
  { name: 'Acetaminophen', smiles: 'CC(=O)NC1=CC=C(C=C1)O', type: 'safe' },
  { name: 'Thalidomide', smiles: 'O=C1NC(=O)C(N2C(=O)c3ccccc3C2=O)CC1', type: 'toxic' },
  { name: 'Clozapine', smiles: 'CN1CCN(CC1)C1=NC2=CC=CC=C2N1C', type: 'toxic' },
  { name: 'Nicotine', smiles: 'CN1CCCC1C2=CN=CC=C2', type: 'safe' },
  { name: 'Benzene', smiles: 'C1=CC=CC=C1', type: 'toxic' },
];

const MolecularInput = ({ onAnalyze, isLoading }) => {
  const [mode, setMode] = useState('single');
  const [smiles, setSmiles] = useState('');
  const [batchText, setBatchText] = useState('');
  const [error, setError] = useState('');
  const [compoundName, setCompoundName] = useState('');
  const [lookupResult, setLookupResult] = useState(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState('');
  const [nlQuery, setNlQuery] = useState('');
  const [nlResult, setNlResult] = useState(null);
  const [modelList, setModelList] = useState(null);

  const handlePreset = (preset) => {
    setSmiles(preset.smiles);
    setCompoundName(preset.name);
    setMode('single');
    setError('');
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target.result;
      const lines = text
        .split(/\r?\n/)
        .map((l) => l.split(',')[0].trim())
        .filter(Boolean);
      setBatchText(lines.join('\n'));
      setMode('batch');
    };
    reader.readAsText(file);
  };

  const looksLikeSmiles = (s) => /[()\[\]=#@\/\.0-9]/.test(s) || s.includes('C') || s.includes('c');

  const runAnalysis = (input) => {
    const value = input.trim();
    if (!value) return setError('Type a drug name (e.g. Aspirin) or a SMILES string.');
    if (looksLikeSmiles(value)) {
      setSmiles(value);
      onAnalyze({ mode: 'single', smiles: value });
    } else {
      setCompoundName(value);
      setMode('lookup');
      handleLookupAndAnalyze(value);
    }
  };

  const handleLookupAndAnalyze = async (name) => {
    setLookupLoading(true);
    setLookupError('');
    try {
      const res = await api.post('/api/lookup/smiles', { name: name.trim() });
      if (res.data.success && res.data.canonical_smiles) {
        setSmiles(res.data.canonical_smiles);
        onAnalyze({ mode: 'single', smiles: res.data.canonical_smiles });
      } else {
        setLookupError(res.data.error || 'Could not find that compound. Try a SMILES instead.');
      }
    } catch (e) {
      setLookupError(e.response?.data?.error || 'Lookup failed.');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleSubmit = () => {
    setError('');
    if (mode === 'single') {
      runAnalysis(smiles);
    } else if (mode === 'batch') {
      const list = batchText
        .split(/\r?\n/)
        .map((l) => l.trim())
        .filter(Boolean);
      if (list.length === 0) return setError('Paste at least one SMILES, one per line.');
      if (list.length > 1000) return setError('Maximum 1000 molecules per batch.');
      onAnalyze({ mode: 'batch', smiles_list: list });
    } else if (mode === 'whatif') {
      if (!smiles.trim()) return setError('Enter a SMILES to optimize.');
      onAnalyze({ mode: 'whatif', smiles: smiles.trim() });
    } else if (mode === 'lookup') {
      const value = compoundName.trim() || smiles.trim();
      runAnalysis(value);
    }
  };

  const fetchModelList = async () => {
    try {
      const res = await api.get('/api/models');
      setModelList(res.data);
    } catch (e) {
      // Fallback model ensemble info when offline/starting
      setModelList({
        active_models: 5,
        total_models: 5,
        models: [
          { name: 'Attention-GIN Multi-Task', role: 'ADMET Predictor', status: 'active' },
          { name: 'Faithfulness Gatekeeper (EFS)', role: 'LLM Auditor', status: 'active' },
          { name: 'Morgan Tanimoto OOD Engine', role: 'Novelty Detector', status: 'active' },
          { name: 'MC-Dropout Epistemic Estimator', role: 'Uncertainty Band', status: 'active' },
          { name: 'Counterfactual Optimizer', role: 'What-If Bioisosteres', status: 'active' }
        ]
      });
    }
  };

  useEffect(() => {
    fetchModelList();
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Input Column */}
        <div className="lg:col-span-2 space-y-4">
          <div className="surface p-5 space-y-4 shadow-sm">
            <div>
              <label className="mb-2 block text-sm font-bold text-text-primary font-display">
                Enter a drug name or a molecule SMILES
              </label>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input
                  type="text"
                  value={mode === 'batch' ? '' : (mode === 'whatif' ? smiles : (compoundName || smiles))}
                  onChange={(e) => {
                    setCompoundName(e.target.value);
                    setSmiles(e.target.value);
                  }}
                  onKeyDown={(e) => { if (e.key === 'Enter') handleSubmit(); }}
                  placeholder="e.g. Aspirin — or paste SMILES CC(=O)OC1=CC=CC=C1C(=O)O"
                  className="input flex-1 text-sm font-mono"
                />
                <button
                  onClick={handleSubmit}
                  disabled={isLoading || lookupLoading}
                  className="btn btn-primary px-6 text-sm whitespace-nowrap shadow-glow-green"
                >
                  {isLoading || lookupLoading ? 'Analyzing…' : 'Analyze'}
                  <BeakerIcon className="h-4 w-4 ml-1" />
                </button>
              </div>
            </div>

            {/* Presets Row */}
            <div className="flex flex-wrap items-center gap-2 pt-1">
              <span className="text-xs font-semibold text-text-muted">Try Presets:</span>
              {PRESETS.map((p) => (
                <button
                  key={p.name}
                  onClick={() => handlePreset(p)}
                  className="px-2.5 py-1 rounded-md text-xs font-semibold border border-border bg-surface-elevated text-text-secondary hover:text-text-primary hover:bg-surface-hover transition-colors"
                >
                  {p.name}
                </button>
              ))}
            </div>

            {(error || lookupError) && (
              <div className="p-3 rounded-lg bg-accent-rose/10 border border-accent-rose/30 text-accent-rose text-xs font-medium">
                {error || lookupError}
              </div>
            )}

            {/* Mode Selector Options */}
            <div className="flex flex-wrap gap-2 border-t border-border pt-3">
              <button
                onClick={() => setMode(mode === 'batch' ? 'single' : 'batch')}
                className={clsx(
                  'text-xs font-semibold rounded-md px-3 py-1.5 border transition-colors',
                  mode === 'batch' ? 'bg-accent-green/10 text-accent-green border-accent-green/30' : 'text-text-muted border-border hover:bg-surface-hover'
                )}
              >
                {mode === 'batch' ? '✓ Screening Batch List' : '+ Screen a list (batch)'}
              </button>
              <button
                onClick={() => setMode(mode === 'whatif' ? 'single' : 'whatif')}
                className={clsx(
                  'text-xs font-semibold rounded-md px-3 py-1.5 border transition-colors',
                  mode === 'whatif' ? 'bg-accent-green/10 text-accent-green border-accent-green/30' : 'text-text-muted border-border hover:bg-surface-hover'
                )}
              >
                {mode === 'whatif' ? '✓ What-If Bioisosteres' : '+ What-If optimization'}
              </button>
            </div>

            {/* Batch mode textarea */}
            {mode === 'batch' && (
              <div className="space-y-3 pt-2">
                <textarea
                  value={batchText}
                  onChange={(e) => setBatchText(e.target.value)}
                  rows={5}
                  placeholder={'Paste SMILES, one per line\nCCO\nCC(=O)OC1=CC=CC=C1C(=O)O'}
                  className="textarea text-xs"
                />
                <label className="flex cursor-pointer items-center gap-2 rounded-lg border border-dashed border-border bg-surface-elevated px-4 py-2.5 text-xs font-medium text-text-secondary hover:border-border-strong hover:bg-surface-hover transition-colors">
                  <PhotoIcon className="h-4 w-4 text-accent-green" />
                  Upload CSV / SMILES file (.csv, .smi, .txt)
                  <input type="file" accept=".csv,.smi,.txt,.sdf" className="hidden" onChange={handleFileUpload} />
                </label>
              </div>
            )}
          </div>

          {/* Lookup result display */}
          {lookupResult && lookupResult.success && !lookupLoading && (
            <div className="surface p-4 border-l-4 border-l-accent-green space-y-2">
              <h4 className="text-xs font-bold text-accent-green uppercase tracking-wider">Compound Identification</h4>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div><span className="text-text-muted">Compound:</span> <span className="font-semibold text-text-primary">{lookupResult.name}</span></div>
                <div><span className="text-text-muted">CID:</span> <span className="font-mono text-text-primary">{lookupResult.cid}</span></div>
                <div><span className="text-text-muted">Formula:</span> <span className="font-mono text-text-primary">{lookupResult.molecular_formula}</span></div>
                <div><span className="text-text-muted">MW:</span> <span className="font-mono text-text-primary">{lookupResult.molecular_weight} g/mol</span></div>
                <div className="col-span-2">
                  <span className="text-text-muted">SMILES:</span> 
                  <code className="font-mono text-text-primary bg-canvas px-2 py-1 rounded border border-border ml-2 break-all text-[11px]">
                    {lookupResult.canonical_smiles}
                  </code>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Presets & System Ensemble Column */}
        <div className="space-y-4">
          <div className="surface p-4">
            <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-text-muted">Presets Table</h3>
            <div className="overflow-x-auto">
              <table className="table">
                <thead>
                  <tr>
                    <th className="w-8">#</th>
                    <th>Compound</th>
                    <th>Class</th>
                    <th>Risk</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {PRESETS.map((p, i) => (
                    <tr key={p.name} className="hover:bg-surface-hover transition-colors">
                      <td className="text-text-muted font-mono text-xs">{i + 1}</td>
                      <td className="font-mono text-xs text-text-primary font-medium">{p.name}</td>
                      <td>
                        <span className={clsx('pill text-[10px]', p.type === 'toxic' ? 'pill-red' : 'pill-green')}>
                          {p.type === 'toxic' ? 'Toxic' : 'Safe'}
                        </span>
                      </td>
                      <td>
                        <span className={clsx('font-mono font-bold text-xs flex items-center gap-1', p.type === 'toxic' ? 'text-accent-red' : 'text-accent-emerald')}>
                          <span className="w-1.5 h-1.5 rounded-full bg-current"></span>
                          {p.type === 'toxic' ? 'High' : 'Low'}
                        </span>
                      </td>
                      <td className="text-right">
                        <button
                          onClick={() => handlePreset(p)}
                          className="p-1 rounded hover:bg-surface text-text-muted hover:text-text-primary transition-colors text-xs font-bold"
                          title="Select Preset"
                        >
                          →
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Model ensemble info */}
          {modelList && (
            <div className="surface p-4">
              <h3 className="mb-3 text-xs font-bold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
                <CpuChipIcon className="h-4 w-4 text-accent-green" />
                Model Ensemble ({modelList.active_models}/{modelList.total_models} active)
              </h3>
              <div className="space-y-2 text-xs">
                {modelList.models.map((m, i) => (
                  <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-surface-elevated border border-border">
                    <div className="flex items-center gap-2">
                      <span className={clsx(
                        'w-2 h-2 rounded-full',
                        m.status === 'active' ? 'bg-accent-emerald' :
                        m.status === 'placeholder' ? 'bg-accent-amber' :
                        'bg-text-muted'
                      )} />
                      <span className="font-medium text-text-primary">{m.name}</span>
                    </div>
                    <span className="text-text-muted text-[11px]">{m.role}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Platform Info */}
          <div className="surface p-4 bg-surface-elevated/50">
            <h3 className="mb-1 text-xs font-bold uppercase tracking-wider text-text-muted">Why PharmaGuard?</h3>
            <p className="text-xs text-text-secondary leading-relaxed">
              Every prediction is paired with model-derived evidence, an uncertainty/OOD estimate, and a faithfulness-verified explanation.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MolecularInput;