import React, { useState, useEffect, useRef, useCallback } from 'react';
import api from '../api';
import { clsx } from 'clsx';
import { Toaster, toast } from 'react-hot-toast';
import {
  BeakerIcon, SwatchIcon, ShieldCheckIcon, MagnifyingGlassIcon,
  TableCellsIcon, SparklesIcon, PlayIcon, CommandLineIcon,
  XMarkIcon, CheckBadgeIcon, InformationCircleIcon
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
  { id: 'demo', label: 'Demo', icon: PlayIcon },
];

const DemoView = ({ results, loading }) => {
  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-surface p-10 text-center text-muted animate-fade-in">
        Loading demo molecules…
      </div>
    );
  }
  if (!results || results.length === 0) {
    return (
      <div className="rounded-lg border border-border bg-surface p-10 text-center text-muted">
        Click “Load Demo” to explore two precomputed examples with zero setup.
      </div>
    );
  }
  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs text-amber-400">
        These are <strong>illustrative demo records</strong> (a benign drug and a known
        toxicant) so you can experience the full triage + faithfulness workflow instantly.
        They are not live model predictions — paste a real SMILES in the Input tab for a
        live analysis.
      </div>
      {results.map((r, i) => (
        <div key={i} className="rounded-lg border border-border bg-surface p-4 shadow-card hover:shadow-card-hover transition-all duration-150">
          <p className="mb-3 font-mono text-xs text-muted break-all">{r.smiles}</p>
          <SafetyDashboard analysis={r} />
        </div>
      ))}
    </div>
  );
};

const CommandPalette = ({ isOpen, onClose, tabs, activeTab, onTabSelect, onQuickAction, searchRef }) => {
  const [search, setSearch] = useState('');

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => searchRef?.current?.focus(), 100);
    }
  }, [isOpen, searchRef]);

  const filteredTabs = TABS.filter(t =>
    t.label.toLowerCase().includes(search.toLowerCase())
  );

  const quickActions = [
    { label: 'Load Demo', action: 'demo', shortcut: '↵' },
    { label: 'Run Analysis', action: 'analyze', shortcut: '⌘⏎' },
    { label: 'Export PDF Report', action: 'export', shortcut: '⌘E' },
    { label: 'Simulate Hallucination', action: 'hallucinate', shortcut: '⌘H' },
  ];

  const filteredActions = quickActions.filter(a =>
    a.label.toLowerCase().includes(search.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="cmd-palette" onClick={onClose}>
      <div className="cmd-palette-backdrop" />
      <div
        className="cmd-palette-window"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-4 pt-3 pb-2 border-b border-border">
          <input
            ref={searchRef}
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Type a command or search tabs..."
            className="cmd-palette-input"
            autoFocus
          />
        </div>

        {filteredActions.length > 0 && (
          <>
            <div className="cmd-palette-section">Quick Actions</div>
            {filteredActions.map((action, i) => (
              <div
                key={action.action}
                className="cmd-palette-item"
                onClick={() => {
                  onQuickAction(action.action);
                  onClose();
                }}
              >
                <span>{action.label}</span>
                <span className="cmd-palette-shortcut">{action.shortcut}</span>
              </div>
            ))}
          </>
        )}

        {filteredTabs.length > 0 && (
          <>
            <div className="cmd-palette-section">Navigation</div>
            {filteredTabs.map((t) => (
              <div
                key={t.id}
                className={clsx(
                  'cmd-palette-item',
                  activeTab === t.id ? 'cmd-palette-item-selected' : ''
                )}
                onClick={() => {
                  onTabSelect(t.id);
                  onClose();
                }}
              >
                <span>{t.label}</span>
              </div>
            ))}
          </>
        )}

        <div className="px-3 py-2 border-t border-border text-xs text-muted">
          ESC to close · ↑↓ to navigate · ↵ to select
        </div>
      </div>
    </div>
  );
};

const PharmaGuardWorkbench = () => {
  const [activeTab, setActiveTab] = useState('input');
  const [analysis, setAnalysis] = useState(null);
  const [batchResult, setBatchResult] = useState(null);
  const [whatif, setWhatif] = useState(null);
  const [loading, setLoading] = useState(false);
  const [demoResults, setDemoResults] = useState(null);
  const [demoLoading, setDemoLoading] = useState(false);
  const [cmdPaletteOpen, setCmdPaletteOpen] = useState(false);
  const cmdInputRef = useRef(null);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('openDemo') === '1') {
      setActiveTab('demo');
      loadDemo();
    }

    // Listen for Cmd/Ctrl+K
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCmdPaletteOpen(true);
      }
      if (e.key === 'Escape') {
        setCmdPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const loadDemo = async () => {
    setDemoLoading(true);
    try {
      const res = await api.get('/api/demo');
      setDemoResults(res.data.results || []);
      toast.success('Loaded 2 demo molecules');
      setActiveTab('demo');
    } catch (e) {
      toast.error('Demo load failed');
    } finally {
      setDemoLoading(false);
    }
  };

  const handleQuickAction = (action) => {
    if (action === 'demo') {
      loadDemo();
    } else if (action === 'export' && analysis) {
      exportPdfReport();
    } else if (action === 'hallucinate') {
      toast('Simulating hallucinated explanation...', { icon: '⚠️' });
    }
  };

  const exportPdfReport = async () => {
    if (!analysis || !analysis.smiles) {
      toast.error('No analysis loaded');
      return;
    }
    try {
      const res = await api.post('/api/report/pdf', {
        smiles: analysis.smiles
      }, {
        responseType: 'blob',
      });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `pharmaguard_report_${Date.now()}.pdf`;
      a.click();
      window.URL.revokeObjectURL(url);
      toast.success('PDF report downloaded');
    } catch (e) {
      toast.error('PDF export failed');
    }
  };

  const handleAnalyze = async ({ mode, smiles, smiles_list }) => {
    setLoading(true);
    try {
      if (mode === 'single') {
        const res = await api.post('/api/analyze/single', { smiles, include_explanation: true });
        setAnalysis(res.data.analysis);
        setWhatif(null);
        setActiveTab('safety');
        toast.success('Analysis complete');
      } else if (mode === 'batch') {
        const res = await api.post('/api/analyze/batch', { smiles_list, include_explanation: false });
        setBatchResult(res.data);
        setAnalysis(null);
        setActiveTab('library');
        toast.success(`Screened ${res.data.total_processed} molecules`);
      } else if (mode === 'whatif') {
        const res = await api.post('/api/optimize/what-if', { smiles, n_variants: 6 });
        setWhatif(res.data);
        setActiveTab('whatif');
        toast.success('Optimization candidates generated');
      } else if (mode === 'lookup') {
        toast.success('Lookup completed');
      }
    } catch (e) {
      toast.error(e.response?.data?.error || 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-canvas text-primary">
        <Toaster position="top-right" />

        {/* Command Palette */}
        <CommandPalette
          isOpen={cmdPaletteOpen}
          onClose={() => setCmdPaletteOpen(false)}
          tabs={TABS}
          activeTab={activeTab}
          onTabSelect={setActiveTab}
          onQuickAction={handleQuickAction}
          searchRef={cmdInputRef}
        />

        {/* Header */}
        <header className="border-b border-border bg-surface-elevated">
          <div className="container-wide flex items-center justify-between h-12">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500 text-white">
                <ShieldCheckIcon className="h-5 w-5" />
              </div>
              <div>
                <h1 className="text-base font-extrabold text-primary">PharmaGuard AI</h1>
                <p className="text-xs text-muted">Trustworthy Drug-Safety Decision Support</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className="rounded-full bg-indigo-500/10 px-2.5 py-0.5 text-xs font-semibold text-indigo-400">
                Predict · Explain · Verify · Trust
              </span>
            </div>
          </div>
        </header>

        {/* Clinical disclaimer — subtle, non-dominant */}
        <div className="border-b border-border bg-surface">
          <div className="container-wide flex items-center gap-2 px-3 py-1.5 text-xs text-muted">
            <span aria-hidden className="text-amber-400">⚠</span>
            <span>
              Not for clinical use — PharmaGuard AI is a computational decision-support tool.
              Predictions are not a regulatory, clinical, or toxicological approval and require
              experimental validation.
            </span>
          </div>
        </div>

        {/* Command palette shortcut hint */}
        <div className="container-wide px-4 py-2">
          <div className="flex items-center justify-between">
            <div className="text-xs text-muted">
              Press <kbd className="px-1.5 py-0.5 rounded bg-surface border border-border text-xs">⌘K</kbd> for command palette
            </div>
          </div>
        </div>

        {/* Tab navigation - Linear underline style */}
        <nav className="sticky top-0 z-20 border-b border-border bg-canvas/80 backdrop-blur">
          <div className="container-wide flex overflow-x-auto px-3 py-1 gap-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-2 text-sm font-medium whitespace-nowrap',
                  'transition-all duration-100',
                  activeTab === t.id
                    ? 'text-primary border-b-2 border-indigo-500'
                    : 'text-muted hover:text-secondary hover:bg-surface rounded-md'
                )}
              >
                <t.icon className="h-4 w-4" />
                {t.label}
              </button>
            ))}
          </div>
        </nav>

        {/* Content */}
        <main className="container-wide px-4 py-4">
          {loading && (
            <div className="mb-4">
              <PipelineProgress active={loading} />
            </div>
          )}

          {activeTab === 'input' && (
            <>
              <MolecularInput onAnalyze={handleAnalyze} isLoading={loading} />
              <div className="mt-4 flex justify-center">
                <button
                  onClick={loadDemo}
                  disabled={demoLoading}
                  className="btn btn-primary"
                >
                  <PlayIcon className="h-4 w-4" />
                  {demoLoading ? 'Loading…' : 'Try Demo (no SMILES needed)'}
                </button>
              </div>
            </>
          )}

          {activeTab === 'explorer' && (
            <div className="animate-fade-in">
              <MolecularExplorer analysis={analysis} />
            </div>
          )}
          {activeTab === 'safety' && analysis && (
            <div className="animate-fade-in">
              <SafetyDashboard analysis={analysis} />
            </div>
          )}
          {activeTab === 'audit' && analysis && (
            <div className="animate-fade-in">
              <ExplanationAudit analysis={analysis} />
            </div>
          )}
          {activeTab === 'library' && (
            <div className="animate-fade-in">
              <LibraryScreening batchResult={batchResult} />
            </div>
          )}
          {activeTab === 'whatif' && (
            <div className="animate-fade-in">
              <WhatIfOptimizer whatif={whatif} />
            </div>
          )}
          {activeTab === 'demo' && (
            <div className="space-y-3">
              <button
                onClick={loadDemo}
                disabled={demoLoading}
                className="btn btn-primary"
              >
                <PlayIcon className="h-4 w-4" />
                {demoLoading ? 'Loading…' : 'Load Demo (2 Free Molecules)'}
              </button>
              <DemoView results={demoResults} loading={demoLoading} />
            </div>
          )}
        </main>

        {/* Footer */}
        <footer className="border-t border-border bg-surface-elevated mt-6">
          <div className="container-wide py-3 text-center text-xs text-muted">
            PharmaGuard AI is a computational decision-support tool. It does not constitute regulatory,
            clinical, or toxicological approval. Predictions require experimental validation.
          </div>
        </footer>
    </div>
  );
};

export default PharmaGuardWorkbench;