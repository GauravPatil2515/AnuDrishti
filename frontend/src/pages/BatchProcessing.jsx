import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRightIcon, BeakerIcon, SparklesIcon } from '@heroicons/react/24/outline'

const BatchProcessing = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-black text-white font-sans flex items-center justify-center">
      <div className="rounded-lg border border-white/5 bg-white/3 p-8 backdrop-blur text-center max-w-xl">
        <h2 className="text-xl font-bold text-white mb-4">Batch Processing</h2>
        <p className="text-white/50 mb-6">
          Screen libraries of molecules for toxicity and ADMET properties. Upload CSV/SMI files or paste SMILES strings (up to 1000 molecules) for high-throughput analysis.
        </p>
        <div className="space-y-4">
          <div className="flex items-center gap-3 p-3 rounded-lg border border-white/5 bg-white/2 hover:bg-white/3 transition-colors">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600/10 text-indigo-400">
              <BeakerIcon className="h-4 w-4" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-white">Single Molecule Mode</h3>
              <p className="mt-1 text-xs text-white/50">
                Analyze one molecule at a time with full explanation verification.
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 p-3 rounded-lg border border-white/5 bg-white/2 hover:bg-white/3 transition-colors">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-indigo-600/10 text-indigo-400">
              <SparklesIcon className="h-4 w-4" />
            </div>
            <div className="flex-1">
              <h3 className="text-sm font-medium text-white">Batch Processing Mode</h3>
              <p className="mt-1 text-xs text-white/50">
                Upload libraries or paste lists for automated screening with summary statistics.
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 p-3 rounded-lg border border-white/5 bg-white/2 hover:bg-white/3 transition-colors">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-emerald-600/10 text-emerald-400">
              <ArrowRightIcon className="h-4 w-4" />
            </div>
            <div class="flex-1">
              <h3 className="text-sm font-medium text-white">What-If Optimization</h3>
              <p className="mt-1 text-xs text-white/50">
                Generate molecular edits to improve safety profiles while maintaining efficacy.
              </p>
            </div>
          </div>
        </div>
        
        <div className="mt-6">
          <button
            onClick={() => navigate('/app/pharmaguard')}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            <span>Go to PharmaGuard Workbench</span>
            <ArrowRightIcon className="h-4 w-4" />
          </button>
        </div>
        
        <p className="mt-4 text-xs text-white/40">
          Batch processing is available as Mode B in the PharmaGuard AI Workbench.
        </p>
      </div>
    </div>
  );
};

export default BatchProcessing;