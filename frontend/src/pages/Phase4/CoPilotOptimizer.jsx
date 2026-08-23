import React, { useState } from 'react';
import {
  BeakerIcon,
  PlayIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowRightIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';
import api from '../../api';
import toast, { Toaster } from 'react-hot-toast';

const CoPilotOptimizer = () => {
  const [smiles, setSmiles] = useState('');
  const [isOptimizing, setIsOptimizing] = useState(false);
  const [optimizationResult, setOptimizationResult] = useState(null);
  const [iterationHistory, setIterationHistory] = useState([]);

  const runOptimization = async () => {
    if (!smiles.trim()) {
      toast.error('Please enter a SMILES string');
      return;
    }

    setIsOptimizing(true);
    setOptimizationResult(null);
    setIterationHistory([]);

    try {
      const response = await api.post('/api/copilot/optimize-loop', {
        smiles: smiles.trim(),
      });

      const result = response.data;
      setOptimizationResult(result);
      setIterationHistory(result.iteration_history || []);

      if (result.verdict === 'VERIFIED') {
        toast.success(`Co-pilot found a VERIFIED candidate in ${result.iterations_run} iteration(s)!`);
      } else {
        toast('All 3 iterations completed - escalated to HUMAN_REVIEW', { icon: '⚠️' });
      }
    } catch (error) {
      const msg = error.response?.data?.error || error.message;
      toast.error(`Optimization failed: ${msg}`);
    } finally {
      setIsOptimizing(false);
    }
  };

  const getVerdictBadge = (verdict) => {
    switch (verdict) {
      case 'VERIFIED':
        return <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-semibold">VERIFIED</span>;
      case 'RETRY':
        return <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded-full text-xs font-semibold">RETRY</span>;
      case 'HUMAN_REVIEW':
        return <span className="px-2 py-1 bg-red-100 text-red-800 rounded-full text-xs font-semibold">HUMAN_REVIEW</span>;
      default:
        return <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-semibold">{verdict}</span>;
    }
  };

  const renderPropertyDelta = (delta) => {
    const toxicityDelta = delta.toxicity_delta;
    const qedDelta = delta.qed_delta;
    const isToxicDown = toxicityDelta < 0;
    const isQedUp = qedDelta > 0;

    return (
      <div className="flex gap-4 text-sm">
        <span className={`font-medium ${isToxicDown ? 'text-green-600' : 'text-red-600'}`}>
          Toxicity: {isToxicDown ? '↓' : '↑'} {Math.abs(toxicityDelta)}
        </span>
        <span className={`font-medium ${isQedUp ? 'text-green-600' : 'text-red-600'}`}>
          QED: {isQedUp ? '↑' : '↓'} {Math.abs(qedDelta)}
        </span>
      </div>
    );
  };

  const renderIteration = (iter) => (
    <div
      key={iter.iteration}
      className={`border rounded-lg p-4 mb-3 ${
        iter.verdict === 'VERIFIED'
          ? 'border-green-200 bg-green-50'
          : 'border-gray-200 bg-gray-50'
      }`}
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <span className="font-semibold text-sm text-gray-700">
            Iteration {iter.iteration}
          </span>
          {getVerdictBadge(iter.verdict)}
        </div>
        <span className="text-xs text-gray-500">{iter.efs_score}</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
        <div>
          <span className="text-xs text-gray-500">Input SMILES:</span>
          <code className="text-xs bg-gray-100 px-2 py-1 rounded block mt-1 break-all">
            {iter.input_smiles}
          </code>
        </div>
        <div>
          <span className="text-xs text-gray-500">Candidate SMILES:</span>
          <code className="text-xs bg-blue-50 px-2 py-1 rounded block mt-1 break-all">
            {iter.candidate_smiles}
          </code>
        </div>
      </div>

      {iter.property_delta && (
        <div className="mt-2">
          {renderPropertyDelta(iter.property_delta)}
        </div>
      )}

      <div className="mt-2 text-xs text-gray-600">
        <span className="font-medium">Notes:</span> {iter.mechanistic_notes}
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <Toaster position="top-right" />

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <SparklesIcon className="h-6 w-6 text-blue-600" />
          Neuro-Symbolic Co-Pilot Optimizer
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          3-iteration closed-loop bioisosteric optimization. When EFS {'<'} 0.70, the co-pilot identifies toxicophores, proposes replacements, and re-scores candidates until verified or escalated.
        </p>
      </div>

      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <div className="flex gap-2">
          <input
            type="text"
            value={smiles}
            onChange={(e) => setSmiles(e.target.value)}
            placeholder="Enter molecule SMILES (e.g., c1ccc([N+](=O)[O-])cc1)"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => e.key === 'Enter' && runOptimization()}
            disabled={isOptimizing}
          />
          <button
            onClick={runOptimization}
            disabled={isOptimizing || !smiles.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isOptimizing ? (
              <RefreshCwIcon className="h-4 w-4 animate-spin" />
            ) : (
              <PlayIcon className="h-4 w-4" />
            )}
            {isOptimizing ? 'Optimizing...' : 'Optimize'}
          </button>
        </div>

        <div className="mt-3 text-xs text-gray-500">
          <InformationCircleIcon className="h-4 w-4 inline mr-1" />
          EFS threshold: 0.70 | Max iterations: 3 | Deterministic fallback when no LLM key
        </div>
      </div>

      {optimizationResult && (
        <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold text-gray-800">
              Optimization Result
            </h2>
            {getVerdictBadge(optimizationResult.verdict)}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center mb-4">
            <div>
              <span className="text-2xl font-bold text-gray-800">
                {optimizationResult.iterations_run}
              </span>
              <p className="text-xs text-gray-500">Iterations Run</p>
            </div>
            <div>
              <span className="text-2xl font-bold text-blue-600">
                {optimizationResult.accepted_candidate_efs !== null
                  ? optimizationResult.accepted_candidate_efs.toFixed(3)
                  : 'N/A'}
              </span>
              <p className="text-xs text-gray-500">Accepted EFS</p>
            </div>
            <div>
              <span className="text-2xl font-bold text-purple-600">
                {optimizationResult.baseline_toxicity?.toFixed(3) || 'N/A'}
              </span>
              <p className="text-xs text-gray-500">Baseline Toxicity</p>
            </div>
            <div>
              <span className="text-2xl font-bold text-green-600">
                {optimizationResult.baseline_qed?.toFixed(3) || 'N/A'}
              </span>
              <p className="text-xs text-gray-500">Baseline QED</p>
            </div>
          </div>

          {optimizationResult.accepted_candidate && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 mb-4">
              <div className="flex items-center gap-2 mb-1">
                <CheckCircleIcon className="h-5 w-5 text-green-600" />
                <span className="font-semibold text-green-800">VERIFIED Candidate</span>
              </div>
              <code className="text-sm bg-white px-2 py-1 rounded block break-all">
                {optimizationResult.accepted_candidate}
              </code>
              {optimizationResult.accepted_property_delta && (
                <div className="mt-2">
                  {renderPropertyDelta(optimizationResult.accepted_property_delta)}
                </div>
              )}
            </div>
          )}

          {optimizationResult.input_smiles && (
            <div className="mt-3">
              <span className="text-xs text-gray-500">Original:</span>
              <code className="text-xs bg-gray-100 px-2 py-1 rounded">
                {optimizationResult.input_smiles}
              </code>
            </div>
          )}
        </div>
      )}

      {iterationHistory.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-lg p-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <BeakerIcon className="h-5 w-5 text-blue-600" />
            Iteration History
          </h2>
          {iterationHistory.map((iter) => renderIteration(iter))}
        </div>
      )}

      {!isOptimizing && !optimizationResult && (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500">
            Enter a SMILES string to start the neuro-symbolic optimization loop.
          </p>
          <p className="text-xs text-gray-400 mt-2">
            Molecules with toxicophores (nitro, basic amines, carboxylic acids)
            will trigger the 3-iteration bioisosteric replacement loop.
          </p>
        </div>
      )}
    </div>
  );
};

export default CoPilotOptimizer;
