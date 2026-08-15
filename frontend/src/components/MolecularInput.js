import React, { useState } from 'react';
import axios from 'axios';
import { clsx } from 'clsx';
import { BeakerIcon, PhotoIcon, ArrowUpTrayIcon, SparklesIcon, MagnifyingGlassIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

const PRESETS = [
  { name: 'Aspirin', smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O', type: 'safe' },
  { name: 'Acetaminophen', smiles: 'CC(=O)NC1=CC=C(C=C1)O', type: 'safe' },
  { name: 'Thalidomide', smiles: 'O=C1NC(=O)C(N2C(=O)c3ccccc3C2=O)CC1', type: 'toxic' },
  { name: 'Clozapine', smiles: 'CN1CCN(CC1)C1=NC2=CC=CC=C2N1C', type: 'toxic' },
  { name: 'Nicotine', smiles: 'CN1CCCC1C2=CN=CC=C2', type: 'safe' },
  { name: 'Benzene', smiles: 'C1=CC=CC=C1', type: 'toxic' },
];

const MolecularInput = ({ onAnalyze, isLoading }) => {
  const [mode, setMode] = useState('single'); // single | batch | whatif | lookup
  const [smiles, setSmiles] = useState('');
  const [batchText, setBatchText] = useState('');
  const [imagePreview, setImagePreview] = useState(null);
  const [error, setError] = useState('');
  const [compoundName, setCompoundName] = useState('');
  const [lookupResult, setLookupResult] = useState(null);
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupError, setLookupError] = useState('');

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
      // Accept .smi/.txt/.csv: one SMILES per line (optionally after a comma)
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
      const res = await axios.post('/api/lookup/smiles', { name: compoundName.trim() });
      setLookupResult(res.data);
      // If we found a SMILES, ask if user wants to use it
      if (res.data.success && res.data.canonical_smiles) {
        setSmiles(res.data.canonical_smiles);
        setMode('single');  // Switch to single mode to analyze
        setLookupResult({ ...res.data, selected: true });
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
      if (!smiles.trim()) return setError('Please enter a SMILES string.');
      onAnalyze({ mode: 'single', smiles: smiles.trim() });
    } else if (mode === 'batch') {
      const list = batchText
        .split(/\r?\n/)
        .map((l) => l.trim())
        .filter(Boolean);
      if (list.length === 0) return setError('Upload or paste at least one SMILES.');
      if (list.length > 1000) return setError('Maximum 1000 molecules per batch.');
      onAnalyze({ mode: 'batch', smiles_list: list });
    } else if (mode === 'whatif') {
      if (!smiles.trim()) return setError('Enter a SMILES for what-if optimization.');
      onAnalyze({ mode: 'whatif', smiles: smiles.trim() });
    } else if (mode === 'lookup') {
      // Just run the lookup
      handleLookup();
    }
  };

  return (
    <div className="space-y-6">
      {/* Mode selector */}
      <div className="flex flex-wrap gap-2">
        {[
          { id: 'single', label: 'Mode A · Single Molecule', icon: BeakerIcon },
          { id: 'batch', label: 'Mode B · Library Screening', icon: ArrowUpTrayIcon },
          { id: 'whatif', label: 'Mode C · What-If Optimization', icon: SparklesIcon },
          { id: 'lookup', label: 'Mode D · Name → SMILES Lookup', icon: MagnifyingGlassIcon },
        ].map((m) => (
          <button
            key={m.id}
            onClick={() => setMode(m.id)}
            className={clsx(
              'flex items-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition',
              mode === m.id
                ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
                : 'bg-white text-slate-600 border border-slate-200 hover:border-indigo-300'
            )}
          >
            <m.icon className="h-5 w-5" />
            {m.label}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Input column */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">
            {mode === 'batch' ? 'Molecular Library (CSV / SMI / SDF)' : 
              mode === 'lookup' ? 'Compound Name → SMILES Lookup' : 
              'Molecular Structure (SMILES)'}
          </h3>

          {mode !== 'batch' && mode !== 'lookup' ? (
            <textarea
              value={smiles}
              onChange={(e) => setSmiles(e.target.value)}
              rows={3}
              placeholder="e.g. CC(=O)OC1=CC=CC=C1C(=O)O"
              className="w-full rounded-xl border border-slate-300 p-3 font-mono text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
            />
          ) : mode === 'lookup' ? (
            <div className="space-y-3">
              <input
                type="text"
                value={compoundName}
                onChange={(e) => setCompoundName(e.target.value)}
                placeholder="e.g. Aspirin, Paracetamol, Benzene"
                className="w-full rounded-xl border border-slate-300 p-3 text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
              />
              <div className="flex gap-2">
                <button
                  onClick={handleLookup}
                  disabled={lookupLoading}
                  className="w-full rounded-xl bg-indigo-600 py-2 text-sm font-bold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700 disabled:opacity-60"
                >
                  {lookupLoading ? 'Looking up…' : 'Lookup Compound'}
                  <MagnifyingGlassIcon className="h-4 w-4 ml-2 inline" />
                </button>
              </div>
              {lookupError && <p className="mt-2 text-sm text-red-600">{lookupError}</p>}
            </div>
          ) : (
            <div className="space-y-3">
              <textarea
                value={batchText}
                onChange={(e) => setBatchText(e.target.value)}
                rows={8}
                placeholder={'Paste SMILES, one per line\nCCO\nCC(=O)OC1=CC=CC=C1C(=O)O\n...'}
                className="w-full rounded-xl border border-slate-300 p-3 font-mono text-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-200"
              />
              <label className="flex cursor-pointer items-center gap-2 rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-3 text-sm text-slate-600 hover:border-indigo-400">
                <PhotoIcon className="h-5 w-5 text-indigo-500" />
                Upload CSV / SMILES file
                <input type="file" accept=".csv,.smi,.txt,.sdf" className="hidden" onChange={handleFileUpload} />
              </label>
            </div>
          )}

          {error && <p className="mt-2 text-sm text-red-600">{error}</p>}

          <button
            onClick={handleSubmit}
            disabled={isLoading || (mode === 'lookup' && lookupLoading)}
            className="mt-4 w-full rounded-xl bg-indigo-600 py-3 text-sm font-bold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700 disabled:opacity-60"
          >
            {isLoading || (mode === 'lookup' && lookupLoading) ? 'Processing…' : 'Run PharmaGuard Analysis'}
          </button>
        </div>

        {/* Presets + preview column */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">Quick Presets</h3>
          <div className="grid grid-cols-2 gap-2">
            {PRESETS.map((p) => (
              <button
                key={p.name}
                onClick={() => handlePreset(p)}
                className={clsx(
                  'rounded-xl border px-3 py-2 text-left text-sm font-medium transition',
                  p.type === 'toxic'
                    ? 'border-red-200 bg-red-50 text-red-700 hover:bg-red-100'
                    : 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                )}
              >
                {p.name}
              </button>
            ))}
          </div>

          {lookupResult && lookupResult.success && !lookupLoading && (
            <div className="mt-4 rounded-xl border border-indigo-200 bg-indigo-50 p-4">
              <h4 className="mb-2 text-sm font-bold text-indigo-700">Lookup Result</h4>
              <div className="space-y-2 text-sm">
                <p className="font-medium">Compound: <span className="font-bold">{lookupResult.name}</span></p>
                <p className="font-medium">CID: <span className="font-mono">{lookupResult.cid}</span></p>
                <p className="font-medium">Formula: <span className="font-mono">{lookupResult.molecular_formula}</span></p>
                <p className="font-medium">Weight: <span className="font-mono">{lookupResult.molecular_weight}</span></p>
                <p className="font-medium">IUPAC: <span className="font-mono">{lookupResult.iupac_name}</span></p>
                <p className="font-medium">SMILES: 
                  <span className="font-mono break-all bg-slate-50 px-2 py-1 rounded">
                    {lookupResult.canonical_smiles}
                  </span>
                </p>
                {lookupResult.selected && (
                  <p className="mt-2 text-xs text-indigo-600">
                    ✓ Selected for analysis - switch to Single Molecule mode to run
                  </p>
                )}
              </div>
            </div>
          )}
          
          <div className="mt-4 rounded-xl bg-slate-50 p-3 text-xs text-slate-500">
            <p className="font-semibold text-slate-600">Why PharmaGuard?</p>
            <p className="mt-1">
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
