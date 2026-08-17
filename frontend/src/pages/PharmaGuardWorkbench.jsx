import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import { clsx } from 'clsx';
import { toast } from 'react-hot-toast';
import {
  BeakerIcon, SwatchIcon, ShieldCheckIcon, MagnifyingGlassIcon,
  TableCellsIcon, SparklesIcon, PlayIcon, InformationCircleIcon
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
  { id: 'explorer', label: 'Explorer', icon: SwatchIcon },
  { id: 'safety', label: 'Safety', icon: ShieldCheckIcon },
  { id: 'audit', label: 'Audit', icon: MagnifyingGlassIcon },
  { id: 'library', label: 'Library', icon: TableCellsIcon },
  { id: 'whatif', label: 'What-If', icon: SparklesIcon },
  { id: 'demo', label: 'Demo Sandbox', icon: PlayIcon },
];

const EmptyState = ({ icon: Icon, title, description }) => (
  <div className="surface p-12 text-center flex flex-col items-center justify-center my-4">
    <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-elevated border border-border mb-4 shadow-sm">
      <Icon className="h-8 w-8 text-text-muted" />
    </div>
    <h3 className="text-base font-bold text-text-primary font-display">{title}</h3>
    <p className="text-xs text-text-secondary mt-1 max-w-md">{description}</p>
  </div>
);

const DemoView = ({ results, loading }) => {
  if (loading) {
    return (
      <div className="surface p-12 text-center text-text-muted animate-fade-in">
        <div className="animate-pulse flex flex-col items-center">
          <div className="h-10 w-10 rounded-full border-4 border-border border-t-accent-green animate-spin mb-4"></div>
          Loading demo molecules…
        </div>
      </div>
    );
  }
  if (!results || results.length === 0) {
    return (
      <EmptyState 
        icon={PlayIcon} 
        title="No Demo Loaded" 
        description="Click 'Load Demo' to explore two precomputed examples with zero setup." 
      />
    );
  }
  return (
    <div className="space-y-4 animate-fade-in">
      <div className="rounded-xl border border-accent-amber/30 bg-accent-amber/5 p-4 text-xs text-accent-amber flex items-start gap-3">
        <InformationCircleIcon className="h-5 w-5 shrink-0" />
        <p>
          These are <strong>illustrative demo records</strong> (a benign drug and a known
          toxicant) so you can experience the full triage + faithfulness workflow instantly.
        </p>
      </div>
      {results.map((r, i) => (
        <div key={i} className="surface p-5 hover:shadow-card-hover transition-all duration-200">
          <p className="mb-4 font-mono text-xs text-text-muted break-all p-2 bg-canvas rounded border border-border">{r.smiles}</p>
          <SafetyDashboard analysis={r} />
        </div>
      ))}
    </div>
  );
};

const CommandPalette = ({ isOpen, onClose, activeTab, onTabSelect, onQuickAction, searchRef }) => {
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
    { label: 'Export PDF Report', action: 'export', shortcut: '⌘E' },
    { label: 'Simulate Hallucination', action: 'hallucinate', shortcut: '⌘H' },
  ];

  const filteredActions = quickActions.filter(a =>
    a.label.toLowerCase().includes(search.toLowerCase())
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4" onClick={onClose}>
      <div className="fixed inset-0 bg-canvas/80 backdrop-blur-sm" />
      <div
        className="relative w-full max-w-lg rounded-xl border border-border bg-surface shadow-dropdown overflow-hidden z-10"
        onClick={e => e.stopPropagation()}
      >
        <div className="px-4 pt-3 pb-2 border-b border-border">
          <input
            ref={searchRef}
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Type a command or search tabs..."
            className="w-full bg-transparent border-0 text-sm text-text-primary placeholder:text-text-muted focus:outline-none"
            autoFocus
          />
        </div>

        {filteredActions.length > 0 && (
          <div className="p-2">
            <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-text-muted">Quick Actions</div>
            {filteredActions.map((action) => (
              <div
                key={action.action}
                className="flex items-center justify-between px-3 py-2 text-xs font-medium text-text-primary rounded-lg hover:bg-surface-hover cursor-pointer"
                onClick={() => {
                  onQuickAction(action.action);
                  onClose();
                }}
              >
                <span>{action.label}</span>
                <span className="font-mono text-[10px] text-text-muted border border-border px-1.5 py-0.5 rounded">{action.shortcut}</span>
              </div>
            ))}
          </div>
        )}

        {filteredTabs.length > 0 && (
          <div className="p-2 border-t border-border">
            <div className="px-3 py-1 text-[10px] font-bold uppercase tracking-wider text-text-muted">Navigation</div>
            {filteredTabs.map((t) => (
              <div
                key={t.id}
                className={clsx(
                  'flex items-center gap-2 px-3 py-2 text-xs font-medium rounded-lg cursor-pointer',
                  activeTab === t.id ? 'bg-accent-green/10 text-accent-green font-semibold' : 'text-text-secondary hover:bg-surface-hover'
                )}
                onClick={() => {
                  onTabSelect(t.id);
                  onClose();
                }}
              >
                <t.icon className="h-4 w-4" />
                <span>{t.label}</span>
              </div>
            ))}
          </div>
        )}

        <div className="px-4 py-2 border-t border-border text-[11px] text-text-muted bg-surface-elevated flex justify-between">
          <span>ESC to close</span>
          <span>Press ⌘K anytime</span>
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
    <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto space-y-6">
      <CommandPalette
        isOpen={cmdPaletteOpen}
        onClose={() => setCmdPaletteOpen(false)}
        activeTab={activeTab}
        onTabSelect={setActiveTab}
        onQuickAction={handleQuickAction}
        searchRef={cmdInputRef}
      />

      {/* Tab Navigation & Info Bar Header */}
      <div className="inline-flex items-center gap-1 rounded-xl bg-surface/80 p-1.5 border border-border/60 backdrop-blur-md">
      {TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={activeTab === t.id
                  ? 'bg-surface-elevated text-text-primary shadow-sm border border-border/80 rounded-lg px-3 py-1.5 text-xs font-semibold'
                  : 'text-text-muted hover:text-text-secondary rounded-lg px-3 py-1.5 text-xs font-medium transition-colors'
                }
              >
                {t.icon} <span>{t.label}</span>
              </button>
            ))}
          </div>
    
          <div className="hidden md:flex items-center gap-2 text-xs text-text-muted px-2">
            <span>Press</span>
            <kbd className="px-1.5 py-0.5 rounded border border-border bg-surface-elevated font-mono text-[10px] font-bold text-text-primary">⌘K</kbd>
            <span>for commands</span>
          </div>

      {/* Main Content Area */}
      <div>
        {loading && (
          <div className="mb-6">
            <PipelineProgress active={loading} />
          </div>
        )}

        {activeTab === 'input' && (
          <div className="animate-fade-in">
            <MolecularInput onAnalyze={handleAnalyze} isLoading={loading} />
            <div className="mt-6 flex justify-center">
              <button
                onClick={loadDemo}
                disabled={demoLoading}
                className="btn btn-secondary"
              >
                <PlayIcon className="h-4 w-4 text-accent-green" />
                {demoLoading ? 'Loading Demo…' : 'Try Demo (No SMILES needed)'}
              </button>
            </div>
          </div>
        )}

        {activeTab === 'explorer' && (
          <div className="animate-fade-in">
            {analysis ? (
              <MolecularExplorer analysis={analysis} />
            ) : (
              <EmptyState 
                icon={SwatchIcon} 
                title="No Molecule Loaded" 
                description="Run an analysis from the Input tab to explore its 2D graph structure and properties." 
              />
            )}
          </div>
        )}
        
        {activeTab === 'safety' && (
          <div className="animate-fade-in">
            {analysis ? (
              <SafetyDashboard analysis={analysis} />
            ) : (
              <EmptyState 
                icon={ShieldCheckIcon} 
                title="No Safety Data" 
                description="Run an analysis to view ADMET predictions, toxicity risks, and epistemic uncertainty bands." 
              />
            )}
          </div>
        )}
        
        {activeTab === 'audit' && (
          <div className="animate-fade-in">
            {analysis ? (
              <ExplanationAudit analysis={analysis} />
            ) : (
              <EmptyState 
                icon={MagnifyingGlassIcon} 
                title="No Explanations to Audit" 
                description="Run an analysis to generate LLM explanations and verify their faithfulness against GNN logic." 
              />
            )}
          </div>
        )}
        
        {activeTab === 'library' && (
          <div className="animate-fade-in">
            {batchResult ? (
              <LibraryScreening batchResult={batchResult} />
            ) : (
              <EmptyState 
                icon={TableCellsIcon} 
                title="No Batch Results" 
                description="Run a batch analysis from the Input tab to view high-throughput library screening results." 
              />
            )}
          </div>
        )}
        
        {activeTab === 'whatif' && (
          <div className="animate-fade-in">
            {whatif ? (
              <WhatIfOptimizer whatif={whatif} />
            ) : (
              <EmptyState 
                icon={SparklesIcon} 
                title="No Counterfactuals Generated" 
                description="Run a What-If optimization from the Input tab to explore bioisosteric toxicity reductions." 
              />
            )}
          </div>
        )}
        
        {activeTab === 'demo' && (
          <div className="animate-fade-in space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-bold font-display text-text-primary">Demo Sandbox</h2>
              <button
                onClick={loadDemo}
                disabled={demoLoading}
                className="btn btn-primary"
              >
                <PlayIcon className="h-4 w-4" />
                {demoLoading ? 'Loading…' : 'Reload Demo Data'}
              </button>
            </div>
            <DemoView results={demoResults} loading={demoLoading} />
          </div>
        )}
      </div>
    </div>
  );
};

export default PharmaGuardWorkbench;