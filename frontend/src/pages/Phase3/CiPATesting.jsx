import React, { useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';
import RegulatorySignoffModal from '../../components/Phase3/RegulatorySignoffModal';

const CiPATesting = () => {
  const [smiles, setSmiles] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [pdfOpen, setPdfOpen] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfResult, setPdfResult] = useState(null);

  const handleAnalyze = async () => {
    if (!smiles.trim()) {
      setError('Please enter a SMILES string');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await fetch('/api/cardiotox/cipa', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles: smiles.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Analysis failed');
      }
      setResult(data);
      toast.success('Cardiotox alert screen complete');
    } catch (err) {
      setError(err.message);
      toast.error('Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async () => {
    setPdfLoading(true);
    try {
      const res = await fetch('/api/report/regulatory-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          smiles: smiles.trim(),
          compound_name: smiles.trim(),
          batch_id: 'PHASE3',
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'PDF export failed');
      }
      setPdfResult(data);
      setPdfOpen(true);
      toast.success('Regulatory PDF generated');
    } catch (err) {
      setError(err.message);
      toast.error('PDF export failed');
    } finally {
      setPdfLoading(false);
    }
  };

  const getRiskColor = (risk) => {
    const colors = {
      LOW_ARRHYTHMIC_RISK: 'bg-green-100 text-green-800 border-green-200',
      INTERMEDIATE_MONITOR: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      HIGH_TORSADES_RISK: 'bg-red-100 text-red-800 border-red-200',
    };
    return colors[risk] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <Toaster />
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary">Multi-Channel Cardiotox Alert Screen (Structure-Based)</h1>
        <p className="text-sm text-text-muted mt-1">
          SMARTS structural-alert estimates of hERG, Nav1.5, and Cav1.2 blocking with heuristic proarrhythmic risk classification. Not the FDA CiPA paradigm — hypothesis generator only.
        </p>
      </div>

      {/* Input panel */}
      <div className="bg-surface border border-border rounded-xl p-6 mb-6">
        <div className="flex gap-4">
          <input
            type="text"
            value={smiles}
            onChange={(e) => setSmiles(e.target.value)}
            placeholder="Enter SMILES string (e.g., CC(=O)OC1=CC=CC=C1)"
            className="flex-1 px-4 py-3 bg-canvas-elevated border border-border rounded-lg focus:ring-2 focus:ring-accent-green/30 text-text-primary"
            onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
          />
          <button
            onClick={handleAnalyze}
            disabled={loading || !smiles.trim()}
            className="px-6 py-3 bg-accent-green text-white rounded-lg font-medium hover:bg-accent-green/90 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </button>
        </div>

        {smiles && result && (
          <div className="mt-4 flex gap-2">
            <button
              onClick={handleExportPDF}
              disabled={pdfLoading}
              className="px-4 py-2 border border-border rounded-lg hover:bg-surface text-sm font-medium transition-colors"
            >
              {pdfLoading ? 'Generating...' : 'Export Regulatory PDF'}
            </button>
          </div>
        )}

        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="bg-surface border border-border rounded-xl p-6">
          <h2 className="text-lg font-semibold text-text-primary mb-4">Analysis Results</h2>

          {/* Risk classification banner */}
          <div className={`inline-block px-4 py-2 rounded-lg border mb-4 ${getRiskColor(result.risk_classification)}`}>
            <span className="font-bold">{result.ghs_risk_flag || result.risk_classification}</span>
          </div>

          {/* Channel probabilities table */}
          <div className="overflow-x-auto mb-4">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left py-2">Channel</th>
                  <th className="text-right py-2">Probability</th>
                  <th className="text-center py-2">95% CI</th>
                  <th className="text-left py-2">Matched Alerts</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(result.channels || {}).map(([name, ch]) => (
                  <tr key={name} className="border-b border-border/30">
                    <td className="py-2 font-medium">{name.replace('_channel', '').toUpperCase()}</td>
                    <td className="text-right py-2">{ch.probability.toFixed(4)}</td>
                    <td className="text-center py-2 text-text-muted">
                      [{ch.conformal_ci_low.toFixed(3)}, {ch.conformal_ci_high.toFixed(3)}]
                    </td>
                    <td className="py-2 text-text-muted">
                      {ch.matched_alerts && ch.matched_alerts.length > 0
                        ? ch.matched_alerts.map(a => a.name).join(', ')
                        : 'None'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Key metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            <div className="bg-canvas-elevated rounded-lg p-3">
              <span className="text-xs text-text-muted">qNet</span>
              <div className="text-xl font-bold text-text-primary">{result.q_net?.toFixed(4)}</div>
            </div>
            <div className="bg-canvas-elevated rounded-lg p-3">
              <span className="text-xs text-text-muted">PRS</span>
              <div className="text-xl font-bold text-text-primary">{result.proarrhythmic_risk_score?.toFixed(4)}</div>
            </div>
            <div className="bg-canvas-elevated rounded-lg p-3">
              <span className="text-xs text-text-muted">Model</span>
              <div className="text-sm font-medium text-text-primary">{result.model}</div>
            </div>
            <div className="bg-canvas-elevated rounded-lg p-3">
              <span className="text-xs text-text-muted">Version</span>
              <div className="text-sm font-medium text-text-primary">{result.model_version}</div>
            </div>
          </div>

          {/* Conformal prediction CI */}
          {result.conformal_prediction && (
            <div className="mb-4 p-3 bg-canvas-elevated rounded-lg">
              <span className="text-xs text-text-muted">Conformal q_hat (max residual):</span>
              <span className="ml-2 text-sm font-medium text-text-primary">
                {result.conformal_prediction.q_hat.toFixed(4)}
              </span>
            </div>
          )}

          {/* Mechanism details */}
          {result.mechanistic_details && (
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-2">Mechanistic Interpretation</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {Object.entries(result.mechanistic_details).map(([key, val]) => (
                  <div key={key} className="bg-canvas-elevated rounded-lg p-3">
                    <span className="text-xs text-text-muted block">{key.replace(/_/g, ' ')}</span>
                    <span className="text-sm font-medium text-text-primary">{String(val)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Regulatory Signoff Modal */}
      {pdfOpen && pdfResult && (
        <RegulatorySignoffModal
          pdfResult={pdfResult}
          onClose={() => setPdfOpen(false)}
          onVerify={async (path) => {
            const res = await fetch(`/api/report/verify-signature?pdf_path=${encodeURIComponent(path)}`);
            return await res.json();
          }}
        />
      )}
    </div>
  );
};

export default CiPATesting;
