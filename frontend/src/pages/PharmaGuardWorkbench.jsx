import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useLocation } from 'react-router-dom';
import { clsx } from 'clsx';
import { Toaster, toast } from 'react-hot-toast';
import {
  BeakerIcon, SwatchIcon, ShieldCheckIcon, MagnifyingGlassIcon, TableCellsIcon, SparklesIcon, PlayIcon,
  CheckBadgeIcon, InformationCircleIcon, ShieldExclamationIcon
} from '@heroicons/react/24/outline';
import MolecularInput from '../components/MolecularInput';
import MolecularExplorer from '../components/MolecularExplorer';
import SafetyDashboard from '../components/SafetyDashboard';
import ExplanationAudit from '../components/ExplanationAudit';
import LibraryScreening from '../components/LibraryScreening';
import WhatIfOptimizer from '../components/WhatIfOptimizer';
import PipelineProgress from '../components/PipelineProgress';

const TABS = [
  { id: 'input', label: 'Input', icon: BeakerIcon },
  { id: 'explorer', label: 'Graph Explorer', icon: SwatchIcon },
  { id: 'safety', label: 'Safety & ADMET', icon: ShieldCheckIcon },
  { id: 'audit', label: 'Explanation Audit', icon: MagnifyingGlassIcon },
  { id: 'library', label: 'Library Screening', icon: TableCellsIcon },
  { id: 'whatif', label: 'What-If', icon: SparklesIcon },
  { id: 'demo', label: 'Demo (2 Free)', icon: PlayIcon },
];

const DemoView = ({ results, loading }) => {
  if (loading) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-400">
        Loading demo molecules…
      </div>
    );
  }
  if (!results || results.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-400">
        Click “Load Demo” to explore two precomputed examples with zero setup.
      </div>
    );
  }
  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-4 text-sm text-indigo-700">
        These are <strong>illustrative demo records</strong> (a benign drug and a known toxicant) so you can
        experience the full triage + faithfulness workflow instantly. They are not live model predictions —
        paste a real SMILES in the Input tab for a live analysis.
      </div>
      {results.map((r, i) => (
        <div key={i} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <p className="mb-3 font-mono text-xs text-slate-500">{r.smiles}</p>
          <SafetyDashboard analysis={r} />
        </div>
      ))}
    </div>
  );
};

const isStandalone = window.location.pathname.includes('/pharmaguard');

const PharmaGuardWorkbench = () => {
  const [activeTab, setActiveTab] = useState('input');
  const [analysis, setAnalysis] = useState(null);
  const [batchResult, setBatchResult] = useState(null);
  const [whatif, setWhatif] = useState(null);
  const [loading, setLoading] = useState(false);
  const [demoResults, setDemoResults] = useState(null);
  const [demoLoading, setDemoLoading] = useState(false);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('openDemo') === '1') {
      setActiveTab('demo');
      loadDemo();
    }
  }, []);

  const loadDemo = async () => {
    setDemoLoading(true);
    try {
      const res = await axios.get('/api/demo');
      setDemoResults(res.data.results || []);
      toast.success('Loaded 2 demo molecules');
      setActiveTab('demo');
    } catch (e) {
      toast.error('Demo load failed');
    } finally {
      setDemoLoading(false);
    }
  };

  const handleAnalyze = async ({ mode, smiles, smiles_list }) => {
    setLoading(true);
    try {
      if (mode === 'single') {
        const res = await axios.post('/api/analyze/single', { smiles, include_explanation: true });
        setAnalysis(res.data.analysis);
        setWhatif(null);
        setActiveTab('safety');
        toast.success('Analysis complete');
      } else if (mode === 'batch') {
        const res = await axios.post('/api/analyze/batch', { smiles_list, include_explanation: false });
        setBatchResult(res.data);
        setAnalysis(null);
        setActiveTab('library');
        toast.success(`Screened ${res.data.total_processed} molecules`);
      } else if (mode === 'whatif') {
        const res = await axios.post('/api/optimize/what-if', { smiles, n_variants: 6 });
        setWhatif(res.data);
        setActiveTab('whatif');
        toast.success('Optimization candidates generated');
      } else if (mode === 'lookup') {
        // For lookup mode, we just show the result in the input tab
        // The actual lookup happens in MolecularInput.handleLookup()
        // This is just for consistency with the API call pattern
        toast.success('Lookup completed');
      }
    } catch (e) {
      toast.error(e.response?.data?.error || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-100">
      <Toaster position="top-right" />

      {/* Header — PharmaGuard AI Workbench */}
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 text-white">
              <ShieldCheckIcon className="h-6 w-6" />
            </div>
            <div>
              <h1 className="text-lg font-extrabold text-slate-800">PharmaGuard AI</h1>
              <p className="text-xs text-slate-500">Trustworthy Drug-Safety Decision Support</p>
            </div>
          </div>
          <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-600">
            Predict · Explain · Verify · Trust
          </span>
        </div>
      </header>

      {/* Prominent clinical-use disclaimer (SIH audit P2 #8) */}
      <div className="border-b border-amber-200 bg-amber-50">
        <div className="mx-auto flex max-w-7xl items-center gap-2 px-6 py-2 text-xs font-semibold text-amber-800">
          <span aria-hidden>⚠️</span>
          <span>
            NOT FOR CLINICAL USE — PharmaGuard AI is a computational decision-support tool.
            Predictions are not regulatory, clinical, or toxicological approval and require experimental validation.
          </span>
        </div>
      </div>

      {/* Tab bar */}
      <nav className="sticky top-0 z-10 border-b border-slate-200 bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-6 py-2">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={clsx(
                'flex items-center gap-2 whitespace-nowrap rounded-xl px-4 py-2 text-sm font-semibold transition',
                activeTab === t.id
                  ? 'bg-indigo-600 text-white shadow'
                  : 'text-slate-600 hover:bg-slate-100'
              )}
            >
              <t.icon className="h-5 w-5" />
              {t.label}
            </button>
          ))}
        </div>
      </nav>

      {/* Content */}
      <main className="mx-auto max-w-7xl px-6 py-6">
        {loading && (
          <div className="mb-6">
            <PipelineProgress active={loading} />
          </div>
        )}
        {activeTab === 'input' && (
          <>
            <MolecularInput onAnalyze={handleAnalyze} isLoading={loading} />
            <div className="mt-6 flex justify-center">
              <button
                onClick={loadDemo}
                disabled={demoLoading}
                className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-bold text-white shadow hover:bg-indigo-700 disabled:opacity-60"
              >
                <PlayIcon className="h-5 w-5" /> {demoLoading ? 'Loading…' : 'Try Demo (no SMILES needed)'}
              </button>
            </div>
          </>
        )}
        {activeTab === 'explorer' && <MolecularExplorer analysis={analysis} />}
        {activeTab === 'safety' && <SafetyDashboard analysis={analysis} />}
        {activeTab === 'audit' && <ExplanationAudit analysis={analysis} />}
        {activeTab === 'library' && <LibraryScreening batchResult={batchResult} />}
        {activeTab === 'whatif' && <WhatIfOptimizer whatif={whatif} />}
        {activeTab === 'demo' && (
          <div className="space-y-4">
            <button
              onClick={loadDemo}
              disabled={demoLoading}
              className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-sm font-bold text-white shadow hover:bg-indigo-700 disabled:opacity-60"
            >
              <PlayIcon className="h-5 w-5" /> {demoLoading ? 'Loading…' : 'Load Demo (2 Free Molecules)'}
            </button>
            <DemoView results={demoResults} loading={demoLoading} />
          </div>
        )}
      </main>

      <footer className="mx-auto max-w-7xl px-6 py-6 text-center text-xs text-slate-400">
        PharmaGuard AI is a computational decision-support tool. It does not constitute regulatory,
        clinical, or toxicological approval. Predictions require experimental validation.
      </footer>
    </div>
  );
};

export default PharmaGuardWorkbench;
