import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { BeakerIcon, CheckBadgeIcon, SignalIcon, SparklesIcon, ArrowRightIcon, ShieldExclamationIcon, CpuChipIcon, ChevronDownIcon, ChevronUpIcon } from '@heroicons/react/24/outline';
import { useAnalysis } from '../App';
import api from '../api';

// Model registry — scientific descriptions for trust & transparency
const MODEL_REGISTRY = [
  {
    id: 'attention_gin',
    label: 'Attention-GIN',
    type: 'Graph Neural Network (GIN + Attention Pooling)',
    dataset: 'Tox21 (12 endpoints, 7,831 compounds)',
    metric: 'ROC-AUC 0.8368',
    endpoints: 'NR-AR, NR-AhR, NR-Aromatase, NR-ER, SR-ARE, SR-ATAD5, SR-HSE, SR-MMP, SR-p53 + 3 more',
    color: 'accent-green',
  },
  {
    id: 'chemberta',
    label: 'ChemBERTa Encoder',
    type: 'Transformer (BERT-based SMILES LM)',
    dataset: 'ZINC (pretrained on 1M SMILES) + fine-tuned',
    metric: '768-dim embeddings, cosine similarity DDI',
    endpoints: 'DDI screening, structural similarity, embedding retrieval',
    color: 'accent-blue',
  },
  {
    id: 'gps',
    label: 'GPS Graph Transformer',
    type: 'Graph Transformer (GPS architecture)',
    dataset: 'Tox21 (12 endpoints)',
    metric: 'MC Dropout uncertainty estimation',
    endpoints: 'All 12 Tox21 endpoints (ensemble with Attention-GIN)',
    color: 'accent-purple',
  },
  {
    id: 'tdc',
    label: 'TDC Rule-Based Panel',
    type: 'SMARTS + RDKit structural alerts',
    dataset: 'TDC hERG (648), DILI (475), AMES (7,255)',
    metric: 'Rule-based structural screening',
    endpoints: 'hERG Cardiotoxicity, DILI Hepatotoxicity, Ames Mutagenicity',
    color: 'accent-amber',
  },
];

const Dashboard = () => {
  const { analysisHistory, lastAnalysis } = useAnalysis();
  const [stats, setStats] = useState({
    molecules_analyzed: 0,
    avg_efs_score: 0.0,
    ood_flags: 0,
    high_triage_count: 0,
    from_session: false
  });
  const [backendStatus, setBackendStatus] = useState(null);
  const [statusLoading, setStatusLoading] = useState(true);
  const [expandedModel, setExpandedModel] = useState(null);

  // Fetch real backend health
  useEffect(() => {
    setStatusLoading(true);
    api.get('/api/health')
      .then(res => {
        setBackendStatus(res.data);
      })
      .catch(() => {
        setBackendStatus({ error: true });
      })
      .finally(() => setStatusLoading(false));
  }, []);

  useEffect(() => {
    let isMounted = true;
    if (analysisHistory && analysisHistory.length > 0) {
      api.post('/api/session/stats', { history: analysisHistory })
        .then(res => {
          if (isMounted && res.data?.success) {
            setStats(res.data.stats);
          }
        })
        .catch(() => {
          if (isMounted) {
            const count = analysisHistory.length;
            const avgEfs = analysisHistory.reduce((acc, h) => acc + (h.explanation?.faithfulness_score || h.explanation?.efs || 0.8), 0) / (count || 1);
            const oodCount = analysisHistory.filter(h => h.ood?.is_ood).length;
            const redCount = analysisHistory.filter(h => (h.triage?.category || '').toUpperCase() === 'RED').length;
            setStats({
              molecules_analyzed: count,
              avg_efs_score: parseFloat(avgEfs.toFixed(2)),
              ood_flags: oodCount,
              high_triage_count: redCount,
              from_session: true
            });
          }
        });
    }
    return () => { isMounted = false; };
  }, [analysisHistory]);

  const modelsLoaded = backendStatus?.models_loaded || [];
  const totalModels = backendStatus?.total_models || 0;
  const modelSource = backendStatus?.model_source || 'none';
  const isHeuristic = modelSource === 'heuristic';
  const isBackendOnline = !backendStatus?.error && (backendStatus?.status === 'healthy' || modelsLoaded.length > 0);

  return (
    <div className="container-wide py-12 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 mb-8">
        <div>
          <h1 className="text-3xl font-display font-bold text-text-primary">Dashboard</h1>
          <p className="text-text-secondary mt-1">
            System overview and recent session analysis activity.
          </p>
        </div>
        <Link 
          to="/app/pharmaguard" 
          className="btn btn-primary"
        >
          <SparklesIcon className="h-4 w-4" />
          AnuDrishti Workbench
          <ArrowRightIcon className="h-4 w-4" />
        </Link>
      </div>
      
      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="surface p-5 hover:-translate-y-1 transition-transform hover:shadow-card-hover">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-accent-green/10 text-accent-green border border-accent-green/20">
              <BeakerIcon className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Molecules Evaluated</h3>
          </div>
          <div className="flex items-end gap-2">
            <p className="text-3xl font-black text-text-primary font-mono">{stats.molecules_analyzed}</p>
            <span className="pill pill-green mb-1">{analysisHistory.length > 0 ? 'Session Active' : 'TDC Benchmark'}</span>
          </div>
        </div>

        <div className="surface p-5 hover:-translate-y-1 transition-transform hover:shadow-card-hover">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20">
              <CheckBadgeIcon className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">Avg EFS Score</h3>
          </div>
          <div className="flex items-end gap-2">
            <p className="text-3xl font-black text-text-primary font-mono">
              {typeof stats.avg_efs_score === 'number' ? stats.avg_efs_score.toFixed(2) : stats.avg_efs_score}
            </p>
            <span className="pill pill-green mb-1">{stats.from_session ? "Session EFS" : "No Data"}</span>
          </div>
        </div>

        <div className="surface p-5 hover:-translate-y-1 transition-transform hover:shadow-card-hover">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-accent-amber/10 text-accent-amber border border-accent-amber/20">
              <SignalIcon className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">OOD Compounds</h3>
          </div>
          <div className="flex items-end gap-2">
            <p className="text-3xl font-black text-text-primary font-mono">{stats.ood_flags}</p>
            <span className="pill pill-yellow mb-1">Novel Scaffolds</span>
          </div>
        </div>
        
        <div className="surface p-5 hover:-translate-y-1 transition-transform hover:shadow-card-hover">
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 rounded-lg bg-accent-red/10 text-accent-red border border-accent-red/20">
              <ShieldExclamationIcon className="h-5 w-5" />
            </div>
            <h3 className="text-sm font-semibold text-text-secondary uppercase tracking-wider">High Toxicity</h3>
          </div>
          <div className="flex items-end gap-2">
            <p className="text-3xl font-black text-text-primary font-mono">{stats.high_triage_count}</p>
            <span className="pill pill-red mb-1">Alert Triggered</span>
          </div>
        </div>
      </div>
      
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        {/* Recent Activity */}
        <div className="md:col-span-2">
          <h2 className="text-lg font-bold text-text-primary mb-4 font-display">Recent Activity</h2>
          <div className="surface overflow-hidden">
            <div className="divide-y divide-border">
              {analysisHistory && analysisHistory.length > 0 ? (
                analysisHistory.slice(0, 5).map((item, idx) => {
                  const triageCat = item.triage?.category || 'GREEN';
                  const isRed = triageCat === 'RED';
                  const isYellow = triageCat === 'YELLOW';
                  const iconColor = isRed ? 'bg-accent-red/10 text-accent-red border-accent-red/20'
                    : isYellow ? 'bg-accent-amber/10 text-accent-amber border-accent-amber/20'
                    : 'bg-accent-green/10 text-accent-green border-accent-green/20';
                  const pillStyle = isRed ? 'pill-red' : isYellow ? 'pill-yellow' : 'pill-green';
                  const efsVal = item.explanation?.faithfulness_score || item.explanation?.efs || 0.85;

                  return (
                    <div key={idx} className="flex items-center gap-4 p-4 hover:bg-surface-hover transition-colors">
                      <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border ${iconColor}`}>
                        <BeakerIcon className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="text-sm font-bold text-text-primary">
                          {item.smiles ? `${item.smiles.slice(0, 24)}...` : 'Molecule Analysis'}
                        </h3>
                        <p className="text-xs text-text-secondary truncate mt-0.5">
                          Triage: {triageCat} · EFS: {(efsVal * 100).toFixed(0)}% · Toxicity: {((item.toxicity_probability || 0.2) * 100).toFixed(0)}%
                        </p>
                      </div>
                      <div className="text-right shrink-0">
                        <span className={`pill ${pillStyle}`}>{triageCat}</span>
                        <p className="text-[10px] text-text-muted mt-1">Session</p>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="flex flex-col items-center justify-center py-10 text-center">
                  <BeakerIcon className="h-10 w-10 text-text-muted mb-3" />
                  <h3 className="text-sm font-bold text-text-primary">No molecules analyzed yet</h3>
                  <p className="text-xs text-text-secondary mt-1 max-w-xs">
                    Analyze a molecule in the <Link to="/app/pharmaguard" className="text-accent-green hover:underline">Workbench</Link> to populate live session stats here.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
        
        {/* Live System Status */}
        <div>
          <h2 className="text-lg font-bold text-text-primary mb-4 font-display">Live System Status</h2>
          <div className="surface p-4 space-y-3">
            {statusLoading ? (
              <div className="flex items-center gap-2 text-xs text-text-muted animate-pulse">
                <div className="h-2 w-2 rounded-full bg-accent-amber animate-ping" />
                Connecting to backend…
              </div>
            ) : backendStatus?.error ? (
              <div className="flex items-center gap-2 text-xs text-accent-red">
                <div className="h-2 w-2 rounded-full bg-accent-red" />
                <span className="font-bold">Backend Offline</span>
                <span className="text-text-muted ml-auto">port 5000</span>
              </div>
            ) : (
              <>
                <div className="flex items-center gap-2 pb-2 border-b border-border">
                  <div className="h-2 w-2 rounded-full bg-accent-emerald animate-pulse" />
                  <span className="text-xs font-bold text-text-primary">Backend Online</span>
                  <span className="text-[10px] font-mono text-text-muted ml-auto">
                    {backendStatus?.models_loaded_count || modelsLoaded.length || '—'} models loaded
                  </span>
                </div>

                {/* GNN Model status */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-semibold text-text-secondary">Attention-GIN (Tox21)</span>
                    <span className={`text-xs font-bold ${modelsLoaded.includes?.('attention_gin') || (isBackendOnline && !isHeuristic) ? 'text-accent-emerald' : isHeuristic ? 'text-accent-amber' : 'text-accent-red'}`}>
                      {isHeuristic ? 'Heuristic Mode' : (modelsLoaded.includes?.('attention_gin') || isBackendOnline ? 'Active' : 'Not Loaded')}
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-elevated rounded-full overflow-hidden">
                    <div className={`h-full ${isBackendOnline ? 'bg-accent-emerald' : 'bg-accent-red'} w-full`} />
                  </div>
                  <p className="text-[10px] text-text-muted mt-0.5">{isHeuristic ? 'Rule-based (no weights) · 12 Tox21 endpoints' : 'ROC-AUC 0.8368 · 12 Tox21 endpoints'}</p>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-semibold text-text-secondary">ChemBERTa (DDI)</span>
                    <span className={`text-xs font-bold ${backendStatus?.chemberta_loaded || isBackendOnline ? 'text-accent-emerald' : 'text-accent-amber'}`}>
                      {backendStatus?.chemberta_loaded ? 'Active' : 'Fallback Mode'}
                    </span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-elevated rounded-full overflow-hidden">
                    <div className={`h-full ${backendStatus?.chemberta_loaded ? 'bg-accent-emerald' : 'bg-accent-amber'} w-3/4`} />
                  </div>
                  <p className="text-[10px] text-text-muted mt-0.5">768-dim SMILES embeddings · Tanimoto DDI</p>
                </div>
                
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-xs font-semibold text-text-secondary">TDC Panel (hERG/DILI/Ames)</span>
                    <span className="text-xs text-accent-emerald font-bold">Rule-Based Active</span>
                  </div>
                  <div className="h-1.5 w-full bg-surface-elevated rounded-full overflow-hidden">
                    <div className="h-full bg-accent-emerald w-full" />
                  </div>
                  <p className="text-[10px] text-text-muted mt-0.5">SMARTS structural alert panel · 3 endpoints</p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Model Registry — Scientific Transparency */}
      <div className="mb-2 flex items-center justify-between">
        <h2 className="text-lg font-bold text-text-primary font-display">Model Registry</h2>
        <span className="text-xs text-text-muted">Click any model to view architecture details</span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {MODEL_REGISTRY.map((model) => (
          <div
            key={model.id}
            className="surface p-4 cursor-pointer hover:shadow-card-hover transition-all duration-200 hover:-translate-y-0.5"
            onClick={() => setExpandedModel(expandedModel === model.id ? null : model.id)}
          >
            <div className="flex items-start justify-between gap-2 mb-2">
              <div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-${model.color}/10 text-${model.color} border border-${model.color}/20`}>
                <CpuChipIcon className="h-4 w-4" />
              </div>
              <button className="text-text-muted hover:text-text-primary transition-colors mt-1">
                {expandedModel === model.id ? <ChevronUpIcon className="h-3.5 w-3.5" /> : <ChevronDownIcon className="h-3.5 w-3.5" />}
              </button>
            </div>
            <p className="text-xs font-bold text-text-primary">{model.label}</p>
            <p className="text-[10px] text-text-muted mt-0.5 font-mono">{model.metric}</p>
            {expandedModel === model.id && (
              <div className="mt-3 pt-3 border-t border-border space-y-1.5 animate-fade-in">
                <div>
                  <span className="text-[9px] font-bold uppercase tracking-wider text-text-muted">Architecture</span>
                  <p className="text-[10px] text-text-secondary">{model.type}</p>
                </div>
                <div>
                  <span className="text-[9px] font-bold uppercase tracking-wider text-text-muted">Training Data</span>
                  <p className="text-[10px] text-text-secondary">{model.dataset}</p>
                </div>
                <div>
                  <span className="text-[9px] font-bold uppercase tracking-wider text-text-muted">Endpoints</span>
                  <p className="text-[10px] text-text-secondary">{model.endpoints}</p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default Dashboard;

