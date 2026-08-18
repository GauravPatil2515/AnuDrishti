import React, { useState, useCallback, useEffect, useRef } from 'react';
import LibraryScreening from '../components/LibraryScreening';
import { useAnalysis } from '../App';
import { BeakerIcon, ArrowDownTrayIcon, ArrowRightIcon, Cog6ToothIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import api from '../api';

const EXAMPLE = `CC(=O)Oc1ccccc1C(=O)O
c1ccccc1
O=[N+]([O-])c1ccccc1
CN1C=NC2=C1C(=O)N(C(=O)N2C)C`;

export default function BatchScreening() {
  const [smilesList, setSmilesList] = useState(EXAMPLE);
  const [batchResult, setBatchResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [polling, setPolling] = useState(false);
  const [progress, setProgress] = useState(null);
  const [taskId, setTaskId] = useState(null);
  const pollIntervalRef = useRef(null);
  const { addAnalysis } = useAnalysis();

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const startPolling = useCallback((taskId) => {
    setPolling(true);
    setTaskId(taskId);
    
    const poll = async () => {
      try {
        const res = await api.get(`/api/analyze/batch-progress/${taskId}`);
        const data = res.data;
        setProgress(data);
        
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(pollIntervalRef.current);
          setPolling(false);
          
          if (data.status === 'completed') {
            // Fetch full results
            const resultRes = await api.get(`/api/analyze/batch-result/${taskId}`);
            setBatchResult(resultRes.data);
            toast.success(`Screened ${resultRes.data.total_processed} molecules`);
          } else {
            toast.error('Batch processing failed');
          }
        }
      } catch (e) {
        console.error('Progress poll failed:', e);
        // Continue polling on transient errors
      }
    };
    
    // Initial poll
    poll();
    
    // Poll every 2 seconds
    pollIntervalRef.current = setInterval(poll, 2000);
  }, []);

  const runScreening = useCallback(async () => {
    const list = smilesList
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean);
    if (list.length === 0) {
      toast.error('Enter at least one SMILES');
      return;
    }
    setLoading(true);
    setBatchResult(null);
    setProgress(null);
    setTaskId(null);
    try {
      const res = await api.post('/api/analyze/batch', {
        smiles_list: list,
        include_explanation: false,
      });
      
      if (res.data.async && res.data.task_id) {
        // Async mode - start polling
        toast.success(`Batch queued (${res.data.total_submitted} molecules)`);
        startPolling(res.data.task_id);
      } else {
        // Sync mode - results returned immediately
        setBatchResult(res.data);
        toast.success(`Screened ${res.data.total_processed} molecules`);
      }
    } catch (e) {
      toast.error(e.response?.data?.error || 'Batch screening failed');
    } finally {
      setLoading(false);
    }
  }, [smilesList, startPolling]);

  const exportResults = () => {
    if (!batchResult) return;
    const rows = batchResult.results || [];
    const csv = [
      'smiles,toxicity_score,triage,label',
      ...rows.map(
        (r) =>
          `${r.smiles},${r.toxicity_probability ?? ''},${(r.triage || {}).category ?? ''},${r.label ?? ''}`
      ),
    ].join('\n');
    const link = document.createElement('a');
    link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    link.download = 'batch_screening_results.csv';
    link.click();
    toast.success('Results exported as CSV');
  };

  const handleAnalyzeMolecule = (row) => {
    const newAnalysis = {
      smiles: row.smiles,
      predictions: row.predictions,
      triage: row.triage,
      toxicity_probability: row.toxicity_score,
      source: 'batch',
    };
    addAnalysis(newAnalysis);
    window.location.href = '/app/safety';
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-2xl font-bold font-display text-text-primary flex items-center gap-2">
            <BeakerIcon className="h-6 w-6 text-accent-green" />
            Batch Screening
          </h1>
          <p className="text-sm text-text-muted mt-1">Async library processing with progress tracking</p>
        </div>
        {batchResult && (
          <button
            onClick={exportResults}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface border border-border rounded-lg transition-colors"
          >
            <ArrowDownTrayIcon className="h-4 w-4" />
            Export CSV
          </button>
        )}
      </div>

      <div className="surface rounded-xl border border-border p-4 space-y-3">
        <label className="block text-xs font-semibold uppercase tracking-wider text-text-muted">
          SMILES Library (one per line)
        </label>
        <textarea
          value={smilesList}
          onChange={(e) => setSmilesList(e.target.value)}
          rows={6}
          className="w-full rounded-lg bg-surface border border-border px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:border-accent-green"
          placeholder="CC(=O)Oc1ccccc1C(=O)O&#10;c1ccccc1"
        />
        <button
          onClick={runScreening}
          disabled={loading || polling}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-accent-green text-canvas rounded-lg hover:opacity-90 disabled:opacity-50 transition-colors"
        >
          <BeakerIcon className="h-4 w-4" />
          {loading ? 'Screening…' : polling ? 'Processing…' : 'Screen Library'}
        </button>
      </div>

      {/* Progress indicator for async jobs */}
      {polling && progress && (
        <div className="surface rounded-xl border border-border p-4 space-y-2 animate-pulse">
          <div className="flex items-center justify-between text-xs">
            <span className="font-semibold">Processing batch…</span>
            <span className="flex items-center gap-1 text-accent-green">
              <Cog6ToothIcon className="h-3 w-3 animate-spin" />
              {progress.completed || 0} / {progress.total || 0}
            </span>
          </div>
          <div className="w-full bg-surface-elevated rounded-full h-2">
            <div
              className="h-2 rounded-full bg-accent-green transition-all duration-500"
              style={{ width: `${progress.total > 0 ? (progress.completed / progress.total) * 100 : 0}%` }}
            />
          </div>
          <p className="text-[10px] text-text-muted">
            {progress.status === 'completed' ? 'Completed!' : 
             progress.status === 'failed' ? 'Failed' : 
             `Processing molecule ${progress.current_index || 0} of ${progress.total || 0}...`}
          </p>
        </div>
      )}

      {batchResult && <LibraryScreening batchResult={batchResult} />}

      {batchResult && (
        <div className="space-y-2">
          {(batchResult.results || []).map((r, i) => (
            <div
              key={i}
              className="flex items-center justify-between surface-elevated rounded-lg border border-border px-3 py-2"
            >
              <div className="min-w-0">
                <code className="text-[11px] text-text-primary break-all">{r.smiles}</code>
                <p className="text-[10px] text-text-muted">
                  {(r.triage || {}).category} · {((r.toxicity_probability ?? 0) * 100).toFixed(0)}% risk
                </p>
              </div>
              <button
                onClick={() => handleAnalyzeMolecule(r)}
                className="flex items-center gap-1 text-xs font-medium text-accent-green hover:bg-accent-green/10 border border-accent-green/30 rounded-lg px-2.5 py-1.5 transition-colors shrink-0"
              >
                Open <ArrowRightIcon className="h-3 w-3" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
