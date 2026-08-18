import React, { useState, useCallback } from 'react';
import LibraryScreening from '../components/LibraryScreening';
import { useAnalysis } from '../App';
import { BeakerIcon, ArrowDownTrayIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

export default function BatchScreening() {
  const [batchResults, setBatchResults] = useState(null);
  const { addAnalysis } = useAnalysis();

  const handleBatchComplete = useCallback((results) => {
    setBatchResults(results);
  }, []);

  const exportResults = () => {
    if (!batchResults) return;
    const csvContent = "data:text/csv;charset=utf-8," + batchResults.map(r => 
      `${r.smiles},${r.toxicity_score},${r.triage},${r.timestamp || ''}`
    ).join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "batch_screening_results.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    toast.success("Results exported as CSV");
  };

  const handleAnalyzeMolecule = (smiles) => {
    if (batchResults) {
      const result = batchResults.find(r => r.smiles === smiles);
      if (result) {
        addAnalysis(result);
        window.location.href = '/app/safety';
      }
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold font-display text-text-primary flex items-center gap-2">
            <BeakerIcon className="h-6 w-6 text-accent-green" />
            Batch Screening
          </h1>
          <p className="text-sm text-text-muted mt-1">Async library processing with progress tracking</p>
        </div>
        {batchResults && (
          <button
            onClick={exportResults}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface border border-border rounded-lg transition-colors"
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            Export CSV
          </button>
        )}
      </div>

      <LibraryScreening 
        onBatchComplete={handleBatchComplete}
        onAnalyzeMolecule={handleAnalyzeMolecule}
      />
    </div>
  );
}
