import React from 'react';
import { clsx } from 'clsx';
import {
  ArrowDownTrayIcon, TableCellsIcon, CheckBadgeIcon,
  ShieldExclamationIcon, InformationCircleIcon
} from '@heroicons/react/24/outline';

const CATEGORY_STYLE = {
  GREEN: 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/30',
  YELLOW: 'bg-amber-500/10 text-amber-400 border border-amber-500/30',
  RED: 'bg-red-500/10 text-red-400 border border-red-500/30',
};

const LibraryScreening = ({ batchResult }) => {
  if (!batchResult || batchResult.total_processed === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border bg-surface p-8 text-center text-muted">
        Upload a molecular library in <b>Mode B</b> to screen and rank candidates.
      </div>
    );
  }

  const results = batchResult.results || [];

  const exportCsv = () => {
    const rows = [['SMILES', 'Category', 'RiskScore', 'Toxicity', 'OOD', 'EFS', 'Trust Status']];
    results.forEach((r) => {
      const efs = r.explanation?.faithfulness_score ?? r.explanation?.efs ?? '';
      const efsVal = typeof efs === 'number' ? efs.toFixed(2) : efs;
      const status = r.explanation?.validation_passed === true ? 'VERIFIED' :
                     r.explanation?.validation_passed === false ? 'REJECTED' : 'UNCHECKED';
      rows.push([
        r.smiles,
        r.triage?.category || '',
        r.triage?.risk_score ?? '',
        r.toxicity_probability ?? '',
        r.ood?.is_ood ?? '',
        efsVal,
        status,
      ]);
    });
    const csv = rows.map((x) => x.join(',')).join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'pharmaguard_library.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5 text-xs text-secondary">
          <TableCellsIcon className="h-3 w-3" />
          <span className="font-bold text-primary">{batchResult.total_processed}</span> molecules screened
        </div>
        <button
          onClick={exportCsv}
          className="btn btn-secondary text-xs"
        >
          <ArrowDownTrayIcon className="h-3 w-3 mr-1" /> Export CSV
        </button>
      </div>

      {/* Dense data table */}
      <div className="table-container">
        <table className="table">
          <thead>
            <tr>
              <th className="w-8">#</th>
              <th>SMILES</th>
              <th className="w-28">Triage</th>
              <th className="w-16 text-right">Risk</th>
              <th className="w-20">Toxicity</th>
              <th className="w-24">OOD</th>
              <th className="w-16">EFS</th>
              <th className="w-28">Trust</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr key={i}>
                <td className="text-muted">{i + 1}</td>
                <td className="max-w-[240px] truncate font-mono text-xs text-secondary">
                  {r.smiles}
                  {r.error && <span className="ml-1 text-red">{r.error}</span>}
                </td>
                <td>
                  <span className={clsx('pill text-[9px]',
                    CATEGORY_STYLE[r.triage?.category] || 'pill-gray'
                  )}>
                    {r.triage?.category || '—'}
                  </span>
                </td>
                <td className="font-mono text-secondary">
                  {r.triage?.risk_score != null ? `${(r.triage.risk_score * 100).toFixed(0)}` : '—'}
                </td>
                <td>
                  {r.toxicity_probability != null ? (
                    <span className={clsx(
                      'font-mono font-bold text-xs',
                      r.toxicity_probability > 0.7 ? 'text-red-400' :
                      r.toxicity_probability > 0.4 ? 'text-amber-400' : 'text-emerald-400'
                    )}>
                      {(r.toxicity_probability * 100).toFixed(0)}%
                    </span>
                  ) : '—'}
                </td>
                <td>
                  {r.ood?.is_ood ? (
                    <span className="flex items-center gap-1 text-xs text-red-400">
                      <InformationCircleIcon className="h-3 w-3" /> FLAGGED
                    </span>
                  ) : (
                    <span className="text-xs text-emerald-400">in-dist</span>
                  )}
                </td>
                <td className="font-mono text-secondary text-xs">
                  {(() => {
                    const efs = r.explanation?.faithfulness_score ?? r.explanation?.efs;
                    if (typeof efs === 'number') {
                      return `${(efs * 100).toFixed(0)}%`;
                    }
                    return '—';
                  })()}
                </td>
                <td>
                  {r.explanation?.validation_passed === true ? (
                    <span className="pill pill-green text-[9px]">
                      <CheckBadgeIcon className="h-2 w-2 mr-0.5" /> VERIFIED
                    </span>
                  ) : r.explanation?.validation_passed === false ? (
                    <span className="pill pill-red text-[9px]">
                      <ShieldExclamationIcon className="h-2 w-2 mr-0.5" /> REJECTED
                    </span>
                  ) : (
                    <span className="text-xs text-muted">UNCHECKED</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default LibraryScreening;