import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRightIcon } from '@heroicons/react/24/outline';

const Predictions = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-black text-white font-sans flex items-center justify-center">
      <div className="rounded-lg border border-white/5 bg-white/3 p-8 backdrop-blur text-center max-w-xl">
        <h2 className="text-xl font-bold text-white mb-4">Molecular Predictions</h2>
        <p className="text-white/50 mb-6">
          Run single-molecule analysis with full explanation verification in the
          <span className="text-indigo-400 font-medium">PharmaGuard AI Workbench</span>.
        </p>
        <div className="flex items-center justify-center">
          <button
            onClick={() => navigate('/app/pharmaguard')}
            className="inline-flex items-center gap-2 rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-500 transition-colors"
          >
            <span>Open Workbench</span>
            <ArrowRightIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Predictions;