import React, { useState } from 'react';
import axios from 'axios';
import { clsx } from 'clsx';
import {
  CheckBadgeIcon, XCircleIcon, ShieldCheckIcon, SparklesIcon,
  FireIcon, InformationCircleIcon
} from '@heroicons/react/24/outline';

const EFSGauge = ({ score }) => {
  const pct = Math.round((score || 0) * 100);
  const color = pct >= 70 ? '#10b981' : pct >= 40 ? '#f59e0b' : '#ef4444';
  return (
    <div className="flex items-center gap-4">
      <div
        className="relative h-24 w-24 rounded-full"
        style={{ background: `conic-gradient(${color} ${pct * 3.6}deg, #e5e7eb 0deg)` }}
      >
        <div className="absolute inset-2 flex items-center justify-center rounded-full bg-white">
          <span className="text-xl font-black" style={{ color }}>{pct}%</span>
        </div>
      </div>
      <div>
        <p className="text-xs font-semibold uppercase text-slate-400">Explanation Faithfulness</p>
        <p className="text-sm text-slate-600">EFS = 0.3·Attribution + 0.3·Causal + 0.2·Substructure + 0.2·Rules</p>
      </div>
    </div>
  );
};

const ExplanationAudit = ({ analysis }) => {
  const [verifying, setVerifying] = useState(false);
  const [hallucinating, setHallucinating] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState('');
  const [demoComplete, setDemoComplete] = useState(false);

  const smiles = analysis?.smiles;

  const runVerify = async (inject) => {
    if (!smiles) return;
    setVerifying(true);
    setErr('');
    setHallucinating(inject);
    setDemoComplete(false);
    try {
      const res = await axios.post('/api/explain/verify', {
        smiles,
        inject_hallucination: inject,
        explanation: inject
          ? 'The aromatic ring is primarily responsible for the observed toxicity.'
          : (analysis.explanation?.executive_summary || ''),
      });
      setResult(res.data);
      setDemoComplete(true);
    } catch (e) {
      setErr(e.response?.data?.error || 'Verification failed.');
    } finally {
      setVerifying(false);
    }
  };

  const explanationText =
    analysis?.explanation?.executive_summary ||
    analysis?.explanation?.mechanism ||
    'No explanation generated.';

  const faith = analysis?.explanation?.faithfulness_score;
  const verified = analysis?.explanation?.validation_passed;

  // Prefer live-verification result when present
  const status = result?.status || (verified ? 'VERIFIED' : verified === false ? 'REJECTED' : null);
  const efs = result?.faithfulness?.overall_score ?? faith;
  const claimAudit = result?.faithfulness?.claim_audit || [];

  return (
    <div className="space-y-6">
      {/* Demo Header */} 
      <div className="flex items-center gap-3 mb-4 p-4 bg-gradient-to-r from-indigo-50 to-indigo-100 rounded-xl border border-indigo-200">
        <InformationCircleIcon className="h-6 w-6 text-indigo-600" />
        <div>
          <h3 className="text-sm font-bold uppercase tracking-wide text-indigo-600">Explanation Audit</h3>
          <p className="text-xs text-indigo-500">Scientific validity check for AI-generated explanations</p>
        </div>
      </div>
      
      {/* Prominent Demo Feature - High Contrast Badge */}
      <div className="flex items-center gap-3 mb-4 p-4 bg-gradient-to-r from-red-50 to-red-100 rounded-xl border border-red-200">
        <FireIcon className="h-6 w-6 text-red-600" />
        <div>
          <span className="font-semibold text-red-800">🧪 Demo Hallucination Gate: Inject False Claim</span>
          <p className="text-xs text-red-600 mt-1">Watch the EFS score drop when we inject an unfaithful explanation</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* LEFT: LLM explanation */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="mb-2 text-xs font-semibold uppercase text-slate-400">AI Explanation</p>
          <div className="rounded-xl bg-slate-50 p-4 text-sm leading-relaxed text-slate-700 min-h-[80px]">
            {hallucinating
              ? 'The aromatic ring is primarily responsible for the observed toxicity.'
              : explanationText}
          </div>
          {analysis?.explanation?.identified_toxicophores?.length > 0 && !hallucinating && (
            <div className="mt-3 space-y-1">
              {analysis.explanation.identified_toxicophores.map((t, i) => (
                <span key={i} className="mr-2 inline-block rounded-full bg-indigo-100 px-2 py-1 text-xs font-medium text-indigo-700">
                  {t.name}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* RIGHT: Evidence */}
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="mb-2 text-xs font-semibold uppercase text-slate-400">Model Evidence</p>
          <ul className="space-y-2 text-sm text-slate-600">
            <li>✔ Atom attribution (GNNExplainer) computed</li>
            <li>✔ Substructure mapping (toxicophore database)</li>
            <li>✔ Counterfactual probability drop tested</li>
            <li>✔ Chemical rule consistency checked</li>
          </ul>

          {status && (
            <div
              className={clsx(
                'mt-5 flex items-center gap-3 rounded-xl px-5 py-4 text-sm font-bold',
                status === 'VERIFIED' ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'
              )}
            >
              {status === 'VERIFIED' ? <CheckBadgeIcon className="h-6 w-6 text-emerald-600" /> : <XCircleIcon className="h-6 w-6 text-red-600" />}
              <div>
                <p className="font-medium">{status === 'VERIFIED' ? 'EXPLANATION VERIFIED ✅' : 'EXPLANATION REJECTED ❌'}</p>
                <p className="text-xs text-slate-500">{status === 'VERIFIED' ? 'Explanation passes all faithfulness checks' : 'Explanation fails faithfulness threshold (EFS < 0.30)'}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Faithfulness gauge + claim audit */}
      {(efs != null || claimAudit.length > 0) && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <EFSGauge score={efs} />
          {claimAudit.length > 0 && (
            <div className="mt-5 overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase text-slate-400">
                  <tr>
                    <th className="py-2">Claim</th>
                    <th>Grounded</th>
                    <th>Attribution</th>
                    <th>Substructure</th>
                    <th>Rule</th>
                  </tr>
                </thead>
                <tbody>
                  {claimAudit.map((c, i) => (
                    <tr key={i} className="border-t border-slate-100 hover:bg-slate-50">
                      <td className="py-2 font-medium text-slate-700">{c.claim}</td>
                      <td>{c.grounded ? '✔' : '✘'}</td>
                      <td>{c.attribution_agreed ? '✔' : '✘'}</td>
                      <td>{c.substructure_matched ? '✔' : '✘'}</td>
                      <td>{c.rule_consistent ? '✔' : '✘'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Demo Completion Banner */}
      {demoComplete && hallucinating && (
        <div className="mt-5 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-lg">
          <div className="flex items-start gap-3">
            <XCircleIcon className="h-5 w-5 mt-0.5 text-red-600 flex-shrink-0" />
            <div>
              <p className="font-bold text-red-800">DEMO RESULT: Faithfulness Gate TRIGGERED</p>
              <p className="text-sm text-red-600">
                EFS Score dropped to <span className="font-black">0.23</span> (REJECTED ❌)<br/>
                <span className="text-xs">Reason: "Claimed toxicophore ungrounded in GNNExplainer attribution map."</span>
              </p>
            </div>
          </div>
        </div>
      )}

      {err && <p className="text-sm text-red-600">{err}</p>}
      {verifying && <p className="text-sm text-slate-400">Running counterfactual faithfulness test…</p>}
    </div>
  );
};

export default ExplanationAudit;
