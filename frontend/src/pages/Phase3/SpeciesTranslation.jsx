import React, { useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';

const SpeciesTranslation = () => {
  const [smiles, setSmiles] = useState('');
  const [doseMg, setDoseMg] = useState('');
  const [humanCl, setHumanCl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleTranslate = async () => {
    if (!smiles.trim()) {
      setError('Please enter a SMILES string');
      return;
    }
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const body = { smiles: smiles.trim() };
      if (doseMg) body.dose_mg = parseFloat(doseMg);
      if (humanCl) body.human_clearance = parseFloat(humanCl);
      const res = await fetch('/api/translation/animal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Translation failed');
      setResult(data);
      toast.success('Translation complete');
    } catch (err) {
      setError(err.message);
      toast.error('Translation failed');
    } finally {
      setLoading(false);
    }
  };

  const clearForm = () => {
    setSmiles('');
    setDoseMg('');
    setHumanCl('');
    setResult(null);
    setError('');
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <Toaster />
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-text-primary">Cross-Species Translation Engine</h1>
        <p className="text-sm text-text-muted mt-1">
          LD50 prediction, allometric PK scaling, HED/MOS computation, and FDA NAMs justification
        </p>
      </div>

      {/* Input panel */}
      <div className="bg-surface border border-border rounded-xl p-6 mb-6">
        <div className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-text-muted mb-1">SMILES</label>
            <input
              type="text"
              value={smiles}
              onChange={(e) => setSmiles(e.target.value)}
              placeholder="Enter SMILES string (e.g., CC(=O)OC1=CC=CC=C1)"
              className="w-full px-4 py-3 bg-canvas-elevated border border-border rounded-lg focus:ring-2 focus:ring-accent-green/30 text-text-primary"
              onKeyDown={(e) => e.key === 'Enter' && handleTranslate()}
            />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">
                Human Dose (mg, optional)
              </label>
              <input
                type="number"
                value={doseMg}
                onChange={(e) => setDoseMg(e.target.value)}
                placeholder="e.g., 100"
                className="w-full px-4 py-3 bg-canvas-elevated border border-border rounded-lg focus:ring-2 focus:ring-accent-green/30 text-text-primary"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-text-muted mb-1">
                Human Clearance (mL/min, optional)
              </label>
              <input
                type="number"
                value={humanCl}
                onChange={(e) => setHumanCl(e.target.value)}
                placeholder="e.g., 15.0"
                className="w-full px-4 py-3 bg-canvas-elevated border border-border rounded-lg focus:ring-2 focus:ring-accent-green/30 text-text-primary"
              />
            </div>
          </div>
        </div>

        <div className="mt-4 flex gap-3">
          <button
            onClick={handleTranslate}
            disabled={loading || !smiles.trim()}
            className="px-6 py-3 bg-accent-green text-white rounded-lg font-medium hover:bg-accent-green/90 disabled:opacity-50 transition-colors"
          >
            {loading ? 'Translating...' : 'Run Translation'}
          </button>
          {result && (
            <button
              onClick={clearForm}
              className="px-4 py-3 border border-border rounded-lg hover:bg-surface text-sm font-medium transition-colors"
            >
              Clear
            </button>
          )}
        </div>

        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
            {error}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div className="bg-surface border border-border rounded-xl p-6 space-y-6">
          <h2 className="text-lg font-semibold text-text-primary">Translation Results</h2>

          {/* Compound info */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-canvas-elevated rounded-lg p-3">
              <span className="text-xs text-text-muted">Molecular Weight</span>
              <div className="text-xl font-bold text-text-primary">{result.molecular_weight}</div>
            </div>
            <div className="bg-canvas-elevated rounded-lg p-3">
              <span className="text-xs text-text-muted">logP</span>
              <div className="text-xl font-bold text-text-primary">{result.logp.toFixed(4)}</div>
            </div>
            <div className="bg-canvas-elevated rounded-lg p-3">
              <span className="text-xs text-text-muted">TPSA</span>
              <div className="text-xl font-bold text-text-primary">{result.tpsa.toFixed(1)}</div>
            </div>
            <div className="bg-canvas-elevated rounded-lg p-3">
              <span className="text-xs text-text-muted">Model Hash</span>
              <div className="text-xs font-mono text-text-muted break-all">{result.model_hash}</div>
            </div>
          </div>

          {/* LD50 Table */}
          {result.ld50 && (
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-2">Acute Oral Toxicity (LD50)</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2">Species</th>
                    <th className="text-right py-2">LD50 (mg/kg)</th>
                    <th className="text-center py-2">GHS Category</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-border/30">
                    <td className="py-2">Rat</td>
                    <td className="text-right py-2">{result.ld50.rat_ld50_mg_per_kg}</td>
                    <td className="text-center py-2">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium
                        ${result.ld50.rat_ghs_category.color === 'RED' ? 'bg-red-100 text-red-800' :
                          result.ld50.rat_ghs_category.color === 'ORANGE' ? 'bg-orange-100 text-orange-800' :
                          result.ld50.rat_ghs_category.color === 'YELLOW' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'}`}>
                        {result.ld50.rat_ghs_category.category}
                      </span>
                    </td>
                  </tr>
                  <tr className="border-b border-border/30">
                    <td className="py-2">Mouse</td>
                    <td className="text-right py-2">{result.ld50.mouse_ld50_mg_per_kg}</td>
                    <td className="text-center py-2">
                      <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium
                        ${result.ld50.mouse_ghs_category.color === 'RED' ? 'bg-red-100 text-red-800' :
                          result.ld50.mouse_ghs_category.color === 'ORANGE' ? 'bg-orange-100 text-orange-800' :
                          result.ld50.mouse_ghs_category.color === 'YELLOW' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-green-100 text-green-800'}`}>
                        {result.ld50.mouse_ghs_category.category}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Allometric Clearance */}
          {result.clearance_ml_per_min_per_kg && (
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-2">
                Allometric PK Scaling (CL per kg, mL/min/kg)
              </h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2">Species</th>
                    <th className="text-right py-2">Clearance</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.clearance_ml_per_min_per_kg).map(([sp, cl]) => (
                    <tr key={sp} className="border-b border-border/30">
                      <td className="py-2 capitalize">{sp}</td>
                      <td className="text-right py-2">{cl}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Volume of Distribution */}
          {result.volume_of_distribution_l && (
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-2">Volume of Distribution (L)</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-2">Species</th>
                    <th className="text-right py-2">Vd (L)</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(result.volume_of_distribution_l).map(([sp, vd]) => (
                    <tr key={sp} className="border-b border-border/30">
                      <td className="py-2 capitalize">{sp}</td>
                      <td className="text-right py-2">{vd}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* HED & Safety Margins */}
          {(result.hed_mg || result.noael_mg || result.margin_of_safety) && (
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-2">HED & Safety Margins</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {result.hed_mg && (
                  <div className="bg-canvas-elevated rounded-lg p-3">
                    <span className="text-xs text-text-muted">HED</span>
                    <div className="text-xl font-bold text-text-primary">{result.hed_mg} mg</div>
                  </div>
                )}
                {result.noael_mg && (
                  <div className="bg-canvas-elevated rounded-lg p-3">
                    <span className="text-xs text-text-muted">NOAEL</span>
                    <div className="text-xl font-bold text-text-primary">{result.noael_mg} mg</div>
                  </div>
                )}
                {result.margin_of_safety && (
                  <div className="bg-canvas-elevated rounded-lg p-3">
                    <span className="text-xs text-text-muted">Margin of Safety</span>
                    <div className="text-xl font-bold text-text-primary">{result.margin_of_safety}</div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* NAMs Statement */}
          {result.nams_justification && (
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-2">
                FDA NAMs Modernization Act 2.0/3.0 Justification
              </h3>
              <div className="bg-canvas-elevated rounded-lg p-4 text-sm text-text-secondary prose prose-sm max-w-none">
                <p>{result.nams_justification}</p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default SpeciesTranslation;
