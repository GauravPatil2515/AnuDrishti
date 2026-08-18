import React, { useState, useEffect, useCallback } from 'react';
import { clsx } from 'clsx';
import api from '../api';
import ErrorBoundary from './ErrorBoundary';
import Skeleton from './Skeleton';
import SafetyDashboardInner from './SafetyDashboard';
import {
  ExclamationTriangleIcon,
  ArrowPathIcon,
  InformationCircleIcon,
  BeakerIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon as ExclTri,
  ShieldExclamationIcon,
} from '@heroicons/react/24/outline';

/**
 * SafetyDashboardWrapper - Handles loading, error, and async states
 * Provides skeleton loaders while fetching data
 */
const SafetyDashboardWrapper = ({ smiles, onError }) => {
  const [analysis, setAnalysis] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchAnalysis = useCallback(async () => {
    if (!smiles) {
      setAnalysis(null);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await api.post('/api/analyze/single', {
        smiles,
        include_explanation: true,
      });

      if (response.data?.success && response.data.analysis) {
        setAnalysis(response.data.analysis);
      } else {
        throw new Error(response.data?.error || 'Analysis failed');
      }
    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || 'Failed to fetch analysis';
      setError(errorMsg);
      if (onError) onError(err);
    } finally {
      setIsLoading(false);
    }
  }, [smiles, onError]);

  useEffect(() => {
    fetchAnalysis();
  }, [fetchAnalysis]);

  // Render skeleton while loading
  if (isLoading) {
    return <Skeleton.Dashboard className="space-y-6" />;
  }

  // Render error state
  if (error) {
    return (
      <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-6">
        <div className="flex items-center gap-3 mb-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10 text-red-500">
            <ExclamationTriangleIcon className="h-5 w-5" />
          </div>
          <div>
            <h3 className="font-semibold text-red-600">Analysis Failed</h3>
            <p className="text-sm text-secondary mt-1">{error}</p>
          </div>
        </div>
        <div className="flex gap-3">
          <button
            onClick={fetchAnalysis}
            className="btn btn-primary flex items-center gap-2"
          >
            <ArrowPathIcon className="h-4 w-4" />
            Retry Analysis
          </button>
        </div>
      </div>
    );
  }

  // Render actual dashboard
  if (!smiles) {
    return (
      <div className="rounded-xl border border-border bg-surface p-8 text-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-surface-hover mx-auto mb-4">
          <BeakerIcon className="h-8 w-8 text-muted" />
        </div>
        <h3 className="text-lg font-semibold text-primary mb-2">Enter a Molecule</h3>
        <p className="text-secondary max-w-md mx-auto">
          Enter a SMILES string or drug name in the input panel to begin toxicity analysis.
        </p>
      </div>
    );
  }

  return <SafetyDashboardInner analysis={analysis} />;
};

/**
 * Error boundary for the SafetyDashboard
 */
const SafetyDashboardErrorBoundary = ({ error, resetErrorBoundary }) => (
  <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-6">
    <div className="flex items-center gap-3 mb-3">
      <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-red-500/10 text-red-500">
        <ExclamationTriangleIcon className="h-5 w-5" />
      </div>
      <div>
        <h3 className="font-semibold text-red-600">Dashboard Error</h3>
        <p className="text-sm text-secondary mt-1">Failed to render safety dashboard</p>
      </div>
    </div>
    <button
      onClick={() => window.location.reload()}
      className="btn btn-primary flex items-center gap-2"
    >
      <InformationCircleIcon className="h-4 w-4" />
      Reload Page
    </button>
  </div>
);

/**
 * Main exported component with error boundary
 */
export const SafetyDashboard = ({ smiles, onError }) => (
  <ErrorBoundary
    fallback={SafetyDashboardErrorBoundary}
    onError={(error) => console.error('SafetyDashboard error:', error)}
  >
    <SafetyDashboardWrapper smiles={smiles} onError={onError} />
  </ErrorBoundary>
);

export default SafetyDashboard;