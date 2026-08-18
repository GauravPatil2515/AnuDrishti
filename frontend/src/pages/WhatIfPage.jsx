import React, { useEffect } from 'react';
import WhatIfOptimizer from '../components/WhatIfOptimizer';
import { useAnalysis } from '../App';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRightIcon } from '@heroicons/react/24/outline';

export default function WhatIfPage() {
  const { lastAnalysis, addAnalysis } = useAnalysis();
  const navigate = useNavigate();

  const handleAnalyzeVariant = (counterfactual) => {
    // Push counterfactual to AnalysisContext and navigate to safety page
    const newAnalysis = {
      smiles: counterfactual.smiles,
      predictions: counterfactual.predictions,
      triage: counterfactual.triage || 'YELLOW',
      explanation: counterfactual.explanation || lastAnalysis?.explanation,
      source: 'whatif',
    };
    addAnalysis(newAnalysis);
    navigate('/app/safety');
  };

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-xs text-text-muted">
        <Link to="/app/analyze" className="hover:text-text-primary">Analyze</Link>
        <span>/</span>
        <span className="text-text-primary font-semibold">What-If Optimizer</span>
      </nav>

      <div>
        <h1 className="text-2xl font-bold font-display text-text-primary">What-If Optimizer</h1>
        <p className="text-sm text-text-muted mt-1">Counterfactual molecule design</p>
      </div>

      <WhatIfOptimizer 
        initialSmiles={lastAnalysis?.smiles || ''}
        onAnalyzeVariant={handleAnalyzeVariant}
      />
    </div>
  );
}
