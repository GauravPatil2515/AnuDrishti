import React, { useState, useEffect } from 'react';
import WhatIfOptimizer from '../components/WhatIfOptimizer';
import { useAnalysis } from '../App';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRightIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import api from '../api';

export default function WhatIfPage() {
  const { lastAnalysis, addAnalysis } = useAnalysis();
  const navigate = useNavigate();

  const [smiles, setSmiles] = useState(lastAnalysis?.smiles || '');
  const [whatif, setWhatif] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (lastAnalysis?.smiles && !smiles) {
      setSmiles(lastAnalysis.smiles);
    }
  }, [lastAnalysis, smiles]);

  const generateVariants = async () => {
    if (!smiles.trim()) {
      toast.error('Enter a SMILES string first');
      return;
    }
    setLoading(true);
    try {
      const res = await api.post('/api/optimize/what-if', {
        smiles: smiles.trim(),
        n_variants: 6,
      });
      setWhatif(res.data);
      toast.success('Optimization candidates generated');
    } catch (e) {
      toast.error(e.response?.data?.error || 'Optimization failed');
      setWhatif(null);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyzeVariant = (candidate) => {
    // Push counterfactual to AnalysisContext and navigate to Safety
    const newAnalysis = {
      smiles: candidate.modified_smiles,
      predictions: candidate.predictions,
      triage: candidate.toxicity_probability >= 0.7 ? 'RED'
        : candidate.toxicity_probability >= 0.5 ? 'YELLOW' : 'GREEN',
      explanation: candidate.prediction_explanation || lastAnalysis?.explanation,
      source: 'whatif',
    };
    addAnalysis(newAnalysis);
    navigate('/app/safety');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <nav className="flex items-center space-x-2 text-xs text-text-muted">
        <Link to="/app/analyze" className="hover:text-text-primary">Analyze</Link>
        <span>/</span>
        <span className="text-text-primary font-semibold">What-If Optimizer</span>
      </nav>

      <div>
        <h1 className="text-2xl font-bold font-display text-text-primary">What-If Optimizer</h1>
        <p className="text-sm text-text-muted mt-1">Counterfactual molecule design</p>
      </div>

      <div className="surface rounded-xl border border-border p-4 space-y-3">
        <label className="block text-xs font-semibold uppercase tracking-wider text-text-muted">
          Starting Molecule (SMILES)
        </label>
        <input
          value={smiles}
          onChange={(e) => setSmiles(e.target.value)}
          placeholder="e.g. CC(=O)Oc1ccccc1C(=O)O"
          className="w-full rounded-lg bg-surface border border-border px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:border-accent-green"
        />
        <button
          onClick={generateVariants}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-green text-canvas rounded-lg hover:opacity-90 disabled:opacity-50 transition-colors"
        >
          <SparklesIcon className="h-4 w-4" />
          {loading ? 'Generating…' : 'Generate Safer Variants'}
        </button>
      </div>

      {whatif && (
        <>
          <WhatIfOptimizer whatif={whatif} />
          <div className="space-y-2">
            {whatif.candidates?.map((c, i) => (
              <div
                key={i}
                className="flex items-center justify-between surface-elevated rounded-lg border border-border px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-text-primary truncate">
                    {c.modification_description}
                  </p>
                  <code className="text-[10px] text-text-muted break-all">{c.modified_smiles}</code>
                </div>
                <button
                  onClick={() => handleAnalyzeVariant(c)}
                  className="flex items-center gap-1 text-xs font-medium text-accent-green hover:bg-accent-green/10 border border-accent-green/30 rounded-lg px-2.5 py-1.5 transition-colors shrink-0"
                >
                  Analyze <ArrowRightIcon className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
