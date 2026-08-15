import React from 'react';
import { Link } from 'react-router-dom';

// Placeholder page — the active experience is the PharmaGuard AI Workbench.
const EnhancedPredictions = () => (
  <div className="mx-auto max-w-3xl px-6 py-16 text-center">
    <h1 className="text-2xl font-bold text-slate-800">Enhanced Predictions</h1>
    <p className="mt-3 text-slate-500">
      Run the full pipeline (prediction → attribution → OOD → triage → faithfulness) in the{' '}
      <Link to="/app/pharmaguard" className="font-semibold text-indigo-600">
        PharmaGuard AI Workbench
      </Link>
      .
    </p>
  </div>
);

export default EnhancedPredictions;
