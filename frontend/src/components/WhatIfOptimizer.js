import React from 'react';
import { clsx } from 'clsx';
import { SparklesIcon, ArrowDownIcon, ArrowUpIcon, BeakerIcon, ScaleIcon } from '@heroicons/react/24/outline';

/**
 * WhatIfOptimizer — Mode C. Shows the original toxic molecule and ranked
 * structural modifications (counterfactuals) with predicted toxicity change.
 */
const WhatIfOptimizer = ({ whatif }) => {
  if (!whatif || whatif.candidates?.length === 0) {
    return (
      <div className="rounded-lg border border-border-dashed border-border bg-surface p-8 text-center text-muted">
        Enter a molecule in <b>Mode C</b> to generate toxicity-lowering modifications.
      </div>
    );
  }

  const originalSmiles = whatif.original_smiles;
  const candidates = whatif.candidates || [];

  const originalTox = candidates.length
    ? (whatif.baseline_toxicity ?? Math.max(...candidates.map((c) => c.toxicity_probability + 0.0001)))
    : 0;

  return (
    <div className="space-y-3">
      {/* Original molecule */}
      <div className="surface-elevated rounded-lg border border-border p-3">
        <div className="flex items-center gap-1.5 mb-1.5">
          <BeakerIcon className="h-3 w-3 text-indigo-400" />
          <p className="text-xs font-semibold uppercase text-muted">Original Molecule</p>
        </div>
        <p className="break-all font-mono text-xs text-secondary">{originalSmiles}</p>
        {originalTox > 0 && (
          <p className="mt-1 text-xs">
            <span className="text-muted">Baseline toxicity:</span>
            <span className="font-mono font-bold text-red-400 ml-1">
              {(originalTox * 100).toFixed(1)}%
            </span>
          </p>
        )}
      </div>

      <h3 className="text-xs font-bold uppercase tracking-wider text-muted">
        Suggested Modifications ({candidates.length})
      </h3>

      <div className="space-y-2">
        {candidates.map((c, i) => {
          const delta = (c.toxicity_probability ?? 0) - originalTox;
          const lowered = delta < 0;
          const deltaAbs = Math.abs(delta);
          return (
            <div key={i} className="surface-elevated rounded-lg border border-border p-3">
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div>
                  <p className="text-xs font-bold text-primary">
                    {c.modification_description}
                  </p>
                  <p className="mt-0.5 break-all font-mono text-[10px] text-muted">
                    {c.modified_smiles}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right">
                    <p className="text-[10px] text-muted">Toxicity</p>
                    <p className="font-black text-sm">
                      {((c.toxicity_probability ?? 0) * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div
                    className={clsx(
                      'flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold',
                      lowered
                        ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                        : 'bg-red-500/10 text-red-400 border border-red-500/30'
                    )}
                  >
                    {lowered ? (
                      <ArrowDownIcon className="h-3 w-3" />
                    ) : (
                      <ArrowUpIcon className="h-3 w-3" />
                    )}
                    {delta >= 0 ? '+' : ''}
                    {deltaAbs.toFixed(1)}%
                  </div>
                </div>
              </div>

              <div className="flex flex-wrap items-center gap-2 text-[10px] text-muted">
                <span>Effect: {c.expected_toxicity_change}</span>
                <span className={clsx('px-1.5 py-0.25 rounded text-xs font-mono',
                  (c.confidence * 100) >= 70 ? 'text-emerald-400' :
                  (c.confidence * 100) >= 40 ? 'text-amber-400' : 'text-red-400'
                )}>
                  conf. {(c.confidence * 100).toFixed(0)}%
                </span>
                {c.qed != null && (
                  <span className="flex items-center gap-1">
                    <ScaleIcon className="h-3 w-3" />
                    <span
                      className={clsx(
                        'rounded-full px-1.5 py-0.25 font-semibold text-xs',
                        c.qed >= 0.4
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : 'bg-border text-muted border border-border'
                      )}
                      title="Quantitative Estimate of Drug-likeness (RDKit QED)"
                    >
                      QED {c.qed.toFixed(2)}
                      {c.qed >= 0.4 && <span className="ml-0.5">· drug-like</span>}
                    </span>
                  </span>
                )}
                {c.sa_score != null && (
                  <span className="flex items-center gap-1">
                    <ScaleIcon className="h-3 w-3" />
                    <span
                      className={clsx(
                        'rounded-full px-1.5 py-0.25 font-semibold text-xs',
                        c.sa_score < 6.0
                          ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30'
                          : 'bg-border text-muted border border-border'
                      )}
                      title="Synthetic Accessibility Score (lower = easier to synthesize)"
                    >
                      SA {c.sa_score.toFixed(2)}
                      {c.sa_score < 6.0 && <span className="ml-0.5">· synthesizable</span>}
                    </span>
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <p className="flex items-center gap-1.5 text-[10px] text-muted italic">
        <SparklesIcon className="h-3 w-3" />
        Candidates are generated by chemically valid perturbations and re-scored through
        the multi-task GNN ensemble. Reduced-toxicity modifications are prioritized while
        ADMET properties are preserved where possible.
      </p>
    </div>
  );
};

export default WhatIfOptimizer;