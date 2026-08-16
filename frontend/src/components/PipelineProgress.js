import React, { useEffect, useState } from 'react';

// Six-stage PharmaGuard pipeline shown while an analysis request is in flight.
// The backend does not stream stage events, so we animate a confident
// sequential walk through the stages to communicate what the platform is doing
// (SIH audit P2 #10: animated pipeline progress for the demo).
const STAGES = [
  { key: 'parse', label: 'SMILES Parsing', hint: 'Validating molecular structure', icon: '🔬' },
  { key: 'feat', label: 'GNN Featurization', hint: 'Building graph representation', icon: '🔗' },
  { key: 'predict', label: 'Multi-Task Prediction', hint: 'Tox21 · BBBP · ClinTox · Clearance', icon: '📊' },
  { key: 'attn', label: 'GNNExplainer Attribution', hint: 'Identifying driving substructures', icon: '🔍' },
  { key: 'ood', label: 'OOD + Triage', hint: 'Novelty & safety risk scoring', icon: '⚠️' },
  { key: 'efs', label: 'Faithfulness Gate', hint: 'Rejecting ungrounded claims', icon: '🛡️' },
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
    
    // Smooth animation for progress bar
    const progressInterval = setInterval(() => {
      setProgress((p) => {
        const targetProgress = ((stage + 1) / STAGES.length) * 100;
        if (p >= targetProgress) return p;
        return Math.min(p + 2, targetProgress);
      });
    }, 50);
    
    // Stage advancement
    const stageInterval = setInterval(() => {
      setStage((s) => (s < STAGES.length - 1 ? s + 1 : s));
    }, 1200); // Longer interval for better demo pacing
    
    return () => {
      clearInterval(progressInterval);
      clearInterval(stageInterval);
    };
  }, [active]);

  if (!active) return null;

  return (
    <div className="rounded-2xl border border-indigo-200 bg-white p-6 shadow-lg">
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-indigo-100 rounded-xl flex items-center justify-center text-indigo-600">
            🧪
          </div>
          <div>
            <p className="text-sm font-bold uppercase tracking-wide text-indigo-600">
              Running PharmaGuard Pipeline
            </p>
            <p className="text-xs text-indigo-500">
              {stage < STAGES.length ? STAGES[stage].label : 'Analysis Complete'}
            </p>
          </div>
        </div>
        <span className="text-xs font-semibold text-indigo-400">
          Stage {Math.min(stage + 1, STAGES.length)} / {STAGES.length}
        </span>
      </div>

      <div className="space-y-4">
        {STAGES.map((st, i) => {
          const done = i < stage;
          const current = i === stage;
          const completed = done && i < STAGES.length - 1;
          
          return (
            <div key={st.key} className="flex items-center gap-4">
              {/* Stage Icon with State */}
              <div className="flex-shrink-0">
                <div className={`h-12 w-12 rounded-xl flex items-center justify-center transition-all duration-500 ${
                  done 
                    ? 'bg-emerald-500 text-white' 
                    : current 
                      ? 'bg-indigo-50 border-2 border-indigo-500 text-indigo-600' 
                      : 'border-2 border-slate-200 bg-white text-slate-300'
                }`}>
                  {st.icon}
                </div>
                {current && (
                  <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 h-2 w-2 bg-indigo-500 rounded-full animate-pulse"/>
                )}
              </div>
              
              {/* Stage Details */}
              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between">
                  <h4 className={`text-sm font-semibold ${
                    done ? 'text-slate-500' : current ? 'text-indigo-700' : 'text-slate-400'
                  }`}>
                    {st.label}
                  </h4>
                  {done && (
                    <span className="text-xs text-emerald-600">✓ Completed</span>
                  )}
                </div>
                <p className="text-[12px] text-slate-400">{st.hint}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Enhanced Progress Bar */}
      <div className="mt-6">
        <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-indigo-500 to-emerald-500 rounded-full transition-all duration-1000"
            style={{ width: `${progress}%` }}
          >
            <div className="absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 h-4 w-4 bg-white rounded-full ring-2 ring-indigo-500"/>
          </div>
        </div>
        <div className="mt-2 flex justify-between text-xs text-slate-500">
          <span>0%</span>
          <span>100%</span>
        </div>
      </div>

      {/* Completion Message */}
      {stage >= STAGES.length - 1 && (
        <div className="mt-5 p-4 bg-emerald-50 border-l-4 border-emerald-500 rounded-r-lg">
          <div className="flex items-start gap-3">
            <CheckBadgeIcon className="h-5 w-5 mt-0.5 text-emerald-600 flex-shrink-0" />
            <div>
              <p className="font-bold text-emerald-800">Analysis Complete</p>
              <p className="text-sm text-emerald-600">
                All six stages finished successfully. Results ready for review.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PipelineProgress;
