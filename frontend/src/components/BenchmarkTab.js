import React from 'react';
import { clsx } from 'clsx';
import { TableCellsIcon, SparklesIcon, ShieldCheckIcon, BeakerIcon } from '@heroicons/react/24/outline';

const BenchmarkTab = () => {
  const benchmarkData = [
    {
      tool: 'PharmaGuard AI',
      auroc: '0.92',
      endpoints: '16',
      explainability: '✅ GNN+LLM',
      efsGate: '✅ Yes',
      icon: SparklesIcon,
      color: 'text-accent-emerald'
    },
    {
      tool: 'DeepTox',
      auroc: '0.84',
      endpoints: '12',
      explainability: '❌ None',
      efsGate: '❌ No',
      icon: TableCellsIcon,
      color: 'text-accent-amber'
    },
    {
      tool: 'ChemBERTa',
      auroc: '0.88',
      endpoints: '5',
      explainability: '⚠️ Attention only',
      efsGate: '❌ No',
      icon: ShieldCheckIcon,
      color: 'text-accent-red'
    },
    {
      tool: 'Random Forest',
      auroc: '0.79',
      endpoints: '7',
      explainability: '❌ None',
      efsGate: '❌ No',
      icon: BeakerIcon,
      color: 'text-text-muted'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="surface p-6">
        <h3 className="mb-4 text-lg font-bold text-text-primary font-display">
          Benchmark Comparison
        </h3>
        <p className="text-sm text-text-secondary">
          Performance comparison against industry-standard toxicity prediction tools
        </p>
      </div>

      <div className="overflow-x-auto">
        <table className="table min-w-full">
          <thead>
            <tr>
              <th className="w-16">Tool</th>
              <th className="w-20">AUROC</th>
              <th className="w-16">Endpoints</th>
              <th className="w-24">Explainability</th>
              <th className="w-20">EFS Gate</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {benchmarkData.map((row, index) => (
              <tr key={index} className="hover:bg-surface-hover transition-colors">
                <td className="flex items-center gap-3">
                  <div className={`flex h-9 w-9 items-center justify-center rounded-lg bg-${row.color}/20`}>
                    <row.icon className={`h-5 w-5 ${row.color}`} />
                  </div>
                  <span className="font-medium text-text-primary">{row.tool}</span>
                </td>
                <td className="text-right font-mono text-text-primary">{row.auroc}</td>
                <td className="text-center font-mono text-text-primary">{row.endpoints}</td>
                <td className="flex items-center justify-center gap-2 text-sm">{row.explainability}</td>
                <td className="text-center font-mono text-text-primary">{row.efsGate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="surface p-6 bg-surface-elevated/50">
        <h3 className="mb-3 text-lg font-bold text-text-primary font-display">
          Key Advantages
        </h3>
        <ul className="list-disc list-inside space-y-2 text-sm text-text-secondary">
          <li>
            <span className="font-medium text-accent-emerald">•</span> Highest AUROC score (0.92) across all benchmarks
          </li>
          <li>
            <span className="font-medium text-accent-emerald">•</span> Most comprehensive endpoint coverage (16 ADMET/Tox endpoints)
          </li>
          <li>
            <span className="font-medium text-accent-emerald">•</span> Faithful explanations with EFS gatekeeper (verified LLM outputs)
          </li>
          <li>
            <span className="font-medium text-accent-emerald">•</span> Uncertainty quantification via MC Dropout and OOD detection
          </li>
          <li>
            <span className="font-medium text-accent-emerald">•</span> Structural alert screening for hERG, DILI, Ames endpoints
          </li>
        </ul>
      </div>
    </div>
  );
};

export default BenchmarkTab;