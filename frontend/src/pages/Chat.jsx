import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import { clsx } from 'clsx';
import { useNavigate } from 'react-router-dom';
import { toast } from 'react-hot-toast';
import {
  ChatBubbleLeftRightIcon, PaperAirplaneIcon, SparklesIcon,
  BeakerIcon, ShieldCheckIcon, ShieldExclamationIcon,
  CheckBadgeIcon, MagnifyingGlassIcon, ClipboardDocumentIcon,
  ChevronDownIcon, ChevronUpIcon, CpuChipIcon, ArrowRightIcon,
  ExclamationCircleIcon, InformationCircleIcon,
  AcademicCapIcon, MagnifyingGlassCircleIcon, BoltIcon
} from '@heroicons/react/24/outline';

const SUGGESTED_PROMPTS = [
  {
    title: "Drug-Drug Interaction (DDI)",
    prompt: "Do Aspirin and Warfarin interact with each other?",
    icon: ShieldExclamationIcon,
    tag: "DDI Interaction"
  },
  {
    title: "hERG Cardiotoxicity Audit",
    prompt: "Is Caffeine safe for hERG potassium channel cardiotoxicity?",
    icon: ShieldCheckIcon,
    tag: "Cardio Safety"
  },
  {
    title: "Ames Mutagenicity Test",
    prompt: "Does Aspirin pass Ames bacterial mutagenicity screening?",
    icon: BeakerIcon,
    tag: "Genotoxicity"
  },
  {
    title: "What-If Toxicity Reduction",
    prompt: "Suggest bioisosteric modifications to lower drug toxicity while preserving drug-likeness.",
    icon: SparklesIcon,
    tag: "Optimization"
  },
  {
    title: "Target Profiling / MoA",
    prompt: "What protein targets does Aspirin bind to?",
    icon: AcademicCapIcon,
    tag: "Mechanism of Action"
  },
  {
    title: "Clinical DDI Check",
    prompt: "Show clinical DDI between Warfarin and Aspirin from NIH RxNav",
    icon: BoltIcon,
    tag: "Clinical DDI"
  },
  {
    title: "Literature Evidence",
    prompt: "Show me PubMed studies on Aspirin toxicity mechanism",
    icon: MagnifyingGlassCircleIcon,
    tag: "PubMed RAG"
  }
];

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: "Welcome to **AnuDrishti Agentic Assistant**. I am your ChemBERTa-augmented computational toxicology & drug interaction co-pilot.\n\nAsk me any question, compare two drugs for Drug-Drug Interactions (DDI), or analyze hERG/DILI/Ames endpoints.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      isInitial: true
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [activeSmiles, setActiveSmiles] = useState('');
  const [activeCompoundName, setActiveCompoundName] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedTraces, setExpandedTraces] = useState({});
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const toggleTrace = (id) => {
    setExpandedTraces(prev => ({ ...prev, [id]: !prev[id] }));
  };

  // Render structured prediction cards for comparison
  const renderComparisonCards = (parsedIntent, ddiData) => {
    const entities = parsedIntent?.entities || [];
    if (entities.length < 2) return null;
    
    const mol1 = entities[0];
    const mol2 = entities[1];
    
    return (
      <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-3">
        {entities.map((smiles, idx) => (
          <div key={idx} className="surface p-3 rounded-lg border border-border">
            <div className="flex items-center justify-between mb-2">
              <span className="font-semibold text-text-primary text-xs">Molecule {idx + 1}</span>
              <span className="pill pill-emerald text-[9px] font-mono">{smiles.slice(0, 20)}...</span>
            </div>
            <code className="font-mono text-[10px] text-text-muted break-all block mb-2">{smiles}</code>
            {/* Prediction would come from parsed_intent or separate call */}
          </div>
        ))}
      </div>
    );
  };

  // Render DDI structured card
  const renderDDICard = (ddi) => {
    if (!ddi || !ddi.success) return null;
    
    const metrics = ddi.metrics || {};
    const riskLevel = metrics.risk_level || 'UNKNOWN';
    const riskColor = riskLevel === 'HIGH' ? 'accent-red' : riskLevel === 'MODERATE' ? 'accent-amber' : 'accent-emerald';
    
    return (
      <div className="mt-3 p-3 rounded-lg bg-surface border border-border space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldExclamationIcon className="h-4 w-4 text-accent-amber" />
            <span className="font-bold text-xs uppercase tracking-wider">Drug-Drug Interaction Risk</span>
          </div>
          <span className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded uppercase border bg-${riskColor}/10 text-${riskColor} border-${riskColor}/30`}>
            {riskLevel} RISK ({(metrics.interaction_risk_score * 100).toFixed(0)}%)
          </span>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
          {ddi.molecules?.map((mol, idx) => (
            <div key={idx} className="p-2 rounded bg-surface-elevated border border-border">
              <p className="font-semibold text-text-primary text-[11px]">{mol.name}</p>
              <code className="font-mono text-[10px] text-text-muted break-all">{mol.smiles}</code>
              {mol.alerts?.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {mol.alerts.map((al, aIdx) => (
                    <span key={aIdx} className="text-[9px] font-mono px-1 py-0.25 rounded bg-accent-amber/10 text-accent-amber border border-accent-amber/20">
                      {typeof al === 'string' ? al : al.name}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
        
        <div className="flex items-center justify-between pt-2 border-t border-border/50 text-[10px] font-mono text-text-muted">
          <span>ChemBERTa Cosine Sim: <strong className="text-accent-green">{metrics.chemberta_cosine_similarity}</strong></span>
          <span>Tanimoto Sim: <strong className="text-text-primary">{metrics.tanimoto_similarity}</strong></span>
        </div>
      </div>
    );
  };

  // Render TDC endpoints card
  const renderTDCCard = (tdcPredictions) => {
    if (!tdcPredictions) return null;
    
    return (
      <div className="mt-3 pt-3 border-t border-border space-y-2">
        <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
          TDC Regulatory Safety Endpoints
        </p>
        <div className="grid grid-cols-3 gap-2">
          {Object.entries(tdcPredictions).map(([endpoint, data]) => {
            const prob = data.probability || 0;
            const riskColor = prob >= 0.6 ? 'text-accent-red border-accent-red/30 bg-accent-red/10'
              : prob >= 0.3 ? 'text-accent-amber border-accent-amber/30 bg-accent-amber/10'
              : 'text-accent-emerald border-accent-emerald/30 bg-accent-emerald/10';
            return (
              <div key={endpoint} className={clsx('p-2 rounded-lg border text-center', riskColor)}>
                <p className="text-[10px] font-bold uppercase tracking-wider opacity-80">{endpoint}</p>
                <p className="font-mono text-sm font-black mt-0.5">{(prob * 100).toFixed(0)}%</p>
                <p className="text-[9px] opacity-75 capitalize">{data.risk_level} Risk</p>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  // Render Target Profiling / MoA card
  const renderTargetCard = (targetData) => {
    if (!targetData || !targetData.targets || targetData.targets.length === 0) return null;
    
    const toxicityTargets = targetData.targets.filter(t => t.is_toxicity_relevant);
    const otherTargets = targetData.targets.filter(t => !t.is_toxicity_relevant);
    
    return (
      <div className="mt-3 pt-3 border-t border-border space-y-2">
        <div className="flex items-center gap-2">
          <AcademicCapIcon className="h-4 w-4 text-accent-purple" />
          <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
            Target Profiling / MoA (ChEMBL)
          </span>
          <span className="text-[10px] font-mono text-accent-purple">
            {targetData.targets.length} targets
          </span>
        </div>
        
        {toxicityTargets.length > 0 && (
          <div className="space-y-1">
            <p className="text-[10px] font-semibold text-accent-red">⚠️ Toxicity-Relevant Targets</p>
            {toxicityTargets.slice(0, 5).map((t, idx) => (
              <div key={idx} className="p-2 rounded bg-accent-red/5 border border-accent-red/20">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-text-primary text-[10px]">{t.name}</span>
                  <span className="text-[9px] font-mono px-1.5 py-0.25 rounded bg-accent-red/20 text-accent-red border border-accent-red/30">
                    {t.confidence}
                  </span>
                </div>
                <div className="text-[9px] text-text-muted mt-0.5 font-mono">
                  {t.type} • pChEMBL: {t.pchembl_value?.toFixed(1)} • {t.activity_type} {t.activity_value} {t.activity_unit}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {otherTargets.length > 0 && (
          <div className="space-y-1">
            <p className="text-[10px] font-semibold text-text-muted">Other Known Targets</p>
            {otherTargets.slice(0, 3).map((t, idx) => (
              <div key={idx} className="p-2 rounded bg-surface border border-border/50">
                <div className="flex items-center justify-between">
                  <span className="text-text-primary text-[10px]">{t.name}</span>
                  <span className="text-[9px] font-mono px-1.5 py-0.25 rounded bg-surface-elevated text-text-muted border border-border">
                    {t.confidence}
                  </span>
                </div>
                <div className="text-[9px] text-text-muted mt-0.5 font-mono">
                  {t.type} • pChEMBL: {t.pchembl_value?.toFixed(1)}
                </div>
              </div>
            ))}
            {otherTargets.length > 3 && (
              <p className="text-[9px] text-text-muted italic">+ {otherTargets.length - 3} more targets</p>
            )}
          </div>
        )}
        
        {targetData.moa_summary && (
          <div className="mt-2 p-2 rounded bg-accent-purple/5 border border-accent-purple/20">
            <p className="text-[10px] font-semibold text-accent-purple">🧬 Inferred MoA</p>
            <p className="text-[10px] text-text-secondary mt-1">{targetData.moa_summary}</p>
          </div>
        )}
      </div>
    );
  };

  // Render Literature Evidence card
  const renderLiteratureCard = (literatureData) => {
    if (!literatureData || !literatureData.articles || literatureData.articles.length === 0) return null;
    
    return (
      <div className="mt-3 pt-3 border-t border-border space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MagnifyingGlassCircleIcon className="h-4 w-4 text-accent-blue" />
            <span className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
              Literature Evidence (PubMed)
            </span>
          </div>
          <span className="text-[9px] font-mono text-text-muted">
            {literatureData.total_found} found • {literatureData.search_time_ms}ms
          </span>
        </div>
        
        <div className="space-y-2">
          {literatureData.articles.map((article, idx) => (
            <div key={idx} className="p-2 rounded bg-surface border border-border/50">
              <p className="font-semibold text-text-primary text-[10px] line-clamp-1">
                {article.title}
              </p>
              <p className="text-[9px] text-text-muted mt-0.5 font-mono">
                {article.authors.slice(0, 3).join(', ')}{article.authors.length > 3 ? ' et al.' : ''} • {article.journal} ({article.pub_date})
              </p>
              <p className="text-[9px] text-text-secondary mt-1 line-clamp-2">
                {article.abstract?.slice(0, 200)}...
              </p>
              {article.mesh_terms && article.mesh_terms.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {article.mesh_terms.slice(0, 3).map((mesh, mIdx) => (
                    <span key={mIdx} className="text-[8px] px-1 py-0.25 rounded bg-accent-blue/10 text-accent-blue border border-accent-blue/20">
                      {mesh}
                    </span>
                  ))}
                </div>
              )}
              {article.doi && (
                <a 
                  href={`https://doi.org/${article.doi}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[9px] text-accent-blue hover:underline mt-1 inline-block font-mono"
                >
                  DOI: {article.doi}
                </a>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  // Render agent trace accordion
  const renderTraceAccordion = (trace, messageId) => {
    if (!trace || trace.length === 0) return null;
    
    return (
      <div className="mt-3 pt-2 border-t border-border/50">
        <button
          onClick={() => toggleTrace(messageId)}
          className="flex items-center gap-1.5 text-[10px] font-mono font-semibold text-accent-green hover:underline focus:outline-none"
        >
          <CpuChipIcon className="h-3.5 w-3.5" />
          <span>{expandedTraces[messageId] ? 'Hide Agent Thought Trace' : `Show Agent Thought Trace (${trace.length} steps)`}</span>
          {expandedTraces[messageId] ? <ChevronUpIcon className="h-3 w-3" /> : <ChevronDownIcon className="h-3 w-3" />}
        </button>

        {expandedTraces[messageId] && (
          <div className="mt-2 p-2 rounded-lg bg-surface border border-border space-y-1 font-mono text-[10px]">
            {trace.map((step, sIdx) => (
              <div key={sIdx} className="flex items-start gap-2 text-text-secondary">
                <span className="text-accent-green font-bold shrink-0">[{step.step}]</span>
                <span className="font-semibold text-text-primary shrink-0">{step.agent}:</span>
                <span className="text-text-muted">{step.action}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  };

  // Render suggestions chips
  const renderSuggestions = (suggestions, onSend) => {
    if (!suggestions || suggestions.length === 0) return null;
    
    return (
      <div className="mt-3 flex flex-wrap gap-2">
        {suggestions.map((s, idx) => (
          <button
            key={idx}
            onClick={() => onSend(s)}
            className="pill pill-emerald text-[10px] font-mono hover:bg-accent-green/20 transition-colors"
          >
            {s}
          </button>
        ))}
      </div>
    );
  };



  // Render single molecule analysis card
  const renderAnalysisCard = (analysis) => {
    if (!analysis) return null;

    const summary = analysis.summary || {};
    const triage = analysis.triage || {};
    const explanation = analysis.explanation || {};
    const predictions = analysis.predictions || {};
    const ood = analysis.ood || {};

    const toxicityProb = summary?.average_toxicity_probability || 0;
    const riskLevel = triage?.category || 'GREEN';
    const riskColor = riskLevel === 'RED' ? 'accent-red' : riskLevel === 'YELLOW' ? 'accent-amber' : 'accent-emerald';
    const efsScore = explanation?.faithfulness_score || explanation?.efs || 0;
    const isOod = ood?.is_ood ?? false;

    return (
      <div className="mt-3 p-3 rounded-lg bg-surface border border-border space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BeakerIcon className="h-4 w-4 text-accent-amber" />
            <span className="font-bold text-xs uppercase tracking-wider">Molecular Analysis</span>
          </div>
          <span className={`font-mono text-[10px] font-bold px-2 py-0.5 rounded uppercase border bg-${riskColor}/10 text-${riskColor} border-${riskColor}/30`}>
            {riskLevel} RISK ({(toxicityProb * 100).toFixed(0)}%)
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
          <div className="p-2 rounded bg-surface-elevated border border-border">
            <p className="font-semibold text-text-primary text-[11px]">SMILES</p>
            <code className="font-mono text-[10px] text-text-muted break-all">{analysis.smiles?.slice(0, 30)}${analysis.smiles?.length > 30 ? '...' : ''}</code>
          </div>
          <div className="p-2 rounded bg-surface-elevated border border-border">
            <p className="font-semibold text-text-primary text-[11px]">Overall Assessment</p>
            <p className="font-mono text-sm">{summary?.overall_assessment || 'Unknown'}</p>
          </div>
        </div>

        {Object.keys(predictions).length > 0 && (
          <div className="mt-2 pt-2 border-t border-border/50">
            <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted">Endpoint Predictions</p>
            <div className="space-y-1">
              {Object.entries(predictions).slice(0, 5).map(([endpoint, data]) => {
                if (typeof data === 'object' && data !== null && 'probability' in data) {
                  const prob = data.probability || 0;
                  const isToxic = prob > 0.5;
                  return (
                    <div key={endpoint} className="flex items-center justify-between px-2 py-1 text-[9px]">
                      <span className="font-mono">{endpoint}</span>
                      <span className={`text-right ${isToxic ? 'text-accent-red' : 'text-accent-emerald'}`}>{(prob * 100).toFixed(0)}%</span>
                    </div>
                  );
                }
                return null;
              })}
              {Object.keys(predictions).length > 5 && (
                <div className="text-[9px] text-text-muted italic mt-1">
                  + {Object.keys(predictions).length - 5} more endpoints
                </div>
              )}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between pt-2 border-t border-border/50 text-[10px] font-mono text-text-muted">
          <span>EFS Score: <strong className={`${efsScore >= 0.8 ? 'text-accent-emerald' : efsScore >= 0.6 ? 'text-accent-amber' : 'text-accent-red'}`}>
            {(efsScore * 100).toFixed(0)}%
          </strong></span>
          <span>OOD: <strong className={isOod ? 'text-accent-red' : 'text-accent-emerald'}>
            {isOod ? 'YES' : 'NO'}
          </strong></span>
        </div>
      </div>
    );
  };
  const handleSend = async (queryText) => {
    const textToSend = queryText || inputQuery;
    if (!textToSend.trim() || loading) return;

    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: textToSend.trim(),
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!queryText) setInputQuery('');
    setLoading(true);

    try {
      // Step 1: Query NLP service
      const queryRes = await api.post('/api/query', { query: textToSend });
      const qData = queryRes.data;

      let replyText = qData.response || '';
      let singleAnalysis = null;

      // Check if SMILES context or single molecule prediction is needed.
      // Heuristic: treat as SMILES only if it contains SMILES-specific characters,
      // has NO spaces (drug names always have spaces or are single words), and is > 10 chars.
      const isSmiles = !textToSend.includes(' ') && textToSend.length > 10 && /[()\[\]=#@\/\.]/.test(textToSend);
      let targetSmiles = activeSmiles;
      let targetName = activeCompoundName;

      if (isSmiles && textToSend.length > 3 && !textToSend.includes(' ')) {
        targetSmiles = textToSend.trim();
        setActiveSmiles(targetSmiles);
      }

      if (targetSmiles && !qData.ddi_data) {
        try {
          const res = await api.post('/api/analyze/single', { smiles: targetSmiles, include_explanation: true });
          singleAnalysis = res.data.analysis;
          if (singleAnalysis?.explanation?.executive_summary) {
            replyText = `**Analysis for ${targetName ? targetName.toUpperCase() : 'Molecule'}** (${targetSmiles}):\n\n${singleAnalysis.explanation.executive_summary}`;
            if (singleAnalysis.explanation.mechanism) {
              replyText += `\n\n**Biochemical Mechanism:**\n${singleAnalysis.explanation.mechanism}`;
            }
          }
        } catch (err) {
          console.error("Single analysis error:", err);
        }
      }

      const assistantMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        analysis: singleAnalysis,
        ddi: qData.ddi_data,
        target_data: qData.target_data,
        literature_data: qData.literature_data,
        trace: qData.trace || [],
        smiles: targetSmiles,
        compoundName: targetName,
        parsed_intent: qData.parsed_intent,
        efs: singleAnalysis?.explanation?.faithfulness_score || qData.parsed_intent?.efs_score || 0.5,
        validation_passed: singleAnalysis?.explanation?.validation_passed ?? (qData.parsed_intent?.validation_passed ?? false),
        suggestions: qData.suggestions
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (e) {
      console.error('Chat query failed:', e);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        text: "I encountered an error querying the model backend. Please ensure the Python backend is running on port 5000.",
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        isError: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleCompoundLookup = async (name) => {
    if (!name.trim()) return;
    setLoading(true);
    try {
      const res = await api.post('/api/lookup/smiles', { name: name.trim() });
      if (res.data?.canonical_smiles) {
        setActiveSmiles(res.data.canonical_smiles);
        setActiveCompoundName(name.trim());
        toast.success(`Loaded SMILES for ${name}`);
        handleSend(`Analyze safety profile for ${name}`);
      } else {
        toast.error(`Could not resolve compound name "${name}"`);
      }
    } catch (e) {
      toast.error("PubChem lookup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-5xl p-4 sm:p-6 lg:p-8 space-y-4 animate-fade-in min-h-[calc(100vh-4rem)] flex flex-col">
      {/* Header bar with compound active context */}
      <div className="surface p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 shadow-sm rounded-xl border border-border">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-green/10 text-accent-green border border-accent-green/20">
            <ChatBubbleLeftRightIcon className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-base font-bold text-text-primary font-display flex items-center gap-2">
              AnuDrishti Agentic Assistant
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-accent-green/10 text-accent-green border border-accent-green/20">
                ChemBERTa + Agent RAG
              </span>
            </h1>
            <p className="text-xs text-text-muted">Agentic Reasoning & Drug-Drug Interaction (DDI) Screening</p>
          </div>
        </div>

        {/* Quick Compound Lookup Input */}
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <div className="relative flex-1 sm:w-64">
            <MagnifyingGlassIcon className="absolute left-3 top-2.5 h-4 w-4 text-text-muted" />
            <input
              type="text"
              placeholder="Search drug (e.g. Aspirin)..."
              value={activeCompoundName}
              onChange={(e) => setActiveCompoundName(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleCompoundLookup(activeCompoundName)}
              className="w-full bg-surface-elevated border border-border rounded-lg pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none focus:border-accent-green"
            />
          </div>
          <button
            onClick={() => handleCompoundLookup(activeCompoundName)}
            disabled={loading || !activeCompoundName}
            className="btn btn-secondary text-xs py-1.5 px-3"
          >
            Load
          </button>
        </div>
      </div>

      {/* Active Molecule Badge Bar */}
      {activeSmiles && (
        <div className="flex items-center justify-between px-4 py-2 rounded-lg bg-surface-elevated border border-border text-xs">
          <div className="flex items-center gap-2 overflow-hidden">
            <BeakerIcon className="h-4 w-4 text-accent-green shrink-0" />
            <span className="font-semibold text-text-primary">Active Molecule:</span>
            <code className="font-mono text-accent-green truncate">{activeSmiles}</code>
          </div>
          <button
            onClick={() => { setActiveSmiles(''); setActiveCompoundName(''); }}
            className="text-[10px] text-text-muted hover:text-text-primary transition-colors"
          >
            Clear Context
          </button>
        </div>
      )}

      {/* Main Messages Container */}
      <div className="flex-1 surface rounded-xl border border-border p-4 overflow-y-auto space-y-4 min-h-[380px] max-h-[550px]">
        {messages.map((m) => (
          <div
            key={m.id}
            className={clsx(
              "flex flex-col gap-2 transition-all duration-150",
              m.sender === 'user' ? "items-end" : "items-start"
            )}
          >
            <div className="flex items-center gap-2 text-[10px] text-text-muted px-1">
              <span className="font-bold uppercase tracking-wider">
                {m.sender === 'user' ? 'Researcher' : 'AnuDrishti AI Agent'}
              </span>
              <span>•</span>
              <span>{m.timestamp}</span>
              {m.efs && m.sender === 'assistant' && (
                m.validation_passed ? (
                  <span className="inline-flex items-center gap-1 font-mono text-[9px] px-1.5 py-0.25 rounded bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20">
                    <CheckBadgeIcon className="h-3 w-3" />
                    EFS {(m.efs * 100).toFixed(0)}% VERIFIED
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 font-mono text-[9px] px-1.5 py-0.25 rounded bg-accent-amber/10 text-accent-amber border border-accent-amber/20">
                    EFS ~{(m.efs * 100).toFixed(0)}% ESTIMATED
                  </span>
                )
              )}
            </div>

            <div
              className={clsx(
                "rounded-xl p-4 text-xs max-w-2xl leading-relaxed shadow-sm border",
                m.sender === 'user'
                  ? "bg-accent-green/10 text-text-primary border-accent-green/20 rounded-tr-none"
                  : "bg-surface-elevated text-text-primary border-border rounded-tl-none space-y-3"
              )}
            >
              {/* Text Body */}
              <div className="whitespace-pre-wrap font-sans">
                {m.text.replace(/\*\*/g, '').replace(/#+\s/g, '')}
              </div>

              
              {/* Analysis Card (If single molecule analysis present) */}
              {renderAnalysisCard(m.analysis)}

{/* DDI Alert Card (If Drug-Drug Interaction present) */}
              {renderDDICard(m.ddi)}

              {/* TDC Safety Endpoints Card (If available in single analysis) */}
              {renderTDCCard(m.analysis?.predictions?.tdc_predictions)}

              {/* Target Profiling / MoA Card */}
              {renderTargetCard(m.target_data)}

              {/* Literature Evidence Card */}
              {renderLiteratureCard(m.literature_data)}

              {/* Comparison cards from parsed_intent */}
              {renderComparisonCards(m.parsed_intent, m.ddi)}

              {/* Agent Reasoning Trace Accordion */}
              {renderTraceAccordion(m.trace, m.id)}

              {/* Suggestions chips */}
              {m.suggestions && renderSuggestions(m.suggestions, handleSend)}

              {/* Action buttons on assistant message */}
              {m.sender === 'assistant' && !m.isInitial && (
                <div className="flex items-center gap-2 pt-2 text-[10px] text-text-muted">
                  <button
                    onClick={() => {
                      navigator.clipboard.writeText(m.text);
                      toast.success('Response copied to clipboard');
                    }}
                    className="flex items-center gap-1 hover:text-text-primary transition-colors"
                  >
                    <ClipboardDocumentIcon className="h-3 w-3" />
                    Copy
                  </button>
                  {m.analysis && (
                    <button
                      onClick={() => {
                        if (m.analysis?.smiles) {
                          window.dispatchEvent(new CustomEvent('pharmaguard-open-analysis', {
                            detail: { analysis: m.analysis, source: 'chat' }
                          }));
                          navigate('/app/safety');
                        }
                      }}
                      className="flex items-center gap-1 hover:text-accent-green transition-colors"
                    >
                      <ArrowRightIcon className="h-3 w-3" />
                      Open in Workbench
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3 p-3 rounded-xl bg-surface-elevated border border-border w-fit animate-pulse">
            <div className="h-4 w-4 rounded-full border-2 border-accent-green border-t-transparent animate-spin" />
            <span className="text-xs text-text-muted font-mono">Running ChemBERTa embeddings & Agentic DDI reasoning…</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Prompts Cards (Shown when history is short) */}
      {messages.length <= 2 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {SUGGESTED_PROMPTS.map((p, idx) => (
            <div
              key={idx}
              onClick={() => handleSend(p.prompt)}
              className="surface p-3 rounded-xl border border-border hover:border-accent-green/40 hover:bg-surface-hover cursor-pointer transition-all duration-150 group"
            >
              <div className="flex items-center justify-between mb-1.5">
                <p.icon className="h-4 w-4 text-accent-green group-hover:scale-110 transition-transform" />
                <span className="text-[9px] font-mono font-semibold uppercase px-1.5 py-0.5 rounded bg-surface-elevated border border-border text-text-muted">
                  {p.tag}
                </span>
              </div>
              <p className="text-xs font-semibold text-text-primary group-hover:text-accent-green transition-colors">
                {p.title}
              </p>
              <p className="text-[11px] text-text-muted mt-1 line-clamp-2">
                "{p.prompt}"
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Chat Input Field */}
      <div className="surface p-2.5 rounded-xl border border-border flex items-center gap-2 shadow-sm">
        <input
          ref={inputRef}
          type="text"
          value={inputQuery}
          onChange={(e) => setInputQuery(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask a question, enter a drug name, or type e.g. 'Do Aspirin and Warfarin interact?'..."
          className="flex-1 bg-transparent border-0 px-3 py-1.5 text-xs text-text-primary placeholder:text-text-muted focus:outline-none"
        />
        <button
          onClick={() => handleSend()}
          disabled={loading || !inputQuery.trim()}
          className="btn btn-primary text-xs py-2 px-4 rounded-lg"
        >
          <PaperAirplaneIcon className="h-4 w-4" />
          <span>Send</span>
        </button>
      </div>
    </div>
  );
};

export default Chat;
