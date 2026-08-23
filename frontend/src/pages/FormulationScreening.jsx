import React, { useState } from 'react';
import { PlusIcon, TrashIcon, PlayIcon, BeakerIcon, ExclamationTriangleIcon, CheckCircleIcon } from '@heroicons/react/24/outline';
import api from '../api';
import toast from 'react-hot-toast';

// Preset formulations for one-click testing
const PRESETS = [
  {
    label: 'Paracetamol Tablet (Safe)',
    components: [
      { name: 'Paracetamol', smiles: 'CC(=O)Nc1ccc(O)cc1', role: 'API', dose_mg: 500 },
      { name: 'Lactose', smiles: 'OC[C@H]1O[C@@H](O)[C@H](O)[C@@H](O)[C@H]1O', role: 'excipient', dose_mg: 100 },
      { name: 'Starch', smiles: 'OC[C@@H]1[C@H](O)C(O)(C)OC1', role: 'excipient', dose_mg: 80 },
    ],
  },
  {
    label: 'Nitrobenzene Mixture (High Risk)',
    components: [
      { name: 'Nitrobenzene', smiles: 'c1ccc([N+](=O)[O-])cc1', role: 'API', dose_mg: 50 },
      { name: 'Ethanol', smiles: 'CCO', role: 'solvent', dose_mg: 10 },
    ],
  },
  {
    label: 'Cardio Cocktail (Multiple APIs)',
    components: [
      { name: 'Aspirin', smiles: 'CC(=O)OC1=CC=CC=C1', role: 'API', dose_mg: 81 },
      { name: 'Atorvastatin', smiles: 'CC(C)C(C(=O)NC(CCCC)C)C', role: 'API', dose_mg: 20 },
      { name: 'Magnesium Stearate', smiles: 'CCCCCCCCCC(=O)O[Mg+]', role: 'excipient', dose_mg: 5 },
    ],
  },
];

const STABILITY_CONFIG = {
  STABLE: { color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', label: 'STABLE' },
  WARNING: { color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/30', label: 'WARNING' },
  CRITICAL_INCOMPATIBILITY: { color: 'text-red-400', bg: 'bg-red-500/10', border: 'border-red-500/30', label: 'INCOMPATIBLE' },
};

const RISK_COLORS = {
  HIGH: 'text-red-400 bg-red-500/10',
  MEDIUM: 'text-amber-400 bg-amber-500/10',
  LOW: 'text-emerald-400 bg-emerald-500/10',
};

export default function FormulationScreening() {
  const [components, setComponents] = useState([
    { name: '', smiles: '', role: 'API', dose_mg: 100 },
    { name: '', smiles: '', role: 'excipient', dose_mg: 50 },
  ]);
  const [formulationName, setFormulationName] = useState('');
  const [results, setResults] = useState(null);

  const [loading, setLoading] = useState(false);

  const addComponent = () => {
    setComponents([...components, { name: '', smiles: '', role: 'API', dose_mg: 100 }]);
  };

  const removeComponent = (idx) => {
    if (components.length <= 1) return;
    setComponents(components.filter((_, i) => i !== idx));
  };

  const updateComponent = (idx, field, value) => {
    const updated = [...components];
    updated[idx] = { ...updated[idx], [field]: value };
    setComponents(updated);
  };

  const loadPreset = (preset) => {
    setComponents(preset.components);
    setFormulationName(preset.label);
  };

  const runScreening = async () => {
    setLoading(true);
    const payload = {
      name: formulationName || 'Untitled Formulation',
      components: components.map(c => ({ ...c, dose_mg: parseFloat(c.dose_mg) || 0 })),
    };

    try {
      const resp = await api.post('/api/formulation/screen', payload);
      const data = resp.data;
      setResults(data);
      if (data.formulation_stability === 'CRITICAL_INCOMPATIBILITY') {
        toast.error('Critical incompatibility detected!');
      } else if (data.formulation_stability === 'WARNING') {
        toast('Formulation warnings detected — review details', { icon: '⚠️' });
      } else {
        toast.success('Formulation is stable!');
      }
    } catch (err) {
      toast.error(`Screening failed: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const stabilityKey = results?.formulation_stability || 'STABLE';
  const cfg = STABILITY_CONFIG[stabilityKey];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-text-primary">Formulation & Mixture Screening</h1>
          <p className="text-sm text-text-secondary mt-1">
            Screen multi-component formulations for chemical incompatibilities, reactive metabolites, and synergistic toxicity.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <select
            onChange={(e) => {
              const p = PRESETS.find(p => p.label === e.target.value);
              if (p) loadPreset(p);
            }}
            className="px-4 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-green/50"
          >
            <option value="">Load preset…</option>
            {PRESETS.map(p => <option key={p.label} value={p.label}>{p.label}</option>)}
          </select>
          <button
            onClick={runScreening}
            disabled={loading || components.some(c => !c.smiles)}
            className="flex items-center gap-2 px-4 py-2 bg-accent-green text-white rounded-lg font-medium hover:bg-accent-green/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
            ) : (
              <PlayIcon className="h-4 w-4" />
            )}
            Run Screening
          </button>
        </div>
      </div>

      {/* Component Builder */}
      <div className="surface rounded-xl border border-border p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-text-primary">Component Builder</h2>
          <button
            onClick={addComponent}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-accent-green hover:bg-accent-green/10 rounded-lg border border-accent-green/30 transition-colors"
          >
            <PlusIcon className="h-4 w-4" />
            Add Component
          </button>
        </div>

        <div className="space-y-3">
          {components.map((comp, idx) => (
            <div key={idx} className="flex items-center gap-3 p-3 bg-canvas rounded-lg border border-border">
              <input
                type="text"
                placeholder="Name"
                value={comp.name}
                onChange={(e) => updateComponent(idx, 'name', e.target.value)}
                className="w-32 px-3 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-green/50"
              />
              <input
                type="text"
                placeholder="SMILES"
                value={comp.smiles}
                onChange={(e) => updateComponent(idx, 'smiles', e.target.value)}
                className="flex-1 px-3 py-2 bg-surface border border-border rounded-lg text-sm font-mono text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-green/50"
              />
              <select
                value={comp.role}
                onChange={(e) => updateComponent(idx, 'role', e.target.value)}
                className="w-32 px-3 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-green/50"
              >
                <option value="API">API</option>
                <option value="excipient">Excipient</option>
                <option value="solvent">Solvent</option>
              </select>
              <input
                type="number"
                placeholder="Dose (mg)"
                value={comp.dose_mg}
                onChange={(e) => updateComponent(idx, 'dose_mg', parseFloat(e.target.value) || 0)}
                className="w-24 px-3 py-2 bg-surface border border-border rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-green/50"
              />
              <button
                onClick={() => removeComponent(idx)}
                className="p-1.5 text-text-muted hover:text-red-400 rounded-lg hover:bg-red-500/10 transition-colors"
                title="Remove component"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Results Panel */}
      {results && (
        <div className="space-y-6">
          {/* Stability Badge */}
          <div className={`flex items-center gap-4 p-6 rounded-xl border ${cfg.bg} ${cfg.border}`}>
            <div className={`p-3 rounded-xl bg-canvas`}>
              {stabilityKey === 'CRITICAL_INCOMPATIBILITY' ? (
                <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
              ) : (
                <CheckCircleIcon className={`h-8 w-8 ${cfg.color}`} />
              )}
            </div>
            <div>
              <h3 className="text-2xl font-bold text-text-primary">Formulation Stability: {cfg.label}</h3>
              <p className="text-sm text-text-secondary mt-1">
                Overall Risk Score: <span className="font-bold text-text-primary">{results.overall_risk_score}</span>
                {' '}| Components: {results.n_components} | Incompatibilities: {results.n_incompatibilities}
              </p>
              <p className="text-xs text-text-muted mt-1">
                Formulation: {results.formulation_name} • {new Date(results.timestamp).toLocaleString()}
              </p>
            </div>
          </div>

          {/* Reactive Metabolite Alert Cards */}
          {results.reactive_metabolite_scan.length > 0 && (
            <div className="grid gap-3 md:grid-cols-2">
              {results.reactive_metabolite_scan.map((scan, i) => {
                const bgClass = scan.risk_label === 'HIGH' ? 'border-red-500/30 bg-red-500/5' :
                  scan.risk_label === 'MODERATE' ? 'border-amber-500/30 bg-amber-500/5' :
                  'border-emerald-500/30 bg-emerald-500/5';
                return (
                  <div key={i} className={`p-4 rounded-xl border ${bgClass}`}>
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-text-primary">{scan.component}</h4>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-bold ${
                        scan.risk_label === 'HIGH' ? 'text-red-400 bg-red-500/10' :
                        scan.risk_label === 'MODERATE' ? 'text-amber-400 bg-amber-500/10' :
                        'text-emerald-400 bg-emerald-500/10'
                      }`}>
                        BRI: {scan.bri_score} ({scan.risk_label})
                      </span>
                    </div>
                    {scan.alerts.map((alert, j) => (
                      <div key={j} className="mt-2 p-2 bg-canvas rounded-lg">
                        <span className="text-xs font-medium text-text-secondary">{alert.name}</span>
                        <p className="text-xs text-text-muted mt-1">{alert.mechanism}</p>
                      </div>
                    ))}
                  </div>
                );
              })}
            </div>
          )}

          {/* Incompatibility Matrix Table */}
          {results.incompatibility_matrix.length > 0 && (
            <div className="surface rounded-xl border border-border p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4 flex items-center gap-2">
                <BeakerIcon className="h-5 w-5 text-red-400" />
                Pairwise Incompatibility Report
              </h3>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left py-2 text-text-secondary">Component A</th>
                      <th className="text-left py-2 text-text-secondary">Component B</th>
                      <th className="text-left py-2 text-text-secondary">Risk</th>
                      <th className="text-left py-2 text-text-secondary">P_incompatible</th>
                      <th className="text-left py-2 text-text-secondary">Mechanism</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.incompatibility_matrix.map((row, i) => (
                      <tr key={i} className="border-b border-border/50">
                        <td className="py-2 text-text-primary">{row.pair[0]}</td>
                        <td className="py-2 text-text-primary">{row.pair[1]}</td>
                        <td className="py-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${RISK_COLORS[row.risk]}`}>
                            {row.risk}
                          </span>
                        </td>
                        <td className="py-2 text-text-secondary">{row.p_incompatible}</td>
                        <td className="py-2 text-text-secondary">{row.mechanism}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Synergistic Toxicity & Components Summary */}
          <div className="grid gap-6 md:grid-cols-2">
            <div className="surface rounded-xl border border-border p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Synergistic Toxicity</h3>
              <div className="space-y-3">
                {Object.entries(results.synergistic_toxicity).map(([key, val]) => (
                  <div key={key} className="flex items-center justify-between">
                    <span className="text-sm text-text-secondary capitalize">{key.replace('_', ' ')}</span>
                    <span className="font-bold text-text-primary">{val}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="surface rounded-xl border border-border p-6">
              <h3 className="text-lg font-semibold text-text-primary mb-4">Components Summary</h3>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {results.components_summary.map((comp, i) => (
                  <div key={i} className="flex items-center justify-between p-2 bg-canvas rounded-lg">
                    <div>
                      <span className="text-sm font-medium text-text-primary">{comp.name}</span>
                      <span className="text-xs text-text-muted ml-2">[{comp.role}]</span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-text-secondary">
                      <span>{comp.dose_mg} mg</span>
                      <span>⚠️{comp.reactivity_risk}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
