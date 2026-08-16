import React, { useState } from 'react';
import { clsx } from 'clsx';
import { SwatchIcon, Squares2X2Icon } from '@heroicons/react/24/outline';
import StructureHeatmap from './StructureHeatmap';

/**
 * MolecularExplorer — renders the 2D structure with a real GNN attention
 * heatmap (atom importance overlay) and lists risk-associated substructures.
 */
const MolecularExplorer = ({ analysis }) => {
  const [toggle, setToggle] = useState('attention'); // attention | substructure

  if (!analysis) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-400">
        Run an analysis to explore the molecular graph and risk-associated regions.
      </div>
    );
  }

  const smiles = analysis.smiles;
  const substructures = analysis.substructures || [];
  const topSub = substructures[0];
  const attnSource = analysis.attention_source;

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {/* Molecule image + attention heatmap */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:col-span-2">
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wide text-slate-500">Molecular Graph</h3>
          <div className="flex gap-1 rounded-lg bg-slate-100 p-1">
            {[
              { id: 'attention', label: 'Attention', icon: SwatchIcon },
              { id: 'substructure', label: 'Substructure', icon: Squares2X2Icon },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setToggle(t.id)}
                className={clsx(
                  'flex items-center gap-1 rounded-md px-2 py-1 text-xs font-semibold',
                  toggle === t.id ? 'bg-white text-indigo-600 shadow' : 'text-slate-500'
                )}
              >
                <t.icon className="h-4 w-4" />
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {toggle === 'attention' ? (
          <StructureHeatmap smiles={smiles} />
        ) : (
          <div className="flex min-h-[260px] items-center justify-center rounded-xl bg-slate-50 p-4">
            <span className="font-mono text-sm text-slate-400">{smiles}</span>
          </div>
        )}

        <div className="mt-3 flex items-center justify-between text-[11px] text-slate-400">
          <span>
            Attribution source:{' '}
            <span className="font-semibold text-slate-600">
              {attnSource === 'gnn_attention' ? 'GNN attention (real)' : attnSource || 'n/a'}
            </span>
          </span>
        </div>

        {toggle === 'substructure' && topSub && (
          <div className="mt-3 rounded-xl bg-indigo-50 p-3 text-sm text-indigo-800">
            Primary flagged substructure: <b>{topSub.name}</b> · attention{' '}
            {(topSub.avg_attention * 100).toFixed(0)}% · {topSub.category}
          </div>
        )}
      </div>

      {/* Attention / substructure list */}
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="mb-3 text-sm font-bold uppercase tracking-wide text-slate-500">
          Risk-Associated Regions
        </h3>
        {substructures.length === 0 ? (
          <p className="text-sm text-slate-400">No high-attention substructures detected.</p>
        ) : (
          <ul className="space-y-2">
            {substructures.map((s, i) => (
              <li key={i} className="rounded-lg border border-slate-100 bg-slate-50 px-3 py-2">
                <div className="flex items-center justify-between text-sm font-semibold text-slate-700">
                  <span>{s.name}</span>
                  <span className="text-indigo-600">{(s.avg_attention * 100).toFixed(0)}%</span>
                </div>
                <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-slate-200">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-indigo-400 to-indigo-600"
                    style={{ width: `${Math.min(100, s.avg_attention * 100)}%` }}
                  />
                </div>
                <p className="mt-1 text-xs text-slate-500">{s.category}</p>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
};

export default MolecularExplorer;
