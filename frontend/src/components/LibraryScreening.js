import React from 'react';
import { clsx } from 'clsx';
import { ArrowDownTrayIcon, TableCellsIcon } from '@heroicons/react/24/outline';

const CATEGORY_STYLE = {
  GREEN: 'bg-emerald-100 text-emerald-700',
  YELLOW: 'bg-amber-100 text-amber-700',
  RED: 'bg-red-100 text-red-700',
};

const LibraryScreening = ({ batchResult }) => {
  if (!batchResult || batchResult.total_processed === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-400">
        Upload a molecular library in <b>Mode B</b> to screen and rank candidates.
      </div>
    );
  }

  const results = batchResult.results || [];
  const exportCsv = () => {
    const rows = [['SMILES', 'Category', 'RiskScore', 'Toxicity', 'OOD']];
    results.forEach((r) => {
      rows.push([
        r.smiles,
        r.triage?.category || '',
        r.triage?.risk_score ?? '',
        r.toxicity_probability ?? '',
        r.ood?.is_ood ?? '',
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
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-slate-500">
          <TableCellsIcon className="h-5 w-5" />
          <span className="font-bold text-slate-700">{batchResult.total_processed}</span> molecules screened
        </div>
        <button
          onClick={exportCsv}
          className="flex items-center gap-2 rounded-xl border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-600 hover:border-indigo-400"
        >
          <ArrowDownTrayIcon className="h-5 w-5" /> Export CSV
        </button>
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-xs uppercase text-slate-500">
            <tr>
              <th className="px-4 py-3">#</th>
              <th className="px-4 py-3">SMILES</th>
              <th className="px-4 py-3">Triage</th>
              <th className="px-4 py-3">Risk</th>
              <th className="px-4 py-3">Toxicity</th>
              <th className="px-4 py-3">OOD</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                <td className="px-4 py-2 text-slate-400">{i + 1}</td>
                <td className="max-w-[260px] truncate px-4 py-2 font-mono text-xs text-slate-600">
                  {r.smiles}
                  {r.error && <span className="ml-2 text-red-500">{r.error}</span>}
                </td>
                <td className="px-4 py-2">
                  <span className={clsx('rounded-full px-2 py-1 text-xs font-bold', CATEGORY_STYLE[r.triage?.category] || 'bg-slate-100 text-slate-600')}>
                    {r.triage?.category || '—'}
                  </span>
                </td>
                <td className="px-4 py-2 font-mono text-slate-600">
                  {r.triage?.risk_score != null ? (r.triage.risk_score * 100).toFixed(0) : '—'}
                </td>
                <td className="px-4 py-2 font-mono text-slate-600">
                  {r.toxicity_probability != null ? (r.toxicity_probability * 100).toFixed(0) + '%' : '—'}
                </td>
                <td className="px-4 py-2">
                  {r.ood?.is_ood ? (
                    <span className="text-red-600">FLAGGED</span>
                  ) : (
                    <span className="text-emerald-600">in-dist</span>
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
