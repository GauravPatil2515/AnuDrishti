import React, { useEffect, useState } from 'react';
import { clsx } from 'clsx';

// Six-stage PharmaGuard pipeline shown while an analysis request is in flight.
const STAGES = [
  { key: 'parse', label: 'SMILES Parsing', hint: 'Validating molecular structure' },
  { key: 'feat', label: 'GNN Featurization', hint: 'Building graph representation' },
  { key: 'predict', label: 'Multi-Task Prediction', hint: 'Tox21 · BBBP · ClinTox · Clearance' },
  { key: 'attn', label: 'GNNExplainer Attribution', hint: 'Identifying driving substructures' },
  { key: 'ood', label: 'OOD + Triage', hint: 'Novelty & safety risk scoring' },
  { key: 'efs', label: 'Faithfulness Gate', hint: 'Rejecting ungrounded claims' },
];

const PipelineProgress = ({ active }) => {
  const [stage, setStage] = useState(0);
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!active) {
      setStage(0);
      setProgress(0);
      return undefined;
    }

    setStage(0);
    setProgress(0);

    const progressInterval = setInterval(() => {
      setProgress((p) => {
        const targetProgress = ((stage + 1) / STAGES.length) * 100;
        if (p >= targetProgress) return p;
        return Math.min(p + 2, targetProgress);
      });
    }, 50);

    const stageInterval = setInterval(() => {
      setStage((s) => (s < STAGES.length - 1 ? s + 1 : s));
    }, 1000);

    return () => {
      clearInterval(progressInterval);
      clearInterval(stageInterval);
    };
  }, [active, stage]);

  if (!active) return null;

  return (
    <div className="surface-elevated rounded-lg border border-border p-4">
      <div className="mb-3 flex items-center justify-between">
<div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              🧪
            </div>
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-white/60">
                Running PharmaGuard Pipeline
              </p>
              <p className="text-[10px] text-white/40">
                {stage < STAGES.length ? STAGES[stage].label : 'Analysis Complete'}
              </p>
            </div>
          </div>
          <span className="text-xs font-semibold text-indigo-400">
            Stage {Math.min(stage + 1, STAGES.length)} / {STAGES.length}
          </span>
      </div>

      <div className="space-y-2.5">
        {STAGES.map((st, i) => {
          const done = i < stage;
          const current = i === stage;

          return (
            <div key={st.key} className="flex items-center gap-3">
              <div className="flex-shrink-0">
<div className={clsx(
                  'h-6 w-6 rounded-md flex items-center justify-center text-xs transition-all',
                  done
                    ? 'bg-emerald-400 text-white'
                    : current
                      ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/50'
                      : 'bg-border text-white/40'
              )}>
                {done ? '✓' : i + 1}
              </div>
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between">
                  <h4 className={clsx(
                    'text-xs font-medium',
                    done ? 'text-white/40' : current ? 'text-indigo-400' : 'text-white/40'
                  )}>
                    {st.label}
                  </h4>
                  {done && (
                    <span className="text-[10px] text-emerald-400">Completed</span>
                  )}
                </div>
                <p className="text-[10px] text-muted">{st.hint}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="mt-3">
<div className="progress-bar">
            <div
              className="progress-fill bg-indigo-400 h-1.5 rounded-full transition-all duration-1000"
              style={{ width: `${progress}%` }}
            />
          </div>
      </div>
    </div>
  );
};

export default PipelineProgress;