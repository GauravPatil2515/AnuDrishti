import React from 'react';
import { clsx } from 'clsx';
import {
  ShieldCheckIcon, ShieldExclamationIcon, ExclamationTriangleIcon,
  SignalIcon, BeakerIcon,
} from '@heroicons/react/24/outline';

const TRIAGE_STYLES = {
  GREEN: { banner: 'bg-emerald-50 border-emerald-200', text: 'text-emerald-700', chip: 'bg-emerald-100 text-emerald-700', Icon: ShieldCheckIcon, label: 'LOW CONCERN' },
  YELLOW: { banner: 'bg-amber-50 border-amber-200', text: 'text-amber-700', chip: 'bg-amber-100 text-amber-700', Icon: ExclamationTriangleIcon, label: 'REVIEW NEEDED' },
  RED: { banner: 'bg-red-50 border-red-200', text: 'text-red-700', chip: 'bg-red-100 text-red-700', Icon: ShieldExclamationIcon, label: 'HIGH CONCERN' },
};

// Map model prediction dicts into a flat endpoint list
const extractEndpoints = (analysis) => {
  const preds = analysis?.predictions?.predictions || {};
  return Object.entries(preds).map(([id, v]) => ({
    id,
    prob: typeof v?.probability === 'number' ? v.probability : 0,
    label: v?.prediction || (v?.probability > 0.5 ? 'Toxic' : 'Non-toxic'),
  }));
};

const RiskMeter = ({ label, prob, color }) => (
  <div className="rounded-xl border border-slate-100 bg-white p-3">
    <div className="flex items-center justify-between text-sm">
      <span className="font-semibold text-slate-700">{label}</span>
      <span className="font-mono text-slate-500">{(prob * 100).toFixed(0)}%</span>
    </div>
    <div className="mt-2 h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
      <div className={clsx('h-full rounded-full', color)} style={{ width: `${Math.min(100, prob * 100)}%` }} />
    </div>
  </div>
);

const SafetyDashboard = ({ analysis }) => {
  if (!analysis) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-400">
        Run an analysis to see the safety &amp; ADMET dashboard.
      </div>
    );
  }

  const triage = analysis.triage || { category: 'GREEN', risk_score: 0, recommendation: '' };
  const style = TRIAGE_STYLES[triage.category] || TRIAGE_STYLES.GREEN;
  const ood = analysis.ood || {};
  const endpoints = extractEndpoints(analysis);
  const toxProb = analysis.toxicity_probability || 0;

  return (
    <div className="space-y-6">
      {/* Triage banner */}
      <div className={clsx('flex items-center justify-between rounded-2xl border p-5', style.banner)}>
        <div className="flex items-center gap-4">
          <style.Icon className={clsx('h-10 w-10', style.text)} />
          <div>
            <p className={clsx('text-xs font-bold uppercase tracking-widest', style.text)}>Overall Safety Assessment</p>
            <p className={clsx('text-2xl font-extrabold', style.text)}>{triage.category}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-slate-500">Safety Risk Score</p>
          <p className={clsx('text-3xl font-black', style.text)}>{(triage.risk_score * 100).toFixed(0)}</p>
          <p className={clsx('mt-1 rounded-full px-3 py-1 text-xs font-bold', style.chip)}>
            {triage.recommendation}
          </p>
        </div>
      </div>

      {/* Risk component breakdown */}
      {triage.components && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {Object.entries(triage.components).map(([k, v]) => (
            <div key={k} className="rounded-xl border border-slate-100 bg-white p-3 text-center">
              <p className="text-[11px] font-semibold uppercase text-slate-400">{k.replace('_', ' ')}</p>
              <p className="text-lg font-bold text-slate-700">{(v * 100).toFixed(0)}</p>
            </div>
          ))}
        </div>
      )}

      {/* Primary toxicity + OOD / confidence badges */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
            <BeakerIcon className="h-5 w-5 text-indigo-500" /> Predicted Toxicity
          </div>
          <p className="mt-1 text-3xl font-black text-indigo-600">{(toxProb * 100).toFixed(0)}%</p>
        </div>

        <div className={clsx('rounded-2xl border bg-white p-4 shadow-sm', ood.is_ood ? 'border-red-200' : 'border-emerald-200')}>
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
            <SignalIcon className="h-5 w-5" /> OOD / Novelty
          </div>
          <p className={clsx('mt-1 text-3xl font-black', ood.is_ood ? 'text-red-600' : 'text-emerald-600')}>
            {ood.is_ood ? 'FLAGGED' : 'IN-DIST'}
          </p>
          {ood.nearest_neighbor_similarity != null && (
            <p className="text-xs text-slate-400">NN similarity {(ood.nearest_neighbor_similarity * 100).toFixed(0)}%</p>
          )}
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
            <ShieldCheckIcon className="h-5 w-5 text-indigo-500" /> Model Confidence
          </div>
          <p className="mt-1 text-3xl font-black text-indigo-600">
            {ood.confidence_modifier != null ? `${(ood.confidence_modifier * 100).toFixed(0)}%` : '—'}
          </p>
          {ood.is_ood && <p className="text-xs text-red-400">Confidence reduced (OOD)</p>}
        </div>
      </div>

      {/* Endpoint grid */}
      <div>
        <h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">
          Multi-Task Endpoints
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {endpoints.map((e) => (
            <RiskMeter
              key={e.id}
              label={e.id}
              prob={e.prob}
              color={e.prob > 0.7 ? 'bg-red-500' : e.prob > 0.4 ? 'bg-amber-400' : 'bg-emerald-500'}
            />
          ))}
          {endpoints.length === 0 && (
            <p className="text-sm text-slate-400">No endpoint predictions available.</p>
          )}
        </div>
      </div>

      <p className="text-xs italic text-slate-400">
        {triage.disclaimer || 'Computational decision-support screening only.'}
      </p>
    </div>
  );
};

export default SafetyDashboard;
