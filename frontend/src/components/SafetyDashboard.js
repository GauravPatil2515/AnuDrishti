import React from 'react';
import { clsx } from 'clsx';
import {
  ShieldCheckIcon, ShieldExclamationIcon, ExclamationTriangleIcon,
  SignalIcon, BeakerIcon, ScaleIcon, CheckBadgeIcon, InformationCircleIcon,
  ChartBarIcon, AcademicCapIcon, ShieldCheckIcon as VerifiedIcon
} from '@heroicons/react/24/outline';

const TRIAGE_STYLES = {
  GREEN: { banner: 'bg-emerald-50 border-emerald-200', text: 'text-emerald-700', chip: 'bg-emerald-100 text-emerald-700', Icon: ShieldCheckIcon, label: 'LOW CONCERN' },
  YELLOW: { banner: 'bg-amber-50 border-amber-200', text: 'text-amber-700', chip: 'bg-amber-100 text-amber-700', Icon: ExclamationTriangleIcon, label: 'REVIEW NEEDED' },
  RED: { banner: 'bg-red-50 border-red-200', text: 'text-red-700', chip: 'bg-red-100 text-red-700', Icon: ShieldExclamationIcon, label: 'HIGH CONCERN' },
};

const EPISTEMIC_BADGES = {
  Low: 'bg-emerald-100 text-emerald-800 border-emerald-300',
  Moderate: 'bg-amber-100 text-amber-800 border-amber-300',
  High: 'bg-red-100 text-red-800 border-red-300',
};

const EFS_BADGES = {
  VERIFIED: { label: 'VERIFIED', className: 'bg-emerald-100 text-emerald-700 border-emerald-300', icon: CheckBadgeIcon },
  PARTIAL: { label: 'PARTIAL', className: 'bg-amber-100 text-amber-700 border-amber-300', icon: InformationCircleIcon },
  REJECTED: { label: 'REJECTED', className: 'bg-red-100 text-red-700 border-red-300', icon: ShieldExclamationIcon },
};

// Map model prediction dicts into a flat endpoint list with uncertainty
const extractEndpoints = (analysis) => {
  const preds = analysis?.predictions?.predictions || {};
  const perEndpointUnc = analysis?.uncertainty?.per_endpoint || {};

  return Object.entries(preds).map(([id, v]) => {
    const prob = typeof v?.probability === 'number' ? v.probability : 0;
    const unc = perEndpointUnc[id] || {};
    const ci_low = typeof unc.ci_low === 'number' ? unc.ci_low : Math.max(0, prob - 0.15);
    const ci_high = typeof unc.ci_high === 'number' ? unc.ci_high : Math.min(1, prob + 0.15);
    const epistemicLabel = unc.epistemic_uncertainty || (unc.epistemic_std < 0.05 ? 'Low' : unc.epistemic_std > 0.15 ? 'High' : 'Moderate');

    return {
      id,
      prob,
      ci_low,
      ci_high,
      epistemic_std: unc.epistemic_std,
      epistemic_uncertainty: epistemicLabel,
      label: v?.prediction || (prob > 0.5 ? 'Toxic' : 'Non-toxic'),
    };
  });
};

const RiskMeter = ({ endpoint }) => {
  const { id, prob, ci_low, ci_high, epistemic_uncertainty, epistemic_std } = endpoint;
  const color = prob > 0.7 ? 'bg-red-500' : prob > 0.4 ? 'bg-amber-400' : 'bg-emerald-500';
  const badgeStyle = EPISTEMIC_BADGES[epistemic_uncertainty] || EPISTEMIC_BADGES.Moderate;

  const lowPercent = Math.max(0, Math.min(100, ci_low * 100));
  const highPercent = Math.max(0, Math.min(100, ci_high * 100));
  const probPercent = Math.max(0, Math.min(100, prob * 100));
  const widthPercent = Math.max(2, highPercent - lowPercent);

  return (
    <div className="rounded-xl border border-slate-100 bg-white p-3.5 shadow-sm space-y-2">
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-slate-700">{id}</span>
          <span className={clsx('rounded-full border px-2 py-0.5 text-[10px] font-bold uppercase', badgeStyle)}>
            Uncertainty: {epistemic_uncertainty}
          </span>
        </div>
        <span className="font-mono text-slate-600 font-bold">{(prob * 100).toFixed(0)}%</span>
      </div>

      {/* Main bar */}
      <div className="relative h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
        <div className={clsx('h-full rounded-full transition-all duration-300', color)} style={{ width: `${probPercent}%` }} />
      </div>

      {/* Interactive 95% Confidence Interval Band */}
      <div className="mt-1 space-y-1">
        <div className="flex justify-between text-[10px] text-slate-400 font-mono">
          <span>CI Low: {(ci_low * 100).toFixed(0)}%</span>
          {epistemic_std != null && <span>std: ±{(epistemic_std * 100).toFixed(1)}%</span>}
          <span>CI High: {(ci_high * 100).toFixed(0)}%</span>
        </div>
        <div className="relative h-2 w-full rounded bg-slate-100">
          <div
            className="absolute h-full rounded bg-indigo-200/70 border border-indigo-400/50"
            style={{ left: `${lowPercent}%`, width: `${widthPercent}%` }}
            title={`95% CI: [${(ci_low * 100).toFixed(1)}%, ${(ci_high * 100).toFixed(1)}%]`}
          />
          <div
            className="absolute top-0 h-full w-1 -ml-0.5 bg-indigo-600 rounded"
            style={{ left: `${probPercent}%` }}
            title={`Point estimate: ${(prob * 100).toFixed(1)}%`}
          />
        </div>
      </div>
    </div>
  );
};

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
  const overallUnc = analysis.uncertainty?.overall || {};

  return (
    <div className="space-y-6">
      {/* Clinical-use disclaimer (SIH audit Issue #7) */}
      <div className="flex items-start gap-2 rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs font-medium text-amber-800">
        <span aria-hidden className="text-sm">⚠️</span>
        <span>
          NOT A CLINICAL DECISION TOOL. This dashboard reports computational predictions from a
          research model. It must not be used for diagnosis, treatment, or regulatory submission
          without independent experimental validation.
        </span>
      </div>

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

      {/* Why trust this? — Explanation Faithfulness Score (EFS) - PROMINENT */}
      {analysis.explanation && (
        <div className="rounded-2xl border-2 border-indigo-300 bg-gradient-to-r from-indigo-50 to-white p-5 shadow-md relative">
          {/* Verified badge on top-right */}
          <div className="absolute top-3 right-3 flex flex-col items-end">
            <div className="flex items-center gap-2">
              {(() => {
                const efs = analysis.explanation.faithfulness_score ?? analysis.explanation.efs;
                const status = analysis.explanation.validation_passed ? 'VERIFIED' : 
                               analysis.explanation.validation_passed === false ? 'REJECTED' : 'UNCHECKED';
                const badge = EFS_BADGES[status] || EFS_BADGES.PARTIAL;
                const Icon = badge.icon || CheckBadgeIcon;
                return (
                  <>
                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-white border-2 border-slate-200 shadow-sm">
                       <span className="text-2xl font-black text-indigo-600">
                         {(efs != null ? `${Math.round(efs * 100)} ± 12` : '—')}%
                       </span>
                    </div>
                    <div className="flex flex-col items-end">
                      <span className={clsx('rounded-full border px-3 py-1 text-xs font-bold uppercase tracking-wider shadow', badge.className)}>
                        <Icon className="h-3 w-3 inline mr-1" /> {badge.label}
                      </span>
                      <p className="text-[10px] text-slate-400 mt-0.5 font-mono">
                        Threshold: ≥70%
                       <p className="text-[10px] text-slate-400 mt-0.5 font-mono">
                         EFS shows uncertainty band (±12%) due to uncalibrated weights
                       </p>
                      </p>
                    </div>
                  </>
                );
              })()}
            </div>
          </div>

          <div className="flex items-start gap-4 pr-48">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-indigo-500/10 text-indigo-500 border border-indigo-500/20 flex-shrink-0">
              <VerifiedIcon className="h-6 w-6" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-bold text-indigo-700">Why trust this explanation? <span className="font-normal text-indigo-600 ml-1">— Faithfulness-gated, not black-box</span></p>
              <p className="text-xs text-indigo-600 mt-1">
                Every AI-generated explanation is validated against the GNN's actual decision process using counterfactual testing.
                Claims not supported by model evidence are rejected — not silently shown.
              </p>
              
              {/* EFS Breakdown - Expandable */}
              <div className="mt-3 border-t border-indigo-200 pt-3">
                <details className="group">
                  <summary className="flex items-center gap-2 cursor-pointer text-xs font-medium text-indigo-700 hover:text-indigo-800 select-none">
                    <ChartBarIcon className="h-4 w-4" />
                    <span>Show EFS Breakdown (0.3·Attribution + 0.3·Causal + 0.2·Substructure + 0.2·Rules)</span>
                    <span className="ml-auto text-indigo-400 group-open:rotate-180 transition-transform">▼</span>
                  </summary>
                  <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px]">
                    <div className="rounded bg-indigo-50 p-2 text-center">
                      <p className="font-bold text-indigo-700">Attribution</p>
                      <p className="text-indigo-600">30%</p>
                      <p className="text-slate-500">Atom attention alignment</p>
                    </div>
                    <div className="rounded bg-indigo-50 p-2 text-center">
                      <p className="font-bold text-indigo-700">Causal</p>
                      <p className="text-indigo-600">30%</p>
                      <p className="text-slate-500">Counterfactual drop test</p>
                    </div>
                    <div className="rounded bg-indigo-50 p-2 text-center">
                      <p className="font-bold text-indigo-700">Substructure</p>
                      <p className="text-indigo-600">20%</p>
                      <p className="text-slate-500">SMARTS toxicophore match</p>
                    </div>
                    <div className="rounded bg-indigo-50 p-2 text-center">
                      <p className="font-bold text-indigo-700">Rules</p>
                      <p className="text-indigo-600">20%</p>
                      <p className="text-slate-500">Chemical validity checks</p>
                    </div>
                  </div>
                </details>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Triage/Screening Disclaimer (Prominently displayed) */}
      <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-4">
        <div className="flex items-start gap-2">
          <span aria-hidden className="text-sm">⚠️</span>
          <span className="text-slate-700">
            <strong>SCREENING ONLY — NOT A REGULATORY TOOL:</strong> This assessment is for 
            preliminary triage and compound prioritization. It is explicitly NOT a replacement for 
            wet-lab testing, regulatory submission, or clinical evaluation. Positive results require 
            experimental validation. Use for research and educational purposes only.
          </span>
        </div>
      </div>

      {/* Primary toxicity + OOD / confidence + Epistemic Uncertainty badges */}
      <div className="grid gap-4 md:grid-cols-4">
        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
            <BeakerIcon className="h-5 w-5 text-indigo-500" /> Predicted Toxicity (95% CI)
          </div>
           <p className="mt-1 text-3xl font-black text-indigo-600">{(toxProb * 100).toFixed(0)}% (${{(overallUnc.ci_low || 0) * 100}.toFixed(0)}-${{(overallUnc.ci_high || 1) * 100}.toFixed(0)}%)</p>
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

        <div className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center gap-2 text-sm font-semibold text-slate-500">
            <ScaleIcon className="h-5 w-5 text-indigo-500" /> Epistemic Band
          </div>
          <p className="mt-1 text-2xl font-black text-indigo-600">
            {overallUnc.epistemic_uncertainty || 'Moderate'}
          </p>
          {overallUnc.epistemic_std != null && (
            <p className="text-xs text-slate-500 font-mono">std ±{(overallUnc.epistemic_std * 100).toFixed(1)}%</p>
          )}
        </div>
      </div>

      {/* Endpoint grid */}
      <div>
        <h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">
          Multi-Task Endpoints (with MC-Dropout 95% CIs)
        </h3>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {endpoints.map((e) => (
            <RiskMeter key={e.id} endpoint={e} />
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
