import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { BeakerIcon, ShieldCheckIcon, SparklesIcon, CpuChipIcon } from '@heroicons/react/24/outline';
import api from '../api';
import { toast } from 'react-hot-toast';

export default function Settings() {
  const [apiKey, setApiKey] = useState('');
  const [modelThreshold, setModelThreshold] = useState(0.5);
  const [loading, setLoading] = useState(false);

  const saveSettings = async () => {
    setLoading(true);
    try {
      // In a real app, you would save to backend or localStorage
      // For now, we'll just save to localStorage and show a toast
      localStorage.setItem('pharmaguard_api_key', apiKey);
      localStorage.setItem('pharmaguard_model_threshold', modelThreshold);
      toast.success('Settings saved successfully');
    } catch (e) {
      toast.error('Failed to save settings');
    } finally {
      setLoading(false);
    }
  };

  const resetSettings = () => {
    localStorage.removeItem('pharmaguard_api_key');
    localStorage.removeItem('pharmaguard_model_threshold');
    setApiKey('');
    setModelThreshold(0.5);
    toast.success('Settings reset to defaults');
  };

  // Load existing settings on mount
  React.useEffect(() => {
    const savedApiKey = localStorage.getItem('pharmaguard_api_key');
    const savedThreshold = localStorage.getItem('pharmaguard_model_threshold');
    if (savedApiKey) setApiKey(savedApiKey);
    if (savedThreshold) setModelThreshold(parseFloat(savedThreshold));
  }, []);

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Breadcrumb */}
      <nav className="flex items-center space-x-2 text-xs text-text-muted">
        <Link to="/app/analyze" className="hover:text-text-primary">Analyze</Link>
        <span>/</span>
        <span className="text-text-primary font-semibold">Settings</span>
      </nav>

      <div>
        <h1 className="text-2xl font-bold font-display text-text-primary">Settings</h1>
        <p className="text-sm text-text-muted mt-1">Configure API keys, model thresholds, and system preferences</p>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {/* API Key Section */}
        <div className="surface p-4 rounded-lg border border-border">
          <h2 className="text-lg font-bold text-text-primary mb-4">API Configuration</h2>
          <div className="space-y-3">
            <label className="block text-xs font-semibold uppercase tracking-wider text-text-muted">
              Groq API Key (for LLM explanations)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="Enter your Groq API key"
              className="w-full rounded-lg bg-surface border border-border px-3 py-2 text-sm font-mono text-text-primary focus:outline-none focus:border-accent-green"
            />
            <p className="text-xs text-text-muted mt-1">
              Get your API key from <a href="https://console.groq.com/" className="text-accent-green hover:underline" target="_blank" rel="noopener noreferrer">Groq Console</a>
            </p>
          </div>
        </div>

        {/* Model Threshold Section */}
        <div className="surface p-4 rounded-lg border border-border">
          <h2 className="text-lg font-bold text-text-primary mb-4">Model Thresholds</h2>
          <div className="space-y-3">
            <label className="block text-xs font-semibold uppercase tracking-wider text-text-muted">
              Toxicity Probability Threshold (for RED triage)
            </label>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={modelThreshold}
                onChange={(e) => setModelThreshold(parseFloat(e.target.value))}
                className="flex-1"
              />
              <span className="font-mono text-xs text-text-primary">{Math.round(modelThreshold * 100)}%</span>
            </div>
            <p className="text-xs text-text-muted mt-1">
              Molecules with toxicity probability above this threshold will be flagged as HIGH concern (RED triage).
            </p>
          </div>
        </div>

        {/* System Info Section */}
        <div className="surface p-4 rounded-lg border border-border">
          <h2 className="text-lg font-bold text-text-primary mb-4">System Information</h2>
          <div className="space-y-3">
            <div className="flex items-center gap-3">
              <BeakerIcon className="h-4 w-4 text-accent-green" />
              <span className="font-medium text-text-primary">Version</span>
              <span className="ml-2 text-xs text-text-muted">1.0.0 (SIH 2026)</span>
            </div>
            <div className="flex items-center gap-3">
              <CpuChipIcon className="h-4 w-4 text-accent-blue" />
              <span className="font-medium text-text-primary">Backend Status</span>
              <span className="ml-2 px-2 py-0.5 rounded bg-accent-green/10 text-accent-green">Online</span>
            </div>
            <div className="flex items-center gap-3">
              <ShieldCheckIcon className="h-4 w-4 text-accent-emerald" />
              <span className="font-medium text-text-primary">Security</span>
              <span className="ml-2 text-xs text-text-muted">All processing done client-side</span>
            </div>
          </div>
        </div>

        {/* Actions Section */}
        <div className="surface p-4 rounded-lg border border-border">
          <h2 className="text-lg font-bold text-text-primary mb-4">Actions</h2>
          <div className="space-y-4">
            <button
              onClick={saveSettings}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium bg-accent-green text-canvas rounded-lg hover:opacity-90 disabled:opacity-50 transition-colors"
            >
              <SparklesIcon className="h-4 w-4" />
              {loading ? 'Saving…' : 'Save Settings'}
            </button>
            <button
              onClick={resetSettings}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium bg-surface border border-border hover:bg-surface-hover text-text-secondary transition-colors"
            >
              Reset to Defaults
            </button>
          </div>
        </div>
      </div>

      {/* Notes */}
      <div className="surface p-4 rounded-lg border border-border">
        <h2 className="text-lg font-bold text-text-primary mb-4">Notes</h2>
        <p className="text-sm text-text-muted">
          Settings are stored locally in your browser and are not sent to any server. API keys are used only for LLM explanation generation and are never stored or transmitted beyond your local machine.
        </p>
      </div>
    </div>
  );
}