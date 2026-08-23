import React, { useState, useEffect, useRef } from 'react';
import {
  BeakerIcon,
  ChartBarIcon,
  EyeIcon,
  ShieldCheckIcon,
  ScaleIcon,
  InformationCircleIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import api from '../../api';
import toast, { Toaster } from 'react-hot-toast';

const AdvancedPanels = () => {
  const [smiles, setSmiles] = useState('');
  const [cnsResult, setCnsResult] = useState(null);
  const [kinomeResult, setKinomeResult] = useState(null);
  const [loading, setLoading] = useState(null);
  const cnsCanvasRef = useRef(null);
  const kinomeCanvasRef = useRef(null);

  const analyzeCNS = async () => {
    if (!smiles.trim()) {
      toast.error('Please enter a SMILES string');
      return;
    }
    setLoading('cns');
    try {
      const response = await api.post('/api/safety/cns-pgp', {
        smiles: smiles.trim(),
      });
      setCnsResult(response.data);
      toast.success('CNS P-gp analysis complete');
    } catch (error) {
      toast.error(`CNS analysis failed: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(null);
    }
  };

  const analyzeKinome = async (target = 'EGFR') => {
    if (!smiles.trim()) {
      toast.error('Please enter a SMILES string');
      return;
    }
    setLoading('kinome');
    try {
      const response = await api.post('/api/safety/kinome-selectivity', {
        smiles: smiles.trim(),
        target_kinase: target,
      });
      setKinomeResult(response.data);
      toast.success(`Kinome selectivity analysis complete (target: ${target})`);
    } catch (error) {
      toast.error(`Kinome analysis failed: ${error.response?.data?.error || error.message}`);
    } finally {
      setLoading(null);
    }
  };

  // Draw CNS quadrant chart
  useEffect(() => {
    if (!cnsResult) return;
    const canvas = cnsCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const size = 240;
    canvas.width = size;
    canvas.height = size;

    ctx.clearRect(0, 0, size, size);

    // Quadrant grid lines
    ctx.strokeStyle = '#ddd';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(size / 2, 0);
    ctx.lineTo(size / 2, size);
    ctx.moveTo(0, size / 2);
    ctx.lineTo(size, size / 2);
    ctx.stroke();

    // Labels
    ctx.fillStyle = '#666';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Low BBB', size / 2, 15);
    ctx.fillText('High BBB', size / 2, size - 5);
    ctx.textAlign = 'left';
    ctx.fillText('Low P-gp', 5, size / 2);
    ctx.textAlign = 'right';
    ctx.fillText('High P-gp', size - 5, size / 2);

    // Plot BBB vs P-gp (scaled)
    const bbbX = (cnsResult.bbb_permeability || 0) * (size - 30) + 15;
    const pgpY = size - ((cnsResult.pgp_substrate_probability || 0) * (size - 30) + 15);

    ctx.fillStyle = '#3B82F6';
    ctx.beginPath();
    ctx.arc(bbbY, pgpY, 6, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = '#1E40AF';
    ctx.lineWidth = 2;
    ctx.stroke();
  }, [cnsResult]);

  // Draw Kinome radar chart
  useEffect(() => {
    if (!kinomeResult) return;
    const canvas = kinomeCanvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const size = 240;
    const centerX = size / 2;
    const centerY = size / 2;
    const radius = 90;
    const n = 15;
    canvas.width = size;
    canvas.height = size;

    ctx.clearRect(0, 0, size, size);

    const affinities = kinomeResult.kinase_affinities || {};
    const values = STANDARD_KINASE_NAMES.map(name =>
      (affinities[name]?.binding_probability || 0)
    );

    // Draw grid circles
    ctx.strokeStyle = '#eee';
    ctx.lineWidth = 1;
    for (let r = 1; r <= 5; r++) {
      ctx.beginPath();
      ctx.arc(centerX, centerY, (radius / 5) * r, 0, 2 * Math.PI);
      ctx.stroke();
    }

    // Draw axes
    for (let i = 0; i < n; i++) {
      const angle = (2 * Math.PI / n) * i - Math.PI / 2;
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(x, y);
      ctx.strokeStyle = '#eee';
      ctx.stroke();
    }

    // Draw data polygon
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const angle = (2 * Math.PI / n) * i - Math.PI / 2;
      const val = values[i];
      const x = centerX + Math.cos(angle) * radius * val;
      const y = centerY + Math.sin(angle) * radius * val;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();
    ctx.fillStyle = 'rgba(16, 185, 129, 0.3)';
    ctx.fill();
    ctx.strokeStyle = '#10B981';
    ctx.lineWidth = 2;
    ctx.stroke();
  }, [kinomeResult]);

  const CNSScoreGauge = ({ score, category }) => {
    const pct = score * 100;
    const color = category === 'HIGH' ? '#EF4444' : category === 'MODERATE' ? '#F59E0B' : '#10B981';

    return (
      <div className="relative w-24 h-24">
        <svg className="w-full h-full" viewBox="0 0 100 100">
          <circle
            cx="50" cy="50" r="40" fill="none"
            stroke="#e5e7eb" strokeWidth="8"
          />
          <circle
            cx="50" cy="50" r="40" fill="none"
            stroke={color} strokeWidth="8"
            strokeDasharray={`${pct} ${100 - pct}`}
            strokeLinecap="round"
            transform="rotate(-90 50 50)"
          />
          <text x="50" y="50" textAnchor="middle"
                dominantBaseline="middle" fontSize="12" fontWeight="bold" fill="#333">
            {(score * 100).toFixed(0)}%
          </text>
        </svg>
        <span className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 text-xs font-semibold">
          {category}
        </span>
      </div>
    );
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <Toaster position="top-right" />

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
          <ChartBarIcon className="h-6 w-6 text-purple-600" />
          Advanced Safety Panels
        </h1>
        <p className="text-sm text-gray-600 mt-1">
          CNS BBB/P-gp composite scoring and Kinome Selectivity Index (SI)
          across 15 standard oncology kinase targets.
        </p>
      </div>

      {/* SMILES input */}
      <div className="bg-white border border-gray-200 rounded-lg p-4 mb-6">
        <input
          type="text"
          value={smiles}
          onChange={(e) => setSmiles(e.target.value)}
          placeholder="Enter molecule SMILES (e.g., CC(=O)OC1=CC=CC=C1)"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          onKeyPress={(e) => e.key === 'Enter' && analyzeCNS()}
        />
        <div className="flex gap-2 mt-3">
          <button
            onClick={analyzeCNS}
            disabled={loading === 'cns' || !smiles.trim()}
            className="px-3 py-1 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm flex items-center gap-1"
          >
            {loading === 'cns' ? 'Analyzing...' : 'CNS P-gp Analysis'}
          </button>
          <button
            onClick={() => analyzeKinome('EGFR')}
            disabled={loading === 'kinome' || !smiles.trim()}
            className="px-3 py-1 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 text-sm flex items-center gap-1"
          >
            {loading === 'kinome' ? 'Analyzing...' : 'Kinome SI (EGFR)'}
          </button>
        </div>
      </div>

      {/* CNS Results */}
      {cnsResult && cnsResult.success && (
        <div className="bg-white border border-gray-200 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <EyeIcon className="h-5 w-5 text-blue-600" />
            CNS Safety - BBB / P-gp Composite
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
            <div className="flex flex-col items-center">
              <CNSScoreGauge
                score={cnsResult.cns_exposure_score || 0}
                category={cnsResult.cns_risk_category || 'MODERATE'}
              />
              <p className="text-sm text-gray-600 mt-2">
                {cnsResult.cns_risk_description}
              </p>
            </div>

            <div className="space-y-3">
              <div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">BBB Permeability</span>
                  <span className="font-semibold">{(cnsResult.bbb_permeability * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{ width: `${cnsResult.bbb_permeability * 100}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">P-gp Substrate Prob.</span>
                  <span className="font-semibold">{(cnsResult.pgp_substrate_probability * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-red-500 h-2 rounded-full"
                    style={{ width: `${cnsResult.pgp_substrate_probability * 100}%` }}
                  />
                </div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Properties</h3>
              <table className="w-full text-xs">
                <tbody>
                  <tr>
                    <td className="text-gray-500">MW</td>
                    <td className="font-mono">{cnsResult.properties?.molecular_weight?.toFixed(1)}</td>
                  </tr>
                  <tr>
                    <td className="text-gray-500">logP</td>
                    <td className="font-mono">{cnsResult.properties?.logp?.toFixed(2)}</td>
                  </tr>
                  <tr>
                    <td className="text-gray-500">TPSA</td>
                    <td className="font-mono">{cnsResult.properties?.tpsa?.toFixed(1)}</td>
                  </tr>
                  <tr>
                    <td className="text-gray-500">HBD</td>
                    <td className="font-mono">{cnsResult.properties?.hbd}</td>
                  </tr>
                </tbody>
              </table>
              {cnsResult.pgp_matched_alerts?.length > 0 && (
                <div className="mt-2">
                  <p className="text-xs text-gray-500">P-gp alerts:</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {cnsResult.pgp_matched_alerts.map((a) => (
                      <span key={a} className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Formula */}
          <div className="mt-4 p-2 bg-gray-50 rounded text-xs text-gray-600">
            Score_CNS = P(BBB) x (1.0 - 0.7 x P(P-gp)) = {(cnsResult.bbb_permeability).toFixed(3)} x (1.0 - 0.7 x {(cnsResult.pgp_substrate_probability).toFixed(3)}) = {cnsResult.cns_exposure_score.toFixed(3)}
          </div>
        </div>
      )}

      {/* Kinome Results */}
      {kinomeResult && kinomeResult.success && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-800 mb-4 flex items-center gap-2">
            <ScaleIcon className="h-5 w-5 text-green-600" />
            Kinome Selectivity Index
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="flex flex-col items-center">
              <canvas ref={kinomeCanvasRef} className="w-48 h-48" />
              <p className="text-xs text-gray-500 mt-2">
                Kinase binding probability across 15 targets
              </p>
            </div>

            <div className="space-y-4">
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <span className="text-3xl font-bold text-purple-600">
                  {kinomeResult.selectivity_index?.toFixed(3)}
                </span>
                <p className="text-sm text-gray-600">Selectivity Index (SI)</p>
                <span className={`text-xs font-semibold px-2 py-1 rounded ${
                  kinomeResult.si_category === 'HIGH_SELECTIVITY'
                    ? 'bg-green-100 text-green-800'
                    : kinomeResult.si_category === 'MODERATE_SELECTIVITY'
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                }`}>
                  {kinomeResult.si_category?.replace('_', ' ')}
                </span>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-700">Target: {kinomeResult.target_kinase}</p>
                <p className="text-xs text-gray-500">
                  Target affinity: {(kinomeResult.target_affinity * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-gray-500">
                  Mean off-target: {(kinomeResult.mean_off_target_affinity * 100).toFixed(1)}%
                </p>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Kinase Affinities</h3>
              <div className="max-h-64 overflow-y-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr>
                      <th className="text-left text-gray-500">Kinase</th>
                      <th className="text-right text-gray-500">Prob.</th>
                      <th className="text-center text-gray-500">Target</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(kinomeResult.kinase_affinities || {})
                      .sort((a, b) => b[1].binding_probability - a[1].binding_probability)
                      .map(([name, data]) => (
                        <tr key={name} className={data.is_target ? 'bg-purple-50' : ''}>
                          <td className="text-gray-700">{name}</td>
                          <td className="text-right font-mono">{(data.binding_probability * 100).toFixed(1)}%</td>
                          <td className="text-center">
                            {data.is_target ? <CheckCircleIcon className="h-3 w-3 text-purple-600 mx-auto" /> : ''}
                          </td>
                        </tr>
                      ))
                    }
                  </tbody>
                </table>
              </div>
              {kinomeResult.high_risk_offtargets?.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-gray-500">High-risk off-targets (&gt;50%):</p>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {kinomeResult.high_risk_offtargets.map((off) => (
                      <span key={off.kinase} className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">
                        {off.kinase} ({Math.round(off.binding_probability * 100)}%)
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Standard kinase names for radar chart axes
const STANDARD_KINASE_NAMES = [
  'EGFR', 'VEGFR2', 'CDK2', 'BRAF', 'MEK1', 'SRC',
  'JAK2', 'PI3KCA', 'AKT1', 'MTOR', 'ALKi', 'ROS1',
  'KIT', 'PDG_FR', 'FLT3',
];

export default AdvancedPanels;
