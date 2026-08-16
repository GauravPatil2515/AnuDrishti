import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import { clsx } from 'clsx';
import {
  BeakerIcon, PhotoIcon, ArrowUpTrayIcon, SparklesIcon,
  MagnifyingGlassIcon, ChatBubbleLeftRightIcon, CpuChipIcon
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
  const [mode, setMode] = useState('single'); // single | batch | whatif | lookup | nl
  const [smiles, setSmiles] = useState('');
  const [batchText, setBatchText] = useState('');
  const [error, setError] = useState('');
  const [compoundName, setCompoundName] = useState('');
  const [lookupResult, setLookupResult] = useState(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState('');
  const [nlQuery, setNlQuery] = useState('');
  const [nlResult, setNlResult] = useState(null);
  const [nlLoading, setNlLoading] = useState(false);
  const [modelList, setModelList] = useState(null);
  const [modelLoading, setModelLoading] = useState(false);

  const handlePreset = (preset) => {
    setSmiles(preset.smiles);
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

  const handleLookup = async () => {
    if (!compoundName.trim()) return setLookupError('Please enter a compound name.');

    setLookupLoading(true);
    setLookupError('');
    setLookupResult(null);

    try {
      const res = await api.post('/api/lookup/smiles', { name: compoundName.trim() });
      setLookupResult(res.data);
      if (res.data.success && res.data.canonical_smiles) {
        setSmiles(res.data.canonical_smiles);
        setMode('single');
        setLookupResult({ ...res.data, selected: true });
      }
    } catch (e) {
      setLookupError(e.response?.data?.error || 'Lookup failed.');
    } finally {
      setLookupLoading(false);
    }
  };

  // Heuristic: treat the input as a SMILES if it contains typical SMILES
  // characters; otherwise assume it is a plain compound / drug name.
  const looksLikeSmiles = (s) => /[()\[\]=#@\/\.0-9]/.test(s) || s.includes('C') || s.includes('c');

  const runAnalysis = (input) => {
    const value = input.trim();
    if (!value) return setError('Type a drug name (e.g. Aspirin) or a SMILES string.');
    if (looksLikeSmiles(value)) {
      setSmiles(value);
      onAnalyze({ mode: 'single', smiles: value });
    } else {
      // Treat as a compound name → look it up, then analyse the resolved SMILES.
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

  const handleNlQuery = async () => {
    setNlLoading(true);
    setError('');
    try {
      const res = await api.post('/api/query', { query: nlQuery });
      setNlResult(res.data);
      if (res.data.entities && res.data.entities.length > 0 && res.data.intent === 'safety') {
        setSmiles(res.data.entities[0]);
        setMode('single');
      }
    } catch (e) {
      setError(e.response?.data?.error || 'Query failed.');
    } finally {
      setNlLoading(false);
    }
  };

  const fetchModelList = async () => {
    setModelLoading(true);
    try {
      const res = await api.get('/api/models');
      setModelList(res.data);
    } catch (e) {
      console.error('Model list fetch failed:', e);
    } finally {
      setModelLoading(false);
    }
  };

  // Auto-fetch models on mount
  useEffect(() => {
    fetchModelList();
  }, []);

  return (
    <div className="space-y-4">
      <div className="grid gap-4 lg:grid-cols-3">
        {/* Input column */}
        <div className="lg:col-span-2 space-y-4">
      {/* Simple unified input: drug name OR SMILES */}
      <div className="surface-elevated rounded-lg p-4">
        <label className="mb-2 block text-sm font-semibold text-primary">
          Enter a drug name or a molecule
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
            placeholder="e.g. Aspirin  —  or paste a SMILES like CC(=O)OC1=CC=CC=C1C(=O)O"
            className="input flex-1 text-sm"
          />
          <button
            onClick={handleSubmit}
            disabled={isLoading}
            className="btn btn-primary px-5 text-sm"
          >
            {isLoading ? 'Analyzing…' : 'Analyze'}
            <BeakerIcon className="h-4 w-4 ml-1" />
          </button>
        </div>

        {/* Preset chips */}
        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          <span className="text-xs text-muted">Try:</span>
          {PRESETS.map((p) => (
            <button
              key={p.name}
              onClick={() => handlePreset(p)}
              className="pill pill-gray text-[11px] hover:bg-surface-hover transition-colors"
            >
              {p.name}
            </button>
          ))}
        </div>

        {(error || lookupError) && (
          <p className="mt-2 text-xs text-red-400">{error || lookupError}</p>
        )}

        {/* Advanced modes */}
        <div className="mt-3 flex flex-wrap gap-2 border-t border-border pt-3">
          <button
            onClick={() => setMode(mode === 'batch' ? 'single' : 'batch')}
            className={clsx(
              'text-xs font-medium rounded-md px-2.5 py-1 transition-colors',
              mode === 'batch' ? 'bg-surface-hover text-primary' : 'text-muted hover:text-secondary'
            )}
          >
            {mode === 'batch' ? '✓ Screening a list' : '+ Screen a list (batch)'}
          </button>
          <button
            onClick={() => setMode(mode === 'whatif' ? 'single' : 'whatif')}
            className={clsx(
              'text-xs font-medium rounded-md px-2.5 py-1 transition-colors',
              mode === 'whatif' ? 'bg-surface-hover text-primary' : 'text-muted hover:text-secondary'
            )}
          >
            {mode === 'whatif' ? '✓ What-If optimizer' : '+ What-If optimization'}
          </button>
        </div>

        {/* Batch input */}
        {mode === 'batch' && (
          <div className="mt-3 space-y-2">
            <textarea
              value={batchText}
              onChange={(e) => setBatchText(e.target.value)}
              rows={5}
              placeholder={'Paste SMILES, one per line\nCCO\nCC(=O)OC1=CC=CC=C1C(=O)O'}
              className="textarea text-xs"
            />
            <label className="flex cursor-pointer items-center gap-2 rounded-md border border-dashed border-border bg-surface px-3 py-2 text-sm text-secondary hover:border-border-hover hover:bg-surface-hover transition-colors">
              <PhotoIcon className="h-4 w-4 text-indigo-400" />
              Upload CSV / SMILES file
              <input type="file" accept=".csv,.smi,.txt,.sdf" className="hidden" onChange={handleFileUpload} />
            </label>
          </div>
        )}

        {/* What-If input note */}
        {mode === 'whatif' && (
          <p className="mt-3 text-xs text-muted">
            Type a SMILES above, then Analyze to generate safer bioisosteric variants.
          </p>
        )}
      </div>

          {/* Lookup result */}
          {lookupResult && lookupResult.success && !lookupLoading && (
            <div className="rounded-lg border border-indigo-500/30 bg-indigo-500/5 p-4">
              <h4 className="mb-2 text-xs font-bold text-indigo-400">Lookup Result</h4>
              <div className="space-y-1 text-xs">
                <p className="font-medium">Compound: <span className="font-mono text-white/60">{lookupResult.name}</span></p>
                <p className="font-medium">CID: <span className="font-mono text-white/60">{lookupResult.cid}</span></p>
                <p className="font-medium">Formula: <span className="font-mono text-white/60">{lookupResult.molecular_formula}</span></p>
                <p className="font-medium">Weight: <span className="font-mono text-white/60">{lookupResult.molecular_weight}</span></p>
                <p className="font-medium">IUPAC: <span className="font-mono text-white/60 break-all">{lookupResult.iupac_name}</span></p>
                <p className="font-medium">SMILES:
                  <span className="font-mono text-white/60 break-all bg-surface px-1.5 py-0.5 rounded ml-1">
                    {lookupResult.canonical_smiles}
                  </span>
                </p>
                {lookupResult.selected && (
                  <p className="mt-1 text-xs text-indigo-400">
                    ✓ Selected for analysis — switch to Single Molecule mode to run
                  </p>
                )}
              </div>
            </div>
          )}

          {/* NL query result */}
          {nlResult && (
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
              <h4 className="mb-2 text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                <ChatBubbleLeftRightIcon className="h-4 w-4" />
                NL Query Response
              </h4>
              <div className="space-y-1 text-xs">
                <p><span className="font-medium text-white/60">Intent:</span> <span className="font-mono text-white/60 capitalize">{nlResult.intent}</span></p>
                <p><span className="font-medium text-white/60">Response:</span> <span className="text-white/60">{nlResult.response}</span></p>
                {nlResult.entities && nlResult.entities.length > 0 && (
                  <p><span className="font-medium text-white/60">Molecules:</span> <span className="font-mono text-white/60">{nlResult.entities.join(', ')}</span></p>
                )}
                {nlResult.intent === 'unknown' && nlResult.suggestions && (
                  <div className="mt-2">
                    <p className="font-medium text-xs text-emerald-400/60 mb-1">Try these:</p>
                    <div className="flex flex-wrap gap-1">
                      {nlResult.suggestions.slice(0, 5).map((s, i) => (
                        <button
                          key={i}
                          onClick={() => { setNlQuery(s); handleNlQuery(); }}
                          className="text-xs px-2 py-1 rounded bg-surface hover:bg-surface-hover text-white/60 transition"
                        >
                          {s}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Presets + Model ensemble column */}
        <div className="space-y-4">
          {/* Presets */}
          <div className="surface-elevated rounded-lg p-4">
            <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-muted">Quick Presets</h3>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th className="w-8">#</th>
                    <th>Compound</th>
                    <th className="w-20">Class</th>
                    <th className="w-28">Risk</th>
                    <th className="w-16"></th>
                  </tr>
                </thead>
                <tbody>
                  {PRESETS.map((p, i) => (
                    <tr key={p.name}>
                      <td className="text-muted">{i + 1}</td>
                      <td className="font-mono text-xs text-secondary">{p.name}</td>
                      <td>
                        <span className={clsx('pill text-[9px]',
                          p.type === 'toxic' ? 'pill-red' : 'pill-green'
                        )}>
                          {p.type === 'toxic' ? 'Toxic' : 'Safe'}
                        </span>
                      </td>
                      <td>
                        <span className={clsx('font-mono font-bold text-xs',
                          p.type === 'toxic' ? 'text-red-400' : 'text-emerald-400'
                        )}>
                          {p.type === 'toxic' ? '● High' : '● Low'}
                        </span>
                      </td>
                      <td>
                        <button
                          onClick={() => handlePreset(p)}
                          className="p-1 rounded hover:bg-surface text-muted transition-colors"
                          title="Select"
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

          {/* Model ensemble */}
          {modelList && (
            <div className="surface-elevated rounded-lg p-4">
              <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-muted flex items-center gap-1.5">
                <CpuChipIcon className="h-4 w-4" />
                Model Ensemble ({modelList.active_models}/{modelList.total_models} active)
              </h3>
              <div className="space-y-1.5 text-xs">
                {modelList.models.map((m, i) => (
                  <div key={i} className="flex items-center justify-between p-1.5 rounded-md hover:bg-surface-hover transition-colors">
                    <div className="flex items-center gap-1.5">
                      <span className={clsx(
                        'w-1.5 h-1.5 rounded-full',
                        m.status === 'active' ? 'bg-emerald-400' :
                        m.status === 'placeholder' ? 'bg-amber-400' :
                        'bg-white/20'
                      )} />
                      <span className="text-white/60">{m.name}</span>
                      {m.phase && <span className="px-1 py-0.25 rounded text-[9px] bg-indigo-500/10 text-indigo-400">P{m.phase}</span>}
                    </div>
                    <span className="text-white/40">{m.role}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Info card */}
          <div className="surface-elevated rounded-lg p-4">
            <h3 className="mb-1.5 text-xs font-bold uppercase tracking-wider text-muted">Why PharmaGuard?</h3>
            <p className="text-xs text-secondary">
              Every prediction is paired with model-derived evidence, an uncertainty / OOD
              estimate, and a faithfulness-verified explanation. Unsupported claims are
              rejected — not silently shown.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MolecularInput;