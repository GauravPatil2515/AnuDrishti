import React, { useState } from 'react';
import axios from 'axios';
import { clsx } from 'clsx';
import { Toaster, toast } from 'react-hot-toast';
import {
  BeakerIcon, SwatchIcon, ShieldCheckIcon, MagnifyingGlassIcon, TableCellsIcon, SparklesIcon,
} from '@heroicons/react/24/outline';
import MolecularInput from '../components/MolecularInput';
import MolecularExplorer from '../components/MolecularExplorer';
import SafetyDashboard from '../components/SafetyDashboard';
import ExplanationAudit from '../components/ExplanationAudit';
import LibraryScreening from '../components/LibraryScreening';
import WhatIfOptimizer from '../components/WhatIfOptimizer';

const TABS = [
  { id: 'input', label: 'Input', icon: BeakerIcon },
  { id: 'explorer', label: 'Graph Explorer', icon: SwatchIcon },
  { id: 'safety', label: 'Safety & ADMET', icon: ShieldCheckIcon },
  { id: 'audit', label: 'Explanation Audit', icon: MagnifyingGlassIcon },
  { id: 'library', label: 'Library Screening', icon: TableCellsIcon },
  { id: 'whatif', label: 'What-If', icon: SparklesIcon },
];

const PharmaGuardWorkbench = () => {
  const [activeTab, setActiveTab] = useState('input');
  const [analysis, setAnalysis] = useState(null);
  const [batchResult, setBatchResult] = useState(null);
  const [whatif, setWhatif] = useState(null);
  const [loading, setLoading] = useState(false);

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
        {activeTab === 'input' && <MolecularInput onAnalyze={handleAnalyze} isLoading={loading} />}
        {activeTab === 'explorer' && <MolecularExplorer analysis={analysis} />}
        {activeTab === 'safety' && <SafetyDashboard analysis={analysis} />}
        {activeTab === 'audit' && <ExplanationAudit analysis={analysis} />}
        {activeTab === 'library' && <LibraryScreening batchResult={batchResult} />}
        {activeTab === 'whatif' && <WhatIfOptimizer whatif={whatif} />}
      </main>

      <footer className="mx-auto max-w-7xl px-6 py-6 text-center text-xs text-slate-400">
        PharmaGuard AI is a computational decision-support tool. It does not constitute regulatory,
        clinical, or toxicological approval. Predictions require experimental validation.
      </footer>
    </div>
  );
};

export default PharmaGuardWorkbench;
