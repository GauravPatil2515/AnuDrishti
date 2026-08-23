import React, { useState, useEffect, useRef } from 'react';
import { clsx } from 'clsx';
import { toast } from 'react-hot-toast';
import { SwatchIcon, Squares2X2Icon, InformationCircleIcon, CubeIcon } from '@heroicons/react/24/outline';
import StructureHeatmap from './StructureHeatmap';

const MolecularExplorer = ({ analysis }) => {
  const [toggle, setToggle] = useState('attention');
  const [rdkitReady, setRdkitReady] = useState(false);
  const [rdkitFailed, setRdkitFailed] = useState(false);
  const [depictSvg, setDepictSvg] = useState(null);
  const [depictLoading, setDepictLoading] = useState(false);
  const [rdkitSvg, setRdkitSvg] = useState(null);

  const apiBase = process.env.REACT_APP_API_BASE || '';

  useEffect(() => {
    // Check if RDKit is loaded
    let timeout;
    const checkRdkit = async () => {
      if (window.RDKit) {
        setRdkitReady(true);
        clearTimeout(timeout);
        return;
      }
      // Poll for RDKit.js (loaded from CDN) up to ~6s
      const waitForRdkit = setInterval(() => {
        if (window.RDKit) {
          clearInterval(waitForRdkit);
          clearTimeout(timeout);
          setRdkitReady(true);
        }
      }, 200);
      // Fallback: if RDKit never loads (offline), degrade gracefully
      timeout = setTimeout(() => {
        clearInterval(waitForRdkit);
        setRdkitFailed(true);
      }, 6000);
    };
    checkRdkit();
    return () => { clearTimeout(timeout); };
  }, []);

  const fetchDepictSvg = async (smiles) => {
    if (!smiles) return;
    setDepictLoading(true);
    try {
      const res = await fetch(`${apiBase}/api/depict`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ smiles })
      });
      const data = await res.json();
      if (data.success && data.svg) {
        setDepictSvg(data.svg);
      }
    } catch (e) {
      console.error('Depict fetch failed:', e);
    } finally {
      setDepictLoading(false);
    }
  };

  const renderStructure = (smiles) => {
    if (!smiles) {
      setRdkitSvg(null);
      return;
    }
    if (rdkitFailed) {
      setRdkitSvg(null);
      return;
    }
    if (!rdkitReady) {
      setRdkitSvg(null);
      return;
    }
    try {
      const RDKit = window.RDKit;
      const mol = RDKit.get_mol(smiles);
      if (mol) {
        const svg = mol.get_svg();
        setRdkitSvg(svg);
        mol.delete();
      } else {
        setRdkitSvg(null);
      }
    } catch (e) {
      console.error('RDKit rendering failed:', e);
      setRdkitSvg(null);
    }
  };

  // Render structure when SMILES changes
  useEffect(() => {
    if (analysis?.smiles) {
      renderStructure(analysis.smiles);
      // Also fetch backend SVG as fallback
      fetchDepictSvg(analysis.smiles);
    }
  }, [analysis?.smiles, rdkitReady]);

  if (!analysis) {
    return (
      <div className="rounded-lg border border-border bg-surface p-8 text-center text-muted">
        Run an analysis to explore the molecular graph and risk-associated regions.
      </div>
    );
  }

  const smiles = analysis.smiles;
  const substructures = analysis.substructures || [];
  const topSub = substructures[0];
  const attnSource = analysis.attention_source;

  return (
    <div className="grid gap-3 lg:grid-cols-3">
      {/* Molecule image + attention heatmap + 2D structure */}
      <div className="surface-elevated rounded-lg p-3 lg:col-span-2">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted">Molecular Graph</h3>
          <div className="flex gap-1 rounded-md bg-border p-1">
            {[
              { id: 'attention', label: 'Attention', icon: SwatchIcon },
              { id: 'substructure', label: 'Substructure', icon: Squares2X2Icon },
              { id: 'structure', label: '2D Structure', icon: CubeIcon },
            ].map((t) => (
              <button
                key={t.id}
                onClick={() => setToggle(t.id)}
                className={clsx(
                  'flex items-center gap-1 rounded px-2 py-1 text-xs font-medium transition-all',
                  toggle === t.id
                    ? 'bg-accent-emerald text-white border border-accent-emerald'
                    : 'text-white/60 hover:text-white hover:bg-surface'
                )}
              >
                <t.icon className="h-3 w-3" />
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {toggle === 'attention' ? (
          <div className="rounded-lg border border-border bg-canvas p-2">
            <StructureHeatmap smiles={smiles} />
          </div>
        ) : toggle === 'substructure' ? (
          <div className="flex min-h-[180px] items-center justify-center rounded-lg bg-surface p-3">
            <span className="font-mono text-xs text-muted break-all">{smiles}</span>
          </div>
        ) : (
          <div className="rounded-lg border border-border bg-canvas p-2 min-h-[180px] flex flex-col items-center justify-center">
            {/* SMILES code box with copy button */}
            <div className="mb-2 flex w-full items-center justify-between">
              <div className="flex-1 min-w-0">
                <code className="font-mono text-xs text-text-primary bg-canvas/50 px-2 py-1 rounded border border-border break-all">{smiles}</code>
              </div>
              <button
                onClick={() => {
                  navigator.clipboard.writeText(smiles);
                  toast.success('SMILES copied!');
                }}
                className="p-1 rounded hover:bg-surface-hover text-text-muted hover:text-text-primary transition-colors"
                title="Copy SMILES"
              >
                <InformationCircleIcon className="h-3 w-3" />
              </button>
            </div>

            {/* SVG container with dark background */}
            <div className="relative w-full max-w-xs h-full min-h-[140px] flex items-center justify-center">
                {!rdkitReady && (
                  <div className="text-center text-muted text-xs">
                    {rdkitFailed ? 'RDKit.js unavailable (offline)' : 'Loading RDKit.js…'}
                  </div>
                )}
                {rdkitReady && rdkitSvg && (
                  <div dangerouslySetInnerHTML={{ __html: rdkitSvg }} />
                )}
                {rdkitFailed && depictSvg && (
                  <div dangerouslySetInnerHTML={{ __html: depictSvg }} />
                )}
                {rdkitFailed && !depictSvg && !depictLoading && (
                  <div className="text-center text-muted text-xs">Offline mode - structure unavailable</div>
                )}
                {depictLoading && (
                  <div className="text-center text-muted text-xs">Loading structure from server…</div>
                )}
            </div>
          </div>
        )}
      </div>

      {/* Attention heatmap sub-components (placeholder) */}
      <div className="surface-elevated rounded-lg p-3">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted">Attention Details</h3>
        </div>
        <div className="space-y-2">
          {attnSource && (
            <>
              <p className="text-xs font-semibold text-text-primary">Source: {attnSource}</p>
              {substructures.length > 0 && (
                <>
                  <p className="text-xs font-semibold text-text-primary">
                    Top Substructure: {typeof topSub === 'string' ? topSub : (topSub.name || topSub.smarts || 'Alert')}
                  </p>
                  <p className="text-xs text-text-muted">{substructures.length} substructures detected</p>
                </>
              )}
            </>
          )}
        </div>
      </div>

      {/* Substructure highlights */}
      <div className="surface-elevated rounded-lg p-3">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-xs font-bold uppercase tracking-wider text-muted">Substructure Highlights</h3>
        </div>
        <div className="space-y-2">
          {substructures.length > 0 ? (
            <>
              {substructures.map((sub, idx) => (
                <div key={idx} className="flex items-center justify-between px-3 py-1 bg-surface/50 rounded">
                  <span className="font-mono text-xs">
                    {typeof sub === 'string' ? sub : (sub.name || sub.smarts || 'Alert')}
                  </span>
                  <span className="text-xs text-text-muted">
                    {typeof sub === 'object' && sub.category ? sub.category : 'Highlighted'}
                  </span>
                </div>
              ))}
              <p className="text-xs text-text-muted mt-2">Click on a substructure to view details</p>
            </>
          ) : (
            <p className="text-xs text-text-muted">No substructures detected</p>
          )}
        </div>
      </div>
    </div>
  );
};

export default MolecularExplorer;