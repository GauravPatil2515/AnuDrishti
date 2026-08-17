import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../App';
import {
  ShieldCheckIcon,
  BeakerIcon,
  SparklesIcon,
  CpuChipIcon,
  CheckBadgeIcon,
  ArrowRightIcon,
  AdjustmentsHorizontalIcon,
  SignalIcon,
  PlayIcon,
  SunIcon,
  MoonIcon
} from '@heroicons/react/24/outline';

const Home = () => {
  const navigate = useNavigate();
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="min-h-screen bg-canvas text-primary font-sans selection:bg-accent-green-glow selection:text-primary">
      {/* Background - Dot grid with subtle radial glow */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden bg-canvas">
        <div 
          className="absolute inset-0 opacity-[0.03] dark:opacity-[0.05]" 
          style={{ backgroundImage: 'radial-gradient(var(--color-text-primary) 1px, transparent 1px)', backgroundSize: '32px 32px' }} 
        />
        <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] rounded-full bg-accent-green opacity-[0.04] dark:opacity-[0.08] blur-[100px]" />
        <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-accent-emerald opacity-[0.03] dark:opacity-[0.06] blur-[100px]" />
      </div>

      {/* Navigation Bar */}
      <header className="relative z-20 border-b border-border bg-canvas-overlay backdrop-blur-md">
        <div className="mx-auto flex max-w-screen-xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/app/pharmaguard')}>
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-accent-green/10 text-accent-green border border-accent-green/20">
              <ShieldCheckIcon className="h-6 w-6" />
            </div>
            <div>
              <span className="text-xl font-bold tracking-tight text-primary font-display">
                PharmaGuard <span className="text-accent-green">AI</span>
              </span>
              <span className="ml-2 text-[10px] uppercase font-bold tracking-widest px-2 py-0.5 rounded-full bg-accent-green/10 text-accent-green border border-accent-green/20">
                SIH 2026
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2 sm:gap-4">
            <button
              onClick={toggleTheme}
              className="p-2 rounded-md text-text-muted hover:text-text-primary hover:bg-surface transition-colors"
              title="Toggle theme"
            >
              {theme === 'dark' ? <SunIcon className="h-5 w-5" /> : <MoonIcon className="h-5 w-5" />}
            </button>
            <button
              onClick={() => navigate('/app/pharmaguard')}
              className="group inline-flex items-center gap-2 rounded-md bg-transparent px-3 py-1.5 text-sm font-semibold text-text-secondary hover:text-text-primary hover:bg-surface transition-colors"
            >
              <span className="hidden sm:inline">Launch Workbench</span>
              <span className="sm:hidden">Launch</span>
              <ArrowRightIcon className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="relative z-20 mx-auto max-w-screen-xl px-6 pt-16 pb-24">
        <div className="text-center max-w-4xl mx-auto space-y-8">
          
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-4 py-1.5 text-xs font-semibold text-text-secondary backdrop-blur shadow-sm">
            <SparklesIcon className="h-4 w-4 text-accent-green" />
            <span>Trustworthy Drug-Safety Decision Support</span>
          </div>

          <h1 className="text-4xl md:text-6xl font-bold tracking-tight text-text-primary leading-tight font-display">
            GNN Predictions Gated by <br className="hidden md:block" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-accent-green to-accent-emerald">
              Faithful LLM Validation
            </span>
          </h1>

          <p className="text-lg md:text-xl text-text-secondary leading-relaxed max-w-3xl mx-auto">
            The first AI computational toxicology platform that automatically verifies LLM molecular explanations using counterfactual perturbations and atom attributions before presenting them to scientists.
          </p>

          <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={() => navigate('/app/pharmaguard')}
              className="btn btn-primary px-8 py-3.5 text-base w-full sm:w-auto shadow-glow-green"
            >
              <BeakerIcon className="h-5 w-5" />
              <span>Open PharmaGuard Workbench</span>
              <ArrowRightIcon className="h-5 w-5" />
            </button>
            <button
              onClick={() => navigate('/app/pharmaguard', { state: { openDemo: true } })}
              className="btn btn-secondary px-8 py-3.5 text-base w-full sm:w-auto"
            >
              <PlayIcon className="h-5 w-5" />
              <span>Try Demo (2 molecules)</span>
            </button>
          </div>
        </div>

        {/* Performance Strip */}
        <div className="mt-16 border-y border-border bg-surface-elevated/50 py-6">
          <div className="mx-auto max-w-4xl flex flex-wrap justify-center gap-8 md:gap-16 text-center">
            <div>
              <p className="text-3xl font-black text-text-primary font-mono">0.849</p>
              <p className="text-xs font-bold uppercase tracking-wider text-text-muted mt-1">BBBP AUROC</p>
            </div>
            <div>
              <p className="text-3xl font-black text-text-primary font-mono">0.849</p>
              <p className="text-xs font-bold uppercase tracking-wider text-text-muted mt-1">BACE AUROC</p>
            </div>
            <div>
              <p className="text-3xl font-black text-text-primary font-mono">0.779</p>
              <p className="text-xs font-bold uppercase tracking-wider text-text-muted mt-1">TOX21 AUROC</p>
            </div>
            <div>
              <p className="text-3xl font-black text-accent-emerald font-mono">≥0.70</p>
              <p className="text-xs font-bold uppercase tracking-wider text-text-muted mt-1">EFS Threshold</p>
            </div>
          </div>
        </div>

        {/* Feature Highlights Grid */}
        <div className="mt-20 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="surface p-6 transition-all hover:-translate-y-1 hover:shadow-card-hover group">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent-green/10 text-accent-green border border-accent-green/20 mb-4 group-hover:scale-110 transition-transform">
              <CpuChipIcon className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-text-primary font-display">Multi-Task GNN</h3>
            <p className="mt-2 text-sm text-text-secondary leading-relaxed">
              Attention-GIN architecture predicting 16 ADMET & toxicity endpoints simultaneously with uncertainty bounds.
            </p>
          </div>

          <div className="surface p-6 transition-all hover:-translate-y-1 hover:shadow-card-hover group">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent-emerald/10 text-accent-emerald border border-accent-emerald/20 mb-4 group-hover:scale-110 transition-transform">
              <CheckBadgeIcon className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-text-primary font-display">Faithfulness Gatekeeper</h3>
            <p className="mt-2 text-sm text-text-secondary leading-relaxed">
              Explanation Faithfulness Score (EFS ≥ 0.70) rejects hallucinated LLM claims before presenting to researchers.
            </p>
          </div>

          <div className="surface p-6 transition-all hover:-translate-y-1 hover:shadow-card-hover group">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent-rose/10 text-accent-rose border border-accent-rose/20 mb-4 group-hover:scale-110 transition-transform">
              <SignalIcon className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-text-primary font-display">OOD & Epistemic Band</h3>
            <p className="mt-2 text-sm text-text-secondary leading-relaxed">
              Hybrid Morgan Tanimoto distance + MC-Dropout 95% Confidence Intervals flag novel molecules automatically.
            </p>
          </div>

          <div className="surface p-6 transition-all hover:-translate-y-1 hover:shadow-card-hover group">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-accent-amber/10 text-accent-amber border border-accent-amber/20 mb-4 group-hover:scale-110 transition-transform">
              <AdjustmentsHorizontalIcon className="h-6 w-6" />
            </div>
            <h3 className="text-lg font-bold text-text-primary font-display">What-If Bioisosteres</h3>
            <p className="mt-2 text-sm text-text-secondary leading-relaxed">
              Generate molecular perturbations and bioisosteric edits to lower predicted toxicity while maintaining viability.
            </p>
          </div>
        </div>

        {/* Technical Details / Flow */}
        <div className="mt-24 pt-16 border-t border-border">
          <div className="text-center max-w-2xl mx-auto mb-12">
            <h2 className="text-2xl md:text-3xl font-bold text-text-primary font-display">How It Works</h2>
            <p className="mt-4 text-text-secondary text-base">A robust 4-step pipeline that ensures both predictive accuracy and explanatory faithfulness.</p>
          </div>
          
          <div className="grid gap-6 md:grid-cols-4">
            <div className="relative surface-elevated p-6 text-center">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-surface border border-border flex items-center justify-center font-bold text-text-primary font-mono text-sm shadow-sm">1</div>
              <h3 className="text-base font-bold text-text-primary mt-4">Molecular Input</h3>
              <p className="text-sm text-text-secondary mt-2">Enter SMILES or natural language to describe your compound.</p>
            </div>
            <div className="relative surface-elevated p-6 text-center">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-surface border border-border flex items-center justify-center font-bold text-text-primary font-mono text-sm shadow-sm">2</div>
              <h3 className="text-base font-bold text-text-primary mt-4">GNN Prediction</h3>
              <p className="text-sm text-text-secondary mt-2">Simultaneously predicts toxicity & ADMET with uncertainty bands.</p>
            </div>
            <div className="relative surface-elevated p-6 text-center">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-surface border border-border flex items-center justify-center font-bold text-text-primary font-mono text-sm shadow-sm">3</div>
              <h3 className="text-base font-bold text-text-primary mt-4">LLM Generation</h3>
              <p className="text-sm text-text-secondary mt-2">Generates mechanistic explanations linking substructures to outcomes.</p>
            </div>
            <div className="relative surface-elevated p-6 text-center">
              <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-8 rounded-full bg-surface border border-border flex items-center justify-center font-bold text-text-primary font-mono text-sm shadow-sm">4</div>
              <h3 className="text-base font-bold text-text-primary mt-4">EFS Verification</h3>
              <p className="text-sm text-text-secondary mt-2">Rigorously tests claims via counterfactual perturbation before display.</p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Home;