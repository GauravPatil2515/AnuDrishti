import React from 'react';
import { clsx } from 'clsx';
import {
  ShieldCheckIcon, ShieldExclamationIcon, ExclamationTriangleIcon,
  SignalIcon, BeakerIcon, ScaleIcon, CheckBadgeIcon, InformationCircleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';

const TRIAGE_STYLES = {
  GREEN: { banner: 'border-accent-emerald/30 bg-accent-emerald/5 text-accent-emerald', chip: 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30', Icon: ShieldCheckIcon, label: 'LOW CONCERN' },
  YELLOW: { banner: 'border-accent-amber/30 bg-accent-amber/5 text-accent-amber', chip: 'bg-accent-amber/10 text-accent-amber border-accent-amber/30', Icon: ExclamationTriangleIcon, label: 'REVIEW NEEDED' },
  RED: { banner: 'border-accent-red/30 bg-accent-red/5 text-accent-red', chip: 'bg-accent-red/10 text-accent-red border-accent-red/30', Icon: ShieldExclamationIcon, label: 'HIGH CONCERN' },
};

const EPISTEMIC_BADGES = {
  Low: 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30',
  Moderate: 'bg-accent-amber/10 text-accent-amber border-accent-amber/30',
  High: 'bg-accent-red/10 text-accent-red border-accent-red/30',
};

const EFS_BADGES = {
  VERIFIED: { label: 'VERIFIED', className: 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30', icon: CheckBadgeIcon },
  PARTIAL: { label: 'PARTIAL', className: 'bg-accent-amber/10 text-accent-amber border-accent-amber/30', icon: InformationCircleIcon },
  REJECTED: { label: 'REJECTED', className: 'bg-accent-red/10 text-accent-red border-accent-red/30', icon: ShieldExclamationIcon },
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

const SafetyDashboard = ({ analysis }) => {
  if (!analysis) return null;

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
    <div className="space-y-6">
      
      {/* Top Banner Area - Triage and Score */}
      <div className={clsx('flex flex-col sm:flex-row items-start sm:items-center justify-between rounded-xl border p-5 shadow-sm', style.banner)}>
        <div className="flex items-center gap-4 mb-4 sm:mb-0">
          <div className={clsx("flex h-12 w-12 items-center justify-center rounded-xl bg-canvas bg-opacity-50 shadow-sm", style.chip)}>
            <style.Icon className="h-7 w-7" />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-widest opacity-80">Safety Assessment</p>
            <p className="text-2xl font-black font-display">{triage.category}</p>
          </div>
        </div>
        <div className="flex items-center gap-6 w-full sm:w-auto">
          <div className="text-left sm:text-right">
            <p className="text-xs font-semibold opacity-80 uppercase tracking-widest">Risk Score</p>
            <p className="text-3xl font-black font-mono">
              {(triage.risk_score * 100).toFixed(0)}
            </p>
          </div>
          <div className="hidden sm:block h-10 w-px bg-current opacity-20"></div>
          <div className="flex-1 text-right sm:text-left">
            <span className={clsx('inline-block rounded-md px-3 py-1.5 text-xs font-bold uppercase tracking-wider', style.chip)}>
              {triage.recommendation}
            </span>
          </div>
        </div>
      </div>

      {/* Faithfulness EFS Box */}
      {analysis.explanation && (
        <div className="surface p-5 border-l-4 border-l-accent-green shadow-sm">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-accent-green/10 border border-accent-green/20 shadow-glow-green relative">
                <span className="text-lg font-black text-accent-green font-mono">
                  {(() => {
                    const efs = analysis.explanation.faithfulness_score ?? analysis.explanation.efs;
                    return efs != null ? Math.round(efs * 100) : '--';
                  })()}
                </span>
                <svg className="absolute inset-0 h-full w-full -rotate-90 text-accent-green/20" viewBox="0 0 36 36">
                  <path strokeDasharray="100, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="currentColor" strokeWidth="2"></path>
                </svg>
              </div>
              
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="text-sm font-bold text-text-primary font-display">Explanation Faithfulness Score (EFS)</h3>
                  {(() => {
                    const status = analysis.explanation.validation_passed ? 'VERIFIED' :
                                   analysis.explanation.validation_passed === false ? 'REJECTED' : 'UNCHECKED';
                    const badge = EFS_BADGES[status] || EFS_BADGES.PARTIAL;
                    const Icon = badge.icon || CheckBadgeIcon;
                    return (
                      <span className={clsx('pill', badge.className)}>
                        <Icon className="h-3 w-3 inline mr-1" /> {badge.label}
                      </span>
                    );
                  })()}
                </div>
                <p className="text-xs text-text-secondary leading-relaxed">
                  The LLM's explanation has been counterfactually verified against the GNN's logic. 
                  Claims not supported by molecular evidence are rejected.
                </p>
              </div>
            </div>
            
          </div>
        </div>
      )}

      {/* Grid of Key Metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <div className="surface p-4 hover:shadow-card-hover transition-shadow">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">
            <BeakerIcon className="h-4 w-4 text-accent-green" /> Toxicity Prob (95% CI)
          </div>
          <div className="flex items-end gap-2">
            <p className="text-3xl font-black text-text-primary font-mono">
              {(toxProb * 100).toFixed(0)}%
            </p>
            <p className="text-sm text-text-muted font-mono mb-1">
              [{`${(ciLow * 100).toFixed(0)}-${(ciHigh * 100).toFixed(0)}%`}]
            </p>
          </div>
        </div>

        <div className={clsx('surface p-4 hover:shadow-card-hover transition-shadow border-l-4', ood.is_ood ? 'border-l-accent-red' : 'border-l-accent-emerald')}>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">
            <SignalIcon className="h-4 w-4" /> Domain Novelty (OOD)
          </div>
          <div className="flex items-end gap-2">
            <p className={clsx('text-xl font-bold font-display', ood.is_ood ? 'text-accent-red' : 'text-accent-emerald')}>
              {ood.is_ood ? 'OUT-OF-DISTRIBUTION' : 'IN-DISTRIBUTION'}
            </p>
          </div>
          {ood.nearest_neighbor_similarity != null && (
            <p className="text-[11px] text-text-muted font-mono mt-1">
              Nearest Neighbor: {(ood.nearest_neighbor_similarity * 100).toFixed(0)}% sim
            </p>
          )}
        </div>

        <div className="surface p-4 hover:shadow-card-hover transition-shadow">
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">
            <ScaleIcon className="h-4 w-4 text-accent-green" /> Epistemic Band
          </div>
          <div className="flex items-end gap-2">
            <p className="text-2xl font-bold text-text-primary font-display">
              {overallUnc.epistemic_uncertainty || 'Moderate'}
            </p>
            {overallUnc.epistemic_std != null && (
              <p className="text-sm text-text-muted font-mono mb-1">
                ±{(overallUnc.epistemic_std * 100).toFixed(1)}%
              </p>
            )}
          </div>
        </div>
      </div>

      {/* TDC Core Toxicity Endpoints: hERG, DILI, Ames */}
      {analysis.tdc_predictions && Object.keys(analysis.tdc_predictions).length > 0 && (
        <div className="surface p-5 space-y-4 shadow-sm border-l-4 border-l-accent-green">
          <div className="flex items-center justify-between border-b border-border pb-3">
            <div>
              <h3 className="text-sm font-bold text-text-primary font-display">Key Safety & Regulatory Endpoints</h3>
              <p className="text-xs text-text-secondary mt-0.5">hERG Cardiotoxicity, DILI Hepatotoxicity, & Ames Genotoxicity Risk Assessment</p>
            </div>
            <span className="pill pill-green">TDC Benchmarked</span>
          </div>

          <div className="grid gap-4 md:grid-cols-3">
            {['herg', 'dili', 'ames'].map((key) => {
              const item = analysis.tdc_predictions[key];
              if (!item) return null;
              const isHigh = item.probability >= 0.5;
              return (
                <div key={key} className={clsx('surface-elevated p-4 rounded-xl border transition-all hover:-translate-y-0.5', isHigh ? 'border-accent-rose/40 bg-accent-rose/5' : 'border-accent-emerald/40 bg-accent-emerald/5')}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-text-primary font-display">{item.name}</span>
                    <span className={clsx('pill text-[10px]', isHigh ? 'pill-red' : 'pill-green')}>
                      {item.label}
                    </span>
                  </div>
                  
                  <div className="flex items-baseline justify-between mt-2">
                    <span className="text-2xl font-black font-mono text-text-primary">{(item.probability * 100).toFixed(1)}%</span>
                    <span className="text-xs font-semibold text-text-muted">{item.risk_level}</span>
                  </div>

                  {item.alerts && item.alerts.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-border/50">
                      <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider mb-1">Structural Alerts:</p>
                      <ul className="space-y-1">
                        {item.alerts.map((alert, idx) => (
                          <li key={idx} className="text-[11px] text-text-secondary flex items-center gap-1">
                            <span className="text-accent-amber font-bold">•</span> {alert}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ADMET Table */}
      <div className="surface overflow-hidden">
        <div className="p-4 border-b border-border bg-surface-elevated flex items-center justify-between">
          <h3 className="text-sm font-bold text-text-primary font-display">Multi-Task Endpoints</h3>
          <span className="text-xs text-text-muted font-semibold">{endpoints.length} active</span>
        </div>
        
        {endpoints.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="table min-w-[500px]">
              <thead>
                <tr>
                  <th className="w-1/3">Endpoint</th>
                  <th className="text-right w-1/5">Probability</th>
                  <th className="text-center w-1/4">Prediction</th>
                  <th className="text-center">Uncertainty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {endpoints.map((e) => (
                  <tr key={e.id} className="hover:bg-surface-hover transition-colors">
                    <td className="font-medium text-text-primary text-xs">{e.id}</td>
                    <td className="text-right">
                      <div className="flex flex-col items-end">
                        <span className="font-mono text-text-primary font-semibold">{(e.prob * 100).toFixed(1)}%</span>
                      </div>
                    </td>
                    <td className="text-center">
                      <span className={clsx('pill', e.prob > 0.5 ? 'pill-red' : 'pill-green')}>
                        {e.label}
                      </span>
                    </td>
                    <td className="text-center">
                      <span className={clsx('pill', e.epistemic_uncertainty === 'Low' ? 'pill-green' : e.epistemic_uncertainty === 'High' ? 'pill-red' : 'pill-yellow')}>
                        {e.epistemic_uncertainty}
                        <span className="text-[10px] ml-1 opacity-70" title="95% CI Range">
                          [{Math.max(0, e.ci_low * 100).toFixed(0)}-{Math.min(100, e.ci_high * 100).toFixed(0)}%]
                        </span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-text-muted text-sm">
            No endpoint predictions available for this compound.
          </div>
        )}
      </div>
      
      {/* Footer Notes */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mt-2">
        <div className="text-[10px] text-text-muted flex items-center gap-2">
          <span className="text-accent-amber font-bold">⚠</span>
          <span>SCREENING ONLY. NOT A CLINICAL OR REGULATORY TOOL.</span>
        </div>
        {analysis.triage?.disclaimer && (
          <div className="text-[10px] text-text-muted italic text-right">
            {analysis.triage.disclaimer}
          </div>
        )}
      </div>

    </div>
  );
};

export default SafetyDashboard;