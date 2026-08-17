import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ShieldCheckIcon,
  BeakerIcon,
  SparklesIcon,
  CpuChipIcon,
  CheckBadgeIcon,
  ArrowRightIcon,
  AdjustmentsHorizontalIcon,
  SignalIcon,
  PlayIcon
} from '@heroicons/react/24/outline';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-canvas text-primary font-sans selection:bg-indigo-500 selection:text-primary">
      {/* Background - following Linear's dark glassmorphism */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden bg-canvas">
        <div className="absolute inset-0 bg-[url('https://linear.app/cdn-cgi/imagedelivery/fO02fVymIlcJF5dCPJW53Q/e6cfc1fb-8b1e-450e-b2d9-1051515efb00/public')] bg-center bg-cover opacity-[0.03]" />
      </div>

      {/* Navigation Bar - Linear style */}
      <header className="relative z-20 border-b border-border bg-surface-elevated/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/app/pharmaguard')}>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600/20 text-indigo-400">
              <ShieldCheckIcon className="h-6 w-6" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-primary">
                PharmaGuard <span className="text-indigo-400">AI</span>
              </span>
              <span className="ml-2 text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-indigo-600/20 text-indigo-400 border border-indigo-500/30">
                SIH 2026
              </span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/app/pharmaguard')}
              className="group inline-flex items-center gap-2 rounded-md bg-transparent px-3 py-1.5 text-sm font-medium text-primary/70 hover:text-primary hover:bg-surface transition-colors"
            >
              <span>Launch Workbench</span>
              <ArrowRightIcon className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-20 mx-auto max-w-7xl px-6 pt-16 pb-24">
        <div className="text-center max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 rounded-md border border-white/10 bg-white/5 px-4 py-1.5 text-xs font-medium text-white/30 backdrop-blur">
            <SparklesIcon className="h-4 w-4 text-indigo-400" />
            <span>Trustworthy Drug-Safety Decision Support</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-white leading-tight">
            GNN Predictions Gated by <br />
            <span className="text-indigo-300">
              Faithful LLM Validation
            </span>
          </h1>

          <p className="text-base text-white/60 leading-relaxed max-w-2xl mx-auto">
            The first AI computational toxicology platform that automatically verifies LLM molecular explanations using counterfactual perturbations and atom attributions before presenting them to scientists.
          </p>

          <div className="pt-6 flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => navigate('/app/pharmaguard')}
              className="btn btn-primary px-6 py-3 text-base"
            >
              <BeakerIcon className="h-5 w-5" />
              <span>Open PharmaGuard AI Workbench</span>
              <ArrowRightIcon className="h-5 w-5" />
            </button>
            <button
              onClick={() => navigate('/app/pharmaguard', { state: { openDemo: true } })}
              className="btn btn-secondary px-6 py-3 text-base"
            >
              <PlayIcon className="h-5 w-5" />
              <span>Try Demo (2 free molecules)</span>
            </button>
          </div>
        </div>

        {/* Feature Highlights Grid - Linear style dense layout */}
        <div className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {/* Multi-Task GNN */}
          <div className="rounded-lg border border-border bg-surface p-4 transition-all hover:border-border-hover hover:bg-surface-elevated">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-indigo-600/10 text-indigo-400 border border-indigo-600/20 mb-3">
              <CpuChipIcon className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-bold text-primary">Multi-Task GNN</h3>
            <p className="mt-2 text-sm text-secondary">
              Attention-GIN multi-task architecture predicting 16 ADMET & toxicity endpoints simultaneously with uncertainty bounds.
            </p>
          </div>

          {/* Faithfulness Gatekeeper */}
          <div className="rounded-lg border border-border bg-surface p-4 transition-all hover:border-border-hover hover:bg-surface-elevated">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-indigo-600/10 text-indigo-400 border border-indigo-600/20 mb-3">
              <CheckBadgeIcon className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-bold text-primary">Faithfulness Gatekeeper</h3>
            <p className="mt-2 text-sm text-secondary">
              Explanation Faithfulness Score (EFS ≥ 0.70) rejects hallucinated LLM claims before presenting explanations to researchers.
            </p>
          </div>

          {/* OOD & Epistemic Band */}
          <div className="rounded-lg border border-border bg-surface p-4 transition-all hover:border-border-hover hover:bg-surface-elevated">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-indigo-600/10 text-indigo-400 border border-indigo-600/20 mb-3">
              <SignalIcon className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-bold text-primary">OOD & Epistemic Band</h3>
            <p className="mt-2 text-sm text-secondary">
              Hybrid Morgan Tanimoto distance + MC-Dropout 95% Confidence Intervals flag novel molecules automatically.
            </p>
          </div>

          {/* What-If Bioisosteres */}
          <div className="rounded-lg border border-border bg-surface p-4 transition-all hover:border-border-hover hover:bg-surface-elevated">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-emerald-600/10 text-emerald-400 border border-emerald-600/20 mb-3">
              <AdjustmentsHorizontalIcon className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-bold text-primary">What-If Bioisosteres</h3>
            <p className="mt-2 text-sm text-secondary">
              Generate molecular perturbations and bioisosteric edits to lower predicted toxicity while maintaining ADMET permeability.
            </p>
          </div>
        </div>

        {/* Technical Details */}
        <div className="mt-20 border-t border-border pt-10">
          <h2 className="text-xl font-bold text-primary mb-6">How It Works</h2>
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-primary">1. Molecular Input</h3>
              <p className="text-secondary">
                Enter a SMILES string or use natural language to describe your compound of interest.
              </p>
              <h3 className="text-lg font-semibold text-primary mt-4">2. Multi-Task Prediction</h3>
              <p className="text-secondary">
                Our GNN simultaneously predicts toxicity, ADMET properties, and provides uncertainty estimates.
              </p>
            </div>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-primary">3. Explanation Generation</h3>
              <p className="text-secondary">
                LLMs generate initial explanations linking substructures to predicted outcomes.
              </p>
              <h3 className="text-lg font-semibold text-primary mt-4">4. Faithfulness Verification</h3>
              <p className="text-secondary">
                Explanations are rigorously verified using counterfactual perturbations before presentation.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Home;