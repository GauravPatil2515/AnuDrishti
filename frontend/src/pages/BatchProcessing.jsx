import React from 'react';
import { Link } from 'react-router-dom';

// Placeholder page — library screening (Mode B) is implemented in the
// PharmaGuard AI Workbench.
const BatchProcessing = () => (
  <div className="mx-auto max-w-3xl px-6 py-16 text-center">
    <h1 className="text-2xl font-bold text-slate-800">Batch Processing</h1>
    <p className="mt-3 text-slate-500">
      Library screening is available in the{' '}
      <Link to="/app/pharmaguard" className="font-semibold text-indigo-600">
        PharmaGuard AI Workbench
      </Link>
      .
    </p>
  </div>
);

export default BatchProcessing;
