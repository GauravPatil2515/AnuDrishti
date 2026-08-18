import React, { useState } from 'react';
import SafetyDashboardWrapper from '../components/SafetyDashboardWrapper';
import { useAnalysis } from '../App';
import { Link } from 'react-router-dom';
import { BeakerIcon, ShieldCheckIcon } from '@heroicons/react/24/outline';
import api from '../api';
import { toast } from 'react-hot-toast';

export default function SafetyDashboard() {
  const { lastAnalysis, addAnalysis } = useAnalysis();
  const [loading, setLoading] = useState(false);

  const loadSample = async (smiles, name) => {
    setLoading(true);
    try {
      const res = await api.post('/api/analyze/single', { smiles, include_explanation: true });
      addAnalysis(res.data.analysis);
      toast.success(`Loaded ${name} safety profile`);
    } catch (e) {
      toast.error('Failed to load sample molecule');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-xs text-text-muted">
        <Link to="/app/analyze" className="hover:text-text-primary">Analyze</Link>
        <Link to="/app/explorer" className="hover:text-text-primary">Explorer</Link>
        <span>/</span>
        <span className="text-text-primary font-semibold">Safety & ADMET</span>
      </nav>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-display text-text-primary">Safety & ADMET</h1>
          <p className="text-sm text-text-muted mt-1">16-endpoint toxicity radar, uncertainty bands & Lipinski compliance</p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs text-text-muted hidden sm:inline">Load Sample:</span>
          <button
            onClick={() => loadSample('CC(=O)Oc1ccccc1C(=O)O', 'Aspirin')}
            disabled={loading}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-surface border border-border hover:bg-surface-hover text-text-secondary transition-colors"
          >
            Aspirin
          </button>
          <button
            onClick={() => loadSample('c1ccc([N+](=O)[O-])cc1', 'Nitrobenzene')}
            disabled={loading}
            className="px-2.5 py-1 text-xs font-medium rounded-lg bg-surface border border-border hover:bg-surface-hover text-text-secondary transition-colors"
          >
            Nitrobenzene
          </button>
        </div>
      </div>

      {!lastAnalysis ? (
        <div className="surface p-12 text-center flex flex-col items-center justify-center my-4">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-surface-elevated border border-border mb-4 shadow-sm">
            <ShieldCheckIcon className="h-8 w-8 text-accent-green" />
          </div>
          <h3 className="text-base font-bold text-text-primary font-display">No Active Safety Profile</h3>
          <p className="text-xs text-text-muted mt-1 max-w-md mb-4">
            Select a sample compound above to inspect 16 toxicity endpoints, or analyze a new SMILES in the Workbench.
          </p>
          <button
            onClick={() => loadSample('CC(=O)Oc1ccccc1C(=O)O', 'Aspirin')}
            disabled={loading}
            className="btn btn-primary text-xs"
          >
            {loading ? 'Loading Aspirin...' : 'View Aspirin Safety Panel'}
          </button>
        </div>
      ) : (
        <>
          <SafetyDashboardWrapper 
            smiles={lastAnalysis.smiles}
            analysis={lastAnalysis}
          />

          {/* Next button */}
          <div className="flex justify-between pt-4">
            <Link 
              to="/app/explorer"
              className="px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface border border-border rounded-lg transition-colors"
            >
              ← Explorer
            </Link>
            <Link 
              to="/app/audit"
              className="px-4 py-2 text-sm font-medium text-accent-green hover:bg-accent-green/10 border border-accent-green/30 rounded-lg transition-colors"
            >
              Next: Explanation Audit →
            </Link>
          </div>
        </>
      )}
    </div>
  );
}
