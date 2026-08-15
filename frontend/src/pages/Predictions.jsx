import React from 'react';
import { Link } from 'react-router-dom';

// Placeholder page — redirect intent to the PharmaGuard AI Workbench.
const Predictions = () => (
  <div className="mx-auto max-w-3xl px-6 py-16 text-center">
    <h1 className="text-2xl font-bold text-slate-800">Predictions</h1>
    <p className="mt-3 text-slate-500">
      Single-molecule analysis now lives in the{' '}
      <Link to="/app/pharmaguard" className="font-semibold text-indigo-600">
        PharmaGuard AI Workbench
      </Link>
      .
    </p>
  </div>
);

export default Predictions;
