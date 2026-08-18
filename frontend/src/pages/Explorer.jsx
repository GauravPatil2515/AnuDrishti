import React, { useState } from 'react';
import MolecularExplorer from '../components/MolecularExplorer';
import { useAnalysis } from '../App';
import { Link } from 'react-router-dom';
import { BeakerIcon } from '@heroicons/react/24/outline';
import api from '../api';
import { toast } from 'react-hot-toast';

export default function Explorer() {
  const { lastAnalysis, addAnalysis } = useAnalysis();
  const [loading, setLoading] = useState(false);

  const loadSample = async (smiles, name) => {
    setLoading(true);
    try {
      const res = await api.post('/api/analyze/single', { smiles, include_explanation: true });
      addAnalysis(res.data.analysis);
      toast.success(`Loaded ${name} analysis`);
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
        <span>/</span>
        <span className="text-text-primary font-semibold">Explorer</span>
      </nav>
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold font-display text-text-primary">Molecular Explorer</h1>
          <p className="text-sm text-text-muted mt-1">Atom-level GNN attention visualization & structural risk regions</p>
        </div>

        {/* Preset Loaders if needed */}
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
            <BeakerIcon className="h-8 w-8 text-accent-green" />
          </div>
          <h3 className="text-base font-bold text-text-primary font-display">No Active Molecule Selected</h3>
          <p className="text-xs text-text-muted mt-1 max-w-md mb-4">
            Select a sample compound above or analyze a new molecule in the Workbench to view atom-level attention maps.
          </p>
          <button
            onClick={() => loadSample('CC(=O)Oc1ccccc1C(=O)O', 'Aspirin')}
            disabled={loading}
            className="btn btn-primary text-xs"
          >
            {loading ? 'Loading Aspirin...' : 'Explore Aspirin Example'}
          </button>
        </div>
      ) : (
        <MolecularExplorer 
          smiles={lastAnalysis.smiles} 
          analysis={lastAnalysis}
          showHighlights={true}
        />
      )}
    </div>
  );
}
