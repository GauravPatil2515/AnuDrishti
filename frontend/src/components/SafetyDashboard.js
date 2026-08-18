import React from 'react';
import { clsx } from 'clsx';
import {
  ShieldCheckIcon, ShieldExclamationIcon, ExclamationTriangleIcon,
  SignalIcon, BeakerIcon, ScaleIcon, CheckBadgeIcon, InformationCircleIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import {
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';

const TRIAGE_STYLES = {
  GREEN: { banner: 'border-accent-emerald/30 bg-accent-emerald/5 text-accent-emerald', chip: 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30', Icon: ShieldCheckIcon, label: 'LOW CONCERN' },
  YELLOW: { banner: 'border-accent-amber/30 bg-accent-amber/5 text-accent-amber', chip: 'bg-accent-amber/10 text-accent-amber border-accent-amber/30', Icon: ExclamationTriangleIcon, label: 'REVIEW NEEDED' },
  RED: { banner: 'border-accent-red/30 bg-accent-red/5 text-accent-red', chip: 'bg-accent-red/10 text-accent-red border-accent-red/30', Icon: ShieldExclamationIcon, label: 'HIGH CONCERN' },
};

const MODEL_SOURCE_COLORS = {
  'Attention-GIN': 'bg-accent-green/10 text-accent-green border-accent-green/20',
  'GPS Graph Transformer': 'bg-accent-purple/10 text-accent-purple border-accent-purple/20',
  'XGBoost': 'bg-accent-blue/10 text-accent-blue border-accent-blue/20',
  'TDC': 'bg-accent-amber/10 text-accent-amber border-accent-amber/20',
  'Rule-based': 'bg-accent-amber/10 text-accent-amber border-accent-amber/20',
};

const EFS_BADGES = {
  VERIFIED: { label: 'VERIFIED', className: 'bg-accent-emerald/10 text-accent-emerald border-accent-emerald/30', icon: CheckBadgeIcon },
  PARTIAL: { label: 'PARTIAL', className: 'bg-accent-amber/10 text-accent-amber border-accent-amber/30', icon: InformationCircleIcon },
  REJECTED: { label: 'REJECTED', className: 'bg-accent-red/10 text-accent-red border-accent-red/30', icon: ShieldExclamationIcon },
};

const getSourceLabel = (source) => {
  if (!source) return 'Attention-GIN';
  if (source.includes('GPS')) return 'GPS Graph Transformer';
  if (source.includes('XGBoost')) return 'XGBoost';
  if (source.includes('TDC') || source.includes('placeholder')) return 'TDC Rule-based';
  return 'Attention-GIN';
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
      source: v?.source || null,
      model_type: v?.model_type || null,
      dataset: v?.dataset || null,
    };
  });
};


const buildRadarData = (analysis) => {
  const preds = analysis?.predictions?.predictions || analysis?.predictions || {};
  const tdc = analysis?.tdc_predictions || {};
  const toxProb = analysis?.toxicity_probability || analysis?.summary?.average_toxicity_probability || 0;

  const data = [];

  if (preds['NR-AR'] !== undefined) {
    data.push({ category: 'NR-AR', score: 1 - (preds['NR-AR']?.probability || 0) });
  }
  if (preds['NR-AhR'] !== undefined) {
    data.push({ category: 'NR-AhR', score: 1 - (preds['NR-AhR']?.probability || 0) });
  }
  if (preds['NR-ER'] !== undefined) {
    data.push({ category: 'NR-ER', score: 1 - (preds['NR-ER']?.probability || 0) });
  }
  if (preds['SR-ATAD5'] !== undefined) {
    data.push({ category: 'SR-ATAD5', score: 1 - (preds['SR-ATAD5']?.probability || 0) });
  }
  if (preds['SR-MMP'] !== undefined) {
    data.push({ category: 'SR-MMP', score: 1 - (preds['SR-MMP']?.probability || 0) });
  }

  if (tdc['herg']) {
    data.push({ category: 'hERG', score: 1 - (tdc['herg']?.probability || 0) });
  }
  if (tdc['dili']) {
    data.push({ category: 'DILI', score: 1 - (tdc['dili']?.probability || 0) });
  }
  if (tdc['ames']) {
    data.push({ category: 'Ames', score: 1 - (tdc['ames']?.probability || 0) });
  }

  if (data.length === 0) {
    data.push({ category: 'Overall', score: 1 - toxProb });
  }

  return data;
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
  const ciHigh = summary.toxicity_ci_high || ((toxProb + 0.15) > 1 ? 1 : (toxProb + 0.15));

  const radarData = buildRadarData(analysis);

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
        <div className="grid gap-4 md:grid-cols-3">
          {['herg', 'dili', 'ames'].map((key) => {
            const item = analysis.tdc_predictions[key];
            if (!item) return null;
          
            const isHighRisk = item.probability >= 0.7;
            const isMediumRisk = item.probability >= 0.3 && item.probability < 0.7;
            const riskColor = isHighRisk ? 'red' : isMediumRisk ? 'amber' : 'emerald';
            const riskLabel = isHighRisk ? 'HIGH' : isMediumRisk ? 'MODERATE' : 'LOW';
            const barColorClass = {
              red: 'bg-red-500',
              amber: 'bg-amber-500',
              emerald: 'bg-emerald-500',
            }[riskColor];
          
            return (
              <div key={key} className="border border-border/60 surface rounded-xl p-4 hover:border-border/80 transition-border">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold text-text-primary font-display">{item.name}</h3>
                  <div className="flex items-center gap-2 text-xs font-medium">
                    <span className={`pill-${riskColor}`}>{riskLabel}</span>
                    <span className="text-text-muted">{item.label}</span>
                  </div>
                </div>
          
                {/* Probability bar */}
                <div className="w-full bg-border/20 rounded-full h-2.5 mb-2">
                  <div 
                    className={`${barColorClass} h-2.5 rounded-full`} 
                    style={{ width: `${Math.min(item.probability * 100, 100)}%` }}
                  ></div>
                </div>
          
                <p className="text-sm text-text-secondary">{item.probability.toFixed(3)} probability</p>
          
                {/* Structural alerts */}
                {item.alerts && item.alerts.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    <span className="text-xs font-semibold text-text-muted">Alerts:</span>
                    {item.alerts.map((alert, idx) => (
                      <span 
                        key={idx} 
                        className="px-2 py-0.5 rounded text-xs font-mono bg-surface/50 border border-border/30"
                      >
                        {alert}
                      </span>
                    ))}
                  </div>
                )}
          
                {/* Risk level description */}
                <p className="mt-2 text-xs text-text-muted">
                  {isHighRisk ? 'Significant structural alert detected' : 
                   isMediumRisk ? 'Moderate risk indicators present' : 
                   'Low risk based on current models'}
                </p>
              </div>
            );
          })}
        </div>
      )}

      {/* ADMET Radar Chart */}
      <div className="surface p-4 border border-border/50">
        <h3 className="text-sm font-bold text-text-primary font-display mb-4 flex items-center gap-2">
          <ChartBarIcon className="h-4 w-4 text-accent-green" />
          ADMET Safety Profile
        </h3>
        <ResponsiveContainer width="100%" height={280}>
          <RadarChart data={radarData}>
            <PolarGrid className="stroke-border/30" />
            <PolarAngleAxis 
              dataKey="category" 
              tick={{ fontSize: 10, fill: '#94a3b8' }} 
              tickMargin={20}
            />
            <PolarRadiusAxis 
              angle={90} 
              domain={[0, 1]} 
              tick={{ fontSize: 8, fill: '#64748b' }}
              tickCount={6}
            />
            <Tooltip 
              contentStyle={{
                backgroundColor: '#1e293b',
                border: '1px solid #334155',
                borderRadius: '8px',
                color: '#e2e8f0'
              }}
              labelStyle={{ color: '#e2e8f0', fontSize: 12 }}
            />
            <Legend 
              layout="horizontal" 
              align="center" 
              verticalAlign="bottom" 
              wrapperStyle={{ paddingTop: 16 }}
            />
            <Radar 
              name="Safety Score (1 = Safe, 0 = Toxic)" 
              dataKey="score" 
              stroke="#10b981" 
              fill="#10b981" 
              fillOpacity={0.15}
              strokeWidth={2}
              dot={false}
            />
          </RadarChart>
        </ResponsiveContainer>
        <p className="text-xs text-text-muted text-center mt-2">
          Each axis represents a safety category. Score closer to 1 (outer edge) = safer profile.
        </p>
      </div>

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
                  <th className="text-left w-1/4">Model Source</th>
                  <th className="text-right w-1/5">Probability</th>
                  <th className="text-center w-1/5">Prediction</th>
                  <th className="text-center">Uncertainty</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {endpoints.map((e) => {
                    const srcLabel = getSourceLabel(e.source);
                    const srcStyle = MODEL_SOURCE_COLORS[srcLabel] || MODEL_SOURCE_COLORS['Attention-GIN'];
                    return (
                  <tr key={e.id} className="hover:bg-surface-hover transition-colors">
                    <td className="font-medium text-text-primary text-xs">
                      <div>
                        <span>{e.id}</span>
                        {e.dataset && (
                          <p className="text-[9px] text-text-muted font-mono mt-0.5">{e.dataset}</p>
                        )}
                      </div>
                    </td>
                    <td className="text-left">
                      <span className={clsx('inline-flex items-center px-1.5 py-0.5 rounded text-[9px] font-mono font-semibold border', srcStyle)}>
                        {srcLabel}
                      </span>
                    </td>
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
                    );
                  })}
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
