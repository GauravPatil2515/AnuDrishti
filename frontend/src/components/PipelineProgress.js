import React, { useEffect, useState } from 'react';

// Six-stage PharmaGuard pipeline shown while an analysis request is in flight.
// The backend does not stream stage events, so we animate a confident
// sequential walk through the stages to communicate what the platform is doing
// (SIH audit P2 #10: animated pipeline progress for the demo).
const STAGES = [
  { key: 'parse', label: 'SMILES Parsing', hint: 'Validating molecular structure' },
  { key: 'feat', label: 'GNN Featurization', hint: 'Building graph representation' },
  { key: 'predict', label: 'Multi-Task Prediction', hint: 'Tox21 · BBBP · ClinTox · Clearance' },
  { key: 'attn', label: 'Attention / Attribution', hint: 'Identifying driving substructures' },
  { key: 'ood', label: 'OOD + Triage', hint: 'Novelty & safety risk scoring' },
  { key: 'efs', label: 'Faithfulness Gate', hint: 'Rejecting ungrounded claims' },
];

const PipelineProgress = ({ active }) => {
  const [stage, setStage] = useState(0);

  useEffect(() => {
    if (!active) {
      setStage(0);
      return undefined;
    }
    setStage(0);
    const id = setInterval(() => {
      setStage((s) => (s < STAGES.length - 1 ? s + 1 : s));
    }, 650);
    return () => clearInterval(id);
  }, [active]);

  if (!active) return null;

  return (
    <div className="rounded-2xl border border-indigo-200 bg-white p-5 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <p className="text-sm font-bold uppercase tracking-wide text-indigo-600">
          Running PharmaGuard Pipeline
        </p>
        <span className="text-xs font-semibold text-indigo-400">
          Stage {stage + 1} / {STAGES.length}
        </span>
      </div>

      <div className="space-y-2.5">
        {STAGES.map((st, i) => {
          const done = i < stage;
          const current = i === stage;
          return (
            <div key={st.key} className="flex items-center gap-3">
              <span
                className={[
                  'flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold transition',
                  done
                    ? 'bg-emerald-500 text-white'
                    : current
                      ? 'border-2 border-indigo-500 bg-indigo-50 text-indigo-600'
                      : 'border-2 border-slate-200 bg-white text-slate-300',
                ].join(' ')}
              >
                {done ? '✓' : current ? (
                  <span className="h-3 w-3 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent" />
                ) : (
                  i + 1
                )}
              </span>
              <div className="flex-1">
                <p
                  className={[
                    'text-sm font-semibold',
                    done ? 'text-slate-500' : current ? 'text-indigo-700' : 'text-slate-400',
                  ].join(' ')}
                >
                  {st.label}
                </p>
                <p className="text-[11px] text-slate-400">{st.hint}</p>
              </div>
              {current && (
                <span className="animate-pulse text-[11px] font-semibold text-indigo-400">
                  running…
                </span>
              )}
            </div>
          );
        })}
      </div>

      <div className="mt-4 h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-indigo-500 transition-all duration-500"
          style={{ width: `${((stage + 1) / STAGES.length) * 100}%` }}
        />
      </div>
    </div>
  );
};

export default PipelineProgress;
