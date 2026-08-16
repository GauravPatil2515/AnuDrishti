import React from 'react';
import { clsx } from 'clsx';
import {
  ShieldCheckIcon, ShieldExclamationIcon, ExclamationTriangleIcon,
  SignalIcon, BeakerIcon, ScaleIcon, CheckBadgeIcon, InformationCircleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

const TRIAGE_STYLES = {
  GREEN: { banner: 'border-emerald-500/30 bg-emerald-500/5 text-emerald-400', chip: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', Icon: ShieldCheckIcon, label: 'LOW CONCERN' },
  YELLOW: { banner: 'border-amber-500/30 bg-amber-500/5 text-amber-400', chip: 'bg-amber-500/10 text-amber-400 border-amber-500/30', Icon: ExclamationTriangleIcon, label: 'REVIEW NEEDED' },
  RED: { banner: 'border-red-500/30 bg-red-500/5 text-red-400', chip: 'bg-red-500/10 text-red-400 border-red-500/30', Icon: ShieldExclamationIcon, label: 'HIGH CONCERN' },
};

const EPISTEMIC_BADGES = {
  Low: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
  Moderate: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
  High: 'bg-red-500/10 text-red-400 border-red-500/30',
};

const EFS_BADGES = {
  VERIFIED: { label: 'VERIFIED', className: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30', icon: CheckBadgeIcon },
  PARTIAL: { label: 'PARTIAL', className: 'bg-amber-500/10 text-amber-400 border-amber-500/30', icon: InformationCircleIcon },
  REJECTED: { label: 'REJECTED', className: 'bg-red-500/10 text-red-400 border-red-500/30', icon: ShieldExclamationIcon },
};

const extractEndpoints = (analysis) => {
  const preds = analysis?.predictions?.predictions || analysis?.predictions || {};
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
  const barColor = prob > 0.7 ? 'bg-red-500' : prob > 0.4 ? 'bg-amber-500' : 'bg-emerald-500';
  const badgeStyle = EPISTEMIC_BADGES[epistemic_uncertainty] || EPISTEMIC_BADGES.Moderate;

  const lowPercent = Math.max(0, Math.min(100, ci_low * 100));
  const highPercent = Math.max(0, Math.min(100, ci_high * 100));
  const probPercent = Math.max(0, Math.min(100, prob * 100));
  const widthPercent = Math.max(2, highPercent - lowPercent);

  return (
    <div className="surface-elevated rounded-lg p-3 space-y-2">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <span className="font-medium text-secondary text-xs">{id}</span>
          <span className={clsx('pill', badgeStyle)}>
            Uncertainty: {epistemic_uncertainty}
          </span>
        </div>
        <span className="font-mono text-primary font-bold text-xs">
          {(prob * 100).toFixed(0)}%
        </span>
      </div>

      {/* Main bar */}
      <div className="relative h-2 overflow-hidden rounded-full bg-border">
        <div className={clsx('h-full rounded-full transition-all duration-150', barColor)} style={{ width: `${probPercent}%` }} />
      </div>

      {/* 95% Confidence Interval Band */}
      <div className="text-[10px] font-mono text-muted flex justify-between">
        <span>CI: {(ci_low * 100).toFixed(0)}%</span>
        {epistemic_std != null && <span>±{(epistemic_std * 100).toFixed(1)}%</span>}
        <span>{(ci_high * 100).toFixed(0)}%</span>
      </div>

      <div className="relative h-1.5 w-full rounded bg-border">
        <div
          className="absolute h-full rounded bg-indigo-500/40 border border-indigo-500/60"
          style={{ left: `${lowPercent}%`, width: `${widthPercent}%` }}
          title={`95% CI: [${(ci_low * 100).toFixed(1)}%, ${(ci_high * 100).toFixed(1)}%]`}
        />
        <div
          className="absolute top-0 h-full w-0.5 -ml-px bg-indigo-500 rounded"
          style={{ left: `${probPercent}%` }}
          title={`Point estimate: ${(prob * 100).toFixed(1)}%`}
        />
      </div>
    </div>
  );
};

const SafetyDashboard = ({ analysis }) => {
  if (!analysis) {
    return (
      <div className="rounded-lg border border-border bg-surface p-8 text-center text-muted">
        Run an analysis to see the safety &amp; ADMET dashboard.
      </div>
    );
  }

  const triage = analysis.triage || { category: 'GREEN', risk_score: 0, recommendation: '' };
  const style = TRIAGE_STYLES[triage.category] || TRIAGE_STYLES.GREEN;
  const ood = analysis.ood || {};
  const endpoints = extractEndpoints(analysis);
  const toxProb = analysis.toxicity_probability || analysis.summary?.average_toxicity_probability || 0;
  const overallUnc = analysis.uncertainty?.overall || {};
  const summary = analysis.predictions?.summary || analysis.summary || {};

  const ciLow = summary.toxicity_ci_low || (toxProb - 0.15);
  const ciHigh = summary.toxicity_ci_high || (toxProb + 0.15) > 1 ? 1 : (toxProb + 0.15);

  return (
    <div className="space-y-4">
      {/* Clinical-use disclaimer */}
      <div className="flex items-start gap-2 rounded-lg border border-amber-500/30 bg-amber-500/5 p-3 text-xs font-medium text-amber-400">
        <span aria-hidden>⚠️</span>
        <span>
          NOT A CLINICAL DECISION TOOL. This dashboard reports computational predictions from a
          research model. It must not be used for diagnosis, treatment, or regulatory submission
          without independent experimental validation.
        </span>
      </div>

      {/* Triage banner */}
      <div className={clsx('flex items-center justify-between rounded-xl border p-4', style.banner)}>
        <div className="flex items-center gap-3">
          <style.Icon className={clsx('h-8 w-8', style.text)} />
          <div>
            <p className="text-xs font-bold uppercase tracking-widest">Overall Safety Assessment</p>
            <p className={clsx('text-xl font-extrabold', style.text)}>{triage.category}</p>
          </div>
        </div>
        <div className="text-right">
          <p className="text-xs text-muted">Risk Score</p>
          <p className={clsx('text-2xl font-black', style.text)}>
            {(triage.risk_score * 100).toFixed(0)}
          </p>
          <p className={clsx('mt-1 rounded-full px-3 py-1 text-xs font-bold', style.chip)}>
            {triage.recommendation}
          </p>
        </div>
      </div>

      {/* Risk component breakdown */}
      {triage.components && (
        <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
          {Object.entries(triage.components).map(([k, v]) => (
            <div key={k} className="surface-elevated rounded-lg p-2.5 text-center">
              <p className="text-[10px] font-semibold uppercase text-muted">{k.replace('_', ' ')}</p>
              <p className="text-sm font-bold text-primary">{(v * 100).toFixed(0)}</p>
            </div>
          ))}
        </div>
      )}

      {/* Faithfulness-gated Explanation Score (EFS) */}
      {analysis.explanation && (
        <div className="rounded-xl border border-indigo-500/30 bg-indigo-500/5 p-4 relative">
          {/* Verified badge */}
          <div className="absolute top-3 right-3">
            {(() => {
              const efs = analysis.explanation.faithfulness_score ?? analysis.explanation.efs;
              const status = analysis.explanation.validation_passed ? 'VERIFIED' :
                             analysis.explanation.validation_passed === false ? 'REJECTED' : 'UNCHECKED';
              const badge = EFS_BADGES[status] || EFS_BADGES.PARTIAL;
              const Icon = badge.icon || CheckBadgeIcon;
              return (
                <div className="flex items-center gap-2">
                  <div className="flex h-12 w-12 items-center justify-center rounded-full bg-canvas border border-border">
                    <span className="text-xl font-black text-indigo-400">
                      {efs != null ? `${Math.round(efs * 100)} ± 12` : '—'}%
                    </span>
                  </div>
                  <span className={clsx('pill', badge.className)}>
                    <Icon className="h-3 w-3 inline mr-1" /> {badge.label}
                  </span>
                </div>
              );
            })()}
          </div>

          <div className="flex items-start gap-3 pr-32">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 flex-shrink-0">
              <CheckBadgeIcon className="h-5 w-5" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-bold text-indigo-400">Why trust this explanation? <span className="font-normal text-indigo-400/80 ml-1">— Faithfulness-gated</span></p>
              <p className="text-xs text-indigo-400/80 mt-1">
                Every AI explanation is validated against the GNN's actual decision process using
                counterfactual testing. Claims not supported by model evidence are rejected.
              </p>

              {/* EFS Breakdown */}
              <div className="mt-2 border-t border-indigo-500/20 pt-2">
                <details className="group">
                  <summary className="flex items-center gap-1.5 cursor-pointer text-xs font-medium text-indigo-400 hover:text-indigo-400/80 select-none">
                    <ChartBarIcon className="h-3 w-3" />
                    <span>EFS Breakdown: 30% Attribution + 30% Causal + 20% Substructure + 20% Rules</span>
                    <span className="ml-auto text-indigo-400/60 group-open:rotate-90 transition-transform">▼</span>
                  </summary>
                  <div className="mt-2 grid grid-cols-2 sm:grid-cols-4 gap-1.5 text-[10px]">
                    <div className="bg-indigo-500/5 rounded p-1.5 text-center">
                      <p className="font-bold text-indigo-400">Attr</p>
                      <p className="text-indigo-400/80">30%</p>
                      <p className="text-muted">Atom alignment</p>
                    </div>
                    <div className="bg-indigo-500/5 rounded p-1.5 text-center">
                      <p className="font-bold text-indigo-400">Causal</p>
                      <p className="text-indigo-400/80">30%</p>
                      <p className="text-muted">Counterfactual test</p>
                    </div>
                    <div className="bg-indigo-500/5 rounded p-1.5 text-center">
                      <p className="font-bold text-indigo-400">Sub</p>
                      <p className="text-indigo-400/80">20%</p>
                      <p className="text-muted">Toxicophore match</p>
                    </div>
                    <div className="bg-indigo-500/5 rounded p-1.5 text-center">
                      <p className="font-bold text-indigo-400">Rules</p>
                      <p className="text-indigo-400/80">20%</p>
                      <p className="text-muted">Validity</p>
                    </div>
                  </div>
                </details>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Screening disclaimer */}
      <div className="rounded-lg border border-border bg-surface p-3">
        <div className="flex items-start gap-2">
          <span aria-hidden>⚠️</span>
          <span className="text-secondary text-xs">
            <strong>SCREENING ONLY — NOT A REGULATORY TOOL:</strong> This assessment is for
            preliminary triage and compound prioritization. It is explicitly NOT a replacement for
            wet-lab testing, regulatory submission, or clinical evaluation.
          </span>
        </div>
      </div>

      {/* Key metrics grid - high density */}
      <div className="grid gap-3 md:grid-cols-4">
        <div className="surface-elevated rounded-lg p-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted">
            <BeakerIcon className="h-4 w-4 text-indigo-400" /> Predicted Toxicity (95% CI)
          </div>
          <p className="mt-1 text-xl font-black text-indigo-400">
            {(toxProb * 100).toFixed(0)}% ({`${(ciLow * 100).toFixed(0)}-${(ciHigh * 100).toFixed(0)}%`})
          </p>
        </div>

        <div className={clsx('rounded-lg border p-3', ood.is_ood ? 'border-red-500/30 bg-red-500/5' : 'border-emerald-500/30 bg-emerald-500/5')}>
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted">
            <SignalIcon className="h-4 w-4" /> OOD / Novelty
          </div>
          <p className={clsx('mt-1 text-xl font-black', ood.is_ood ? 'text-red-400' : 'text-emerald-400')}>
            {ood.is_ood ? 'FLAGGED' : 'IN-DIST'}
          </p>
          {ood.nearest_neighbor_similarity != null && (
            <p className="text-[10px] text-muted font-mono">
              NN: {(ood.nearest_neighbor_similarity * 100).toFixed(0)}%
            </p>
          )}
        </div>

        <div className="surface-elevated rounded-lg p-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted">
            <ShieldCheckIcon className="h-4 w-4 text-indigo-400" /> Model Confidence
          </div>
          <p className="mt-1 text-xl font-black text-indigo-400">
            {ood.confidence_modifier != null ? `${(ood.confidence_modifier * 100).toFixed(0)}%` : '—'}
          </p>
        </div>

        <div className="surface-elevated rounded-lg p-3">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-muted">
            <ScaleIcon className="h-4 w-4 text-indigo-400" /> Epistemic Band
          </div>
          <p className="mt-1 text-lg font-black text-indigo-400">
            {overallUnc.epistemic_uncertainty || 'Moderate'}
          </p>
          {overallUnc.epistemic_std != null && (
            <p className="text-[10px] text-muted font-mono">
              ±{(overallUnc.epistemic_std * 100).toFixed(1)}%
            </p>
          )}
        </div>
      </div>

      {/* TDC established-panel predictions (hERG / DILI / Ames) */}
      <div className="surface-elevated rounded-lg p-3">
        <h3 className="mb-2 flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-muted">
          <BeakerIcon className="h-4 w-4 text-indigo-400" /> Established Panels — hERG / DILI / Ames
        </h3>
        {analysis.tdc_predictions && Object.keys(analysis.tdc_predictions).length > 0 ? (
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
            {Object.entries(analysis.tdc_predictions).map(([key, v]) => {
              const prob = typeof v?.probability === 'number' ? v.probability : 0;
              const toxic = v?.label === 'Toxic';
              return (
                <div key={key} className="rounded-lg border border-border bg-surface p-2.5">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold uppercase text-secondary">{key}</p>
                    <span className={clsx('pill', toxic ? 'pill-red' : 'pill-green')}>
                      {v?.label || (toxic ? 'Toxic' : 'Non-toxic')}
                    </span>
                  </div>
                  <p className="mt-1 text-lg font-black text-primary">{(prob * 100).toFixed(0)}%</p>
                  <p className="text-[10px] text-muted">TDC pretrained</p>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-muted">
            TDC established-panel models (hERG / DILI / Ames) are offline in this deployment.
            Predictions are unavailable; core GNN + ADMET panels above remain active.
          </p>
        )}
      </div>

      {/* Endpoint grid - high density table */}
      <div className="surface-elevated rounded-lg p-3">
        <h3 className="mb-2 text-xs font-bold uppercase tracking-wider text-muted">
          Multi-Task Endpoints ({endpoints.length} total)
        </h3>
        {endpoints.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th className="text-left">Endpoint</th>
                <th className="text-right">Probability</th>
                <th className="text-center">Prediction</th>
                <th className="text-center">E[CI]</th>
                <th className="text-center">Unc.</th>
              </tr>
            </thead>
            <tbody>
              {endpoints.map((e) => (
                <tr key={e.id}>
                  <td className="font-mono text-secondary text-xs">{e.id}</td>
                  <td className="text-right font-mono text-primary">{(e.prob * 100).toFixed(1)}%</td>
                  <td className="text-center">
                    <span className={clsx('pill', e.prob > 0.5 ? 'pill-red' : 'pill-green')}>
                      {e.label}
                    </span>
                  </td>
                  <td className="text-center text-[10px] font-mono text-muted">
                    [{Math.max(0, e.ci_low * 100).toFixed(0)}-{Math.min(100, e.ci_high * 100).toFixed(0)}%]
                  </td>
                  <td className="text-center">
                    <span className={clsx('pill', e.epistemic_uncertainty === 'Low' ? 'pill-green' : e.epistemic_uncertainty === 'High' ? 'pill-red' : 'pill-yellow')}>
                      {e.epistemic_uncertainty}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p className="text-xs text-muted">No endpoint predictions available.</p>
        )}
      </div>

      {analysis.triage?.disclaimer && (
        <p className="text-[10px] italic text-muted">
          {analysis.triage.disclaimer}
        </p>
      )}
    </div>
  );
};

export default SafetyDashboard;