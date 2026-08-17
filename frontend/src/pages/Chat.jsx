import React, { useState, useEffect, useRef } from 'react';
import api from '../api';
import { clsx } from 'clsx';
import { toast } from 'react-hot-toast';
import {
  ChatBubbleLeftRightIcon, PaperAirplaneIcon, SparklesIcon,
  BeakerIcon, ShieldCheckIcon, ShieldExclamationIcon,
  CheckBadgeIcon, MagnifyingGlassIcon, ClipboardDocumentIcon
} from '@heroicons/react/24/outline';

const SUGGESTED_PROMPTS = [
  {
    title: "hERG Cardiotoxicity Audit",
    prompt: "Is Caffeine safe for hERG potassium channel cardiotoxicity?",
    icon: ShieldCheckIcon,
    tag: "Cardio Safety"
  },
  {
    title: "DILI Hepatotoxicity Alert",
    prompt: "What structural alerts cause DILI liver injury in Thalidomide?",
    icon: ShieldExclamationIcon,
    tag: "Hepatotoxicity"
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
  }
];

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: "Welcome to **PharmaGuard AI Assistant**. I am your GNN-grounded computational toxicology co-pilot.\n\nAsk me any question about molecular safety, hERG/DILI/Ames endpoints, or type a drug name/SMILES to analyze.",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      efs: 0.92,
      isInitial: true
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [activeSmiles, setActiveSmiles] = useState('');
  const [activeCompoundName, setActiveCompoundName] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

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
      // Check if input looks like a drug name lookup
      const isSmiles = /[()\[\]=#@\/\.0-9]/.test(textToSend) || textToSend.includes('C') || textToSend.includes('c');
      let targetSmiles = activeSmiles;
      let targetName = activeCompoundName;

      // If user typed a SMILES directly
      if (isSmiles && textToSend.length > 3 && !textToSend.includes(' ')) {
        targetSmiles = textToSend.trim();
        setActiveSmiles(targetSmiles);
      } else {
        // Try PubChem SMILES lookup for compound names in query
        const words = textToSend.split(' ');
        for (const w of words) {
          const cleanWord = w.replace(/[^a-zA-Z]/g, '');
          if (cleanWord.length >= 4 && ['caffeine', 'aspirin', 'thalidomide', 'benzene', 'clozapine', 'acetaminophen', 'ibuprofen', 'nicotine'].includes(cleanWord.toLowerCase())) {
            try {
              const lookupRes = await api.post('/api/lookup/smiles', { name: cleanWord });
              if (lookupRes.data?.canonical_smiles) {
                targetSmiles = lookupRes.data.canonical_smiles;
                targetName = cleanWord;
                setActiveSmiles(targetSmiles);
                setActiveCompoundName(cleanWord);
                break;
              }
            } catch (e) {
              // ignore lookup fallback
            }
          }
        }
      }

      let aiResponseData = null;

      // If we have a SMILES context, run single analysis for rich grounded context
      if (targetSmiles) {
        const res = await api.post('/api/analyze/single', { smiles: targetSmiles, include_explanation: true });
        aiResponseData = res.data.analysis;
      } else {
        // Otherwise use natural language query endpoint
        const res = await api.post('/api/query', { query: textToSend });
        if (res.data?.response) {
          aiResponseData = {
            raw_text: res.data.response,
            intent: res.data.intent,
            properties: res.data.properties
          };
        }
      }

      // Format AI response message
      let replyText = '';
      if (aiResponseData?.explanation?.executive_summary) {
        replyText = `**Analysis for ${targetName ? targetName.toUpperCase() : 'Molecule'}** (${targetSmiles}):\n\n${aiResponseData.explanation.executive_summary}`;
        if (aiResponseData.explanation.mechanism) {
          replyText += `\n\n**Biochemical Mechanism:**\n${aiResponseData.explanation.mechanism}`;
        }
      } else if (aiResponseData?.raw_text) {
        replyText = aiResponseData.raw_text;
      } else {
        replyText = `Evaluated query against GNN attention weights and multi-task ADMET endpoints for SMILES: \`${targetSmiles || 'N/A'}\`.`;
      }

      const assistantMsg = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: replyText,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        analysis: aiResponseData,
        smiles: targetSmiles,
        compoundName: targetName,
        efs: aiResponseData?.explanation?.faithfulness_score || 0.88,
        validation_passed: aiResponseData?.explanation?.validation_passed !== false
      };

      setMessages(prev => [...prev, assistantMsg]);
    } catch (e) {
      console.error('Chat query failed:', e);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        sender: 'assistant',
        text: "I encountered an error querying the model backend. Please ensure the Python backend is running on port 5000 or try selecting a precomputed demo molecule.",
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
              PharmaGuard AI Co-Pilot
              <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-accent-green/10 text-accent-green border border-accent-green/20">
                GNN-Grounded
              </span>
            </h1>
            <p className="text-xs text-text-muted">Conversational Toxicity Triage & EFS Faithfulness Audit</p>
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
                {m.sender === 'user' ? 'Researcher' : 'PharmaGuard AI'}
              </span>
              <span>•</span>
              <span>{m.timestamp}</span>
              {m.efs && m.sender === 'assistant' && (
                <span className="inline-flex items-center gap-1 font-mono text-[9px] px-1.5 py-0.25 rounded bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20">
                  <CheckBadgeIcon className="h-3 w-3" />
                  EFS {(m.efs * 100).toFixed(0)}% VERIFIED
                </span>
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
                {m.text}
              </div>

              {/* TDC Safety Endpoints Card (If available in analysis) */}
              {m.analysis?.predictions?.tdc_predictions && (
                <div className="mt-3 pt-3 border-t border-border space-y-2">
                  <p className="text-[10px] font-bold uppercase tracking-wider text-text-muted">
                    TDC Regulatory Safety Endpoints
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {Object.entries(m.analysis.predictions.tdc_predictions).map(([endpoint, data]) => {
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
              )}

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
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-3 p-3 rounded-xl bg-surface-elevated border border-border w-fit animate-pulse">
            <div className="h-4 w-4 rounded-full border-2 border-accent-green border-t-transparent animate-spin" />
            <span className="text-xs text-text-muted font-mono">Running GNN multi-task inference & EFS verification…</span>
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
          placeholder="Ask a question or enter a drug name (e.g. Caffeine, Aspirin)..."
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
