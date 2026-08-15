import React, { useEffect, useState } from 'react';
import axios from 'axios';

/**
 * StructureHeatmap — renders a 2D molecular structure with atoms coloured by
 * real GNN attention weights (blue = low importance → red = high importance).
 * Backed by POST /api/visualize/attention-heatmap (Milestone B.2).
 */
const StructureHeatmap = ({ smiles, height = '260px' }) => {
  const [svg, setSvg] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    if (!smiles) return undefined;
    let active = true;
    setLoading(true);
    setErr(null);
    axios
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
        className="flex items-center justify-center overflow-auto rounded-xl bg-slate-50 p-4"
        style={{ minHeight: height }}
      >
        {loading ? (
          <span className="text-sm text-slate-400">Rendering attention map…</span>
        ) : svg ? (
          <div className="w-full [&>svg]:mx-auto [&>svg]:h-auto [&>svg]:max-w-full" dangerouslySetInnerHTML={{ __html: svg }} />
        ) : (
          <span className="font-mono text-xs text-slate-400">{smiles}</span>
        )}
      </div>

      <div className="mt-2 flex items-center justify-center gap-2 text-[11px] text-slate-500">
        <span>Low</span>
        <span
          className="h-2 w-32 rounded-full"
          style={{ background: 'linear-gradient(to right, rgb(51,115,255), rgb(255,51,51))' }}
        />
        <span>High attention</span>
      </div>
      {err && <p className="mt-1 text-center text-xs text-red-400">{err}</p>}
    </div>
  );
};

export default StructureHeatmap;
