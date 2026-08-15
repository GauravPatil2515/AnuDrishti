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
  SignalIcon
} from '@heroicons/react/24/outline';

const Home = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans selection:bg-indigo-500 selection:text-white">
      {/* Background radial gradients */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 -left-40 h-96 w-96 rounded-full bg-indigo-600/20 blur-3xl" />
        <div className="absolute top-1/3 -right-40 h-96 w-96 rounded-full bg-purple-600/20 blur-3xl" />
        <div className="absolute -bottom-40 left-1/3 h-96 w-96 rounded-full bg-pink-600/15 blur-3xl" />
      </div>

      {/* Navigation Bar */}
      <header className="relative z-10 border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/app/pharmaguard')}>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-500 to-purple-600 text-white shadow-lg shadow-indigo-500/30">
              <ShieldCheckIcon className="h-6 w-6" />
            </div>
            <div>
              <span className="text-xl font-black tracking-tight text-white">PharmaGuard <span className="text-indigo-400">AI</span></span>
              <span className="ml-2 text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">SIH 2026</span>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button
              onClick={() => navigate('/app/pharmaguard')}
              className="group inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-indigo-600 to-purple-600 px-5 py-2.5 text-sm font-bold text-white shadow-lg shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:scale-[1.02] active:scale-[0.98]"
            >
              <span>Launch Workbench</span>
              <ArrowRightIcon className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-10 mx-auto max-w-7xl px-6 pt-16 pb-24">
        <div className="text-center max-w-3xl mx-auto space-y-6">
          <div className="inline-flex items-center gap-2 rounded-full border border-indigo-500/30 bg-indigo-500/10 px-4 py-1.5 text-xs font-semibold text-indigo-300 backdrop-blur">
            <SparklesIcon className="h-4 w-4 text-indigo-400" />
            <span>Trustworthy Drug-Safety Decision Support</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-white leading-tight">
            GNN Predictions Gated by <br />
            <span className="bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              Faithful LLM Validation
            </span>
          </h1>

          <p className="text-lg text-slate-400 leading-relaxed">
            The first AI computational toxicology platform that automatically verifies LLM molecular explanations using counterfactual perturbations and atom attributions before presenting them to scientists.
          </p>

          <div className="pt-4 flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => navigate('/app/pharmaguard')}
              className="inline-flex items-center gap-3 rounded-2xl bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600 px-8 py-4 text-base font-extrabold text-white shadow-xl shadow-indigo-500/25 transition-all hover:shadow-indigo-500/40 hover:scale-[1.03] active:scale-[0.97]"
            >
              <BeakerIcon className="h-5 w-5" />
              <span>Open PharmaGuard AI Workbench</span>
              <ArrowRightIcon className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <div className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur transition-all hover:border-indigo-500/50 hover:bg-slate-900/80">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 mb-4">
              <CpuChipIcon className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Multi-Task GNN</h3>
            <p className="mt-2 text-sm text-slate-400">
              Attention-GIN multi-task architecture predicting 16 ADMET & toxicity endpoints simultaneously with uncertainty bounds.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur transition-all hover:border-indigo-500/50 hover:bg-slate-900/80">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20 mb-4">
              <CheckBadgeIcon className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">Faithfulness Gatekeeper</h3>
            <p className="mt-2 text-sm text-slate-400">
              Explanation Faithfulness Score ($EFS \ge 0.70$) rejects hallucinated LLM claims before presenting explanations to researchers.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur transition-all hover:border-indigo-500/50 hover:bg-slate-900/80">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-pink-500/10 text-pink-400 border border-pink-500/20 mb-4">
              <SignalIcon className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">OOD & Epistemic Band</h3>
            <p className="mt-2 text-sm text-slate-400">
              Hybrid Morgan Tanimoto distance + MC-Dropout 95% Confidence Intervals flag novel molecules automatically.
            </p>
          </div>

          <div className="rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur transition-all hover:border-indigo-500/50 hover:bg-slate-900/80">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 mb-4">
              <AdjustmentsHorizontalIcon className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-white">What-If Bioisosteres</h3>
            <p className="mt-2 text-sm text-slate-400">
              Generate molecular perturbations and bioisosteric edits to lower predicted toxicity while maintaining ADMET permeability.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Home;
