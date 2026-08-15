import React from 'react';

// Placeholder landing page for the legacy DrugTox-AI shell.
// The active SIH deliverable lives at /app/pharmaguard (PharmaGuard AI Workbench).
const Home = () => (
  <div className="mx-auto max-w-3xl px-6 py-16 text-center">
    <h1 className="text-3xl font-extrabold text-slate-800">DrugTox-AI Platform</h1>
    <p className="mt-3 text-slate-500">
      The trustworthy drug-safety decision-support experience is now <b>PharmaGuard AI</b>.
    </p>
    <a
      href="/app/pharmaguard"
      className="mt-6 inline-block rounded-xl bg-indigo-600 px-5 py-3 text-sm font-bold text-white shadow hover:bg-indigo-700"
    >
      Open PharmaGuard AI Workbench →
    </a>
  </div>
);

export default Home;
