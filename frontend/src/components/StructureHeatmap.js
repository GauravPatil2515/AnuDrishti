import React, { useEffect, useState } from 'react';
import api from '../api';

/**
 * StructureHeatmap — renders a 2D molecular structure with atoms coloured by
 * real GNN attention weights (blue = low importance → red = high importance).
 * Backed by POST /api/visualize/attention-heatmap (Milestone B.2).
 */
const StructureHeatmap = ({ smiles, height = '180px' }) => {
  const [svg, setSvg] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!smiles) return undefined;
    let active = true;
    setLoading(true);
    setErr(null);
    api
      .post('/api/visualize/attention-heatmap', { smiles })
      .then((res) => {
        if (active && res.data?.success) setSvg(res.data.svg);
        else if (active) setErr('Attention map unavailable');
      })
      .catch(() => active && setErr('Attention map unavailable'))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [smiles]);

  return (
    <div>
      <div
        className="flex items-center justify-center overflow-auto rounded-lg bg-surface p-3"
        style={{ minHeight: height }}
      >
        {loading ? (
          <div className="flex items-center gap-2 text-xs text-muted">
            <svg className="animate-spin h-3 w-3" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"></circle>
            </svg>
            Rendering attention map…
          </div>
        ) : svg ? (
          <div className="w-full [&>svg]:h-auto [&>svg]:max-w-full [&>svg]:w-auto" dangerouslySetInnerHTML={{ __html: svg }} />
        ) : (
          <span className="font-mono text-xs text-muted break-all">{smiles}</span>
        )}
      </div>

      <div className="mt-1.5 flex items-center justify-center gap-1.5 text-[10px] text-muted">
        <span>Low</span>
        <span
          className="h-1.5 w-24 rounded-full"
          style={{ background: 'linear-gradient(to right, rgb(51,115,255), rgb(255,51,51))' }}
        />
        <span>High attention</span>
      </div>

      {err && <p className="mt-1 text-center text-xs text-red-400">{err}</p>}
    </div>
  );
};

export default StructureHeatmap;