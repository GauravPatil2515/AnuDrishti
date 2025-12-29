import React, { useState } from 'react';
import {
  BeakerIcon,
  CubeIcon,
  PlayIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  ArrowDownTrayIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

const EnhancedPredictions = () => {
  const [inputType, setInputType] = useState('smiles');
  const [inputValue, setInputValue] = useState('');
  const [selectedModels, setSelectedModels] = useState(['clintox']);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [moleculeImage, setMoleculeImage] = useState(null);
  const [moleculeProps, setMoleculeProps] = useState(null);
  const [isLoadingImage, setIsLoadingImage] = useState(false);

  const availableModels = [
    {
      id: 'tox21',
      name: 'Tox21',
      type: 'Toxicity Assessment',
      description: 'Multi-target toxicity prediction across 12 biological pathways',
      outputType: 'classification',
      accuracy: '89.5%',
      category: 'toxicity',
      examples: 'Thalidomide, Warfarin, Aspirin'
    },
    {
      id: 'clintox',
      name: 'Clinical Toxicity',
      type: 'Toxicity Assessment',
      description: 'FDA approval and clinical trial toxicity risk prediction',
      outputType: 'classification',
      accuracy: '94.2%',
      category: 'toxicity',
      examples: 'Ibuprofen, Acetaminophen, Diclofenac'
    },
    {
      id: 'bbbp',
      name: 'Blood-Brain Barrier Penetration',
      type: 'ADMET Property (Distribution)',
      description: 'BBB permeability for CNS targeting (critical for neurological drugs)',
      outputType: 'classification',
      accuracy: '91.8%',
      category: 'admet',
      examples: 'Caffeine, Morphine, Dopamine'
    },
    {
      id: 'caco2',
      name: 'Caco-2 Permeability',
      type: 'ADMET Property (Absorption)',
      description: 'Intestinal absorption prediction via epithelial cell permeability',
      outputType: 'regression',
      accuracy: 'R²: 0.87',
      category: 'admet',
      examples: 'Metformin, Atenolol, Propranolol'
    },
    {
      id: 'clearance',
      name: 'Intrinsic Clearance',
      type: 'ADMET Property (Metabolism)',
      description: 'Enzyme-mediated clearance rate (affects dosing frequency and half-life)',
      outputType: 'regression',
      accuracy: 'R²: 0.83',
      category: 'admet',
      examples: 'Midazolam, Propofol, Lidocaine'
    },
    {
      id: 'hlm_clint',
      name: 'HLM Intrinsic Clearance',
      type: 'ADMET Property (Metabolism)',
      description: 'Human liver microsomal clearance (hepatic metabolism rate prediction)',
      outputType: 'regression',
      accuracy: 'R²: 0.85',
      category: 'admet',
      examples: 'Diazepam, Verapamil, Terfenadine'
    }
  ];

  const handleModelToggle = (modelId) => {
    setSelectedModels(prev => {
      if (prev.includes(modelId)) {
        return prev.filter(id => id !== modelId);
      } else {
        return [...prev, modelId];
      }
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || selectedModels.length === 0) return;

    setIsLoading(true);
    setResults(null);

    try {
      const response = await fetch('http://localhost:5000/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          smiles: inputValue,
          models: selectedModels
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.error) {
        throw new Error(data.error);
      }

      setResults(data);

      // Fetch molecular visualization
      fetchMolecularVisualization(inputValue);

    } catch (error) {
      console.error('Prediction error:', error);
      setResults({
        error: error.message,
        smiles: inputValue
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fetchMolecularVisualization = async (smiles) => {
    setIsLoadingImage(true);
    setMoleculeImage(null);
    setMoleculeProps(null);

    try {
      const response = await fetch('http://localhost:5000/api/visualize/molecule', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          smiles: smiles,
          size: 400
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setMoleculeImage(data.image);
          setMoleculeProps(data.properties);
        }
      } else {
        console.error('Visualization failed');
      }
    } catch (error) {
      console.error('Visualization error:', error);
    } finally {
      setIsLoadingImage(false);
    }
  };

  const getInterpretation = (modelId, model, prediction, probability, results) => {
    // Use backend ADMET interpretations if available
    if (results?.admet_properties) {
      const admetMap = {
        'bbbp': 'bbb_penetration',
        'caco2': 'caco2_permeability',
        'clearance': 'hepatic_clearance',
        'hlm_clint': 'hlm_clearance'
      };

      const admetKey = admetMap[modelId];
      if (admetKey && results.admet_properties[admetKey]) {
        const admet = results.admet_properties[admetKey];
        return {
          text: admet.label || 'Unknown',
          color: admet.label === 'High' ? 'green' : admet.label === 'Low' ? 'red' : 'yellow',
          interpretation: admet.interpretation
        };
      }
    }

    // Get outputType with fallback for unknown models
    const outputType = model?.outputType || 'classification';

    // For toxicity models or fallback
    if (outputType === 'classification') {
      // For BBBP, use the label from backend
      if (modelId === 'bbbp') {
        const pred = results?.predictions?.[modelId];
        if (pred?.label) {
          return {
            text: pred.label,
            color: pred.label.includes('Permeable') ? 'green' : 'red'
          };
        }
      }

      // For toxicity models
      if (probability > 0.7) return { text: 'High Risk', color: 'red' };
      if (probability > 0.4) return { text: 'Moderate Risk', color: 'yellow' };
      return { text: 'Low Risk', color: 'green' };
    } else {
      // Regression models - generic fallback
      if (prediction > 0.7) return { text: 'High', color: 'green' };
      if (prediction > 0.3) return { text: 'Moderate', color: 'yellow' };
      return { text: 'Low', color: 'red' };
    }
  };

  const exportResults = (format) => {
    if (!results) return;

    if (format === 'csv') {
      const csv = [
        ['Model', 'Prediction', 'Probability/Value', 'Interpretation'],
        ...Object.entries(results.predictions || {}).map(([modelId, pred]) => {
          const model = availableModels.find(m => m.id === modelId);
          const interp = getInterpretation(modelId, model, pred.prediction, pred.probability, results);
          return [
            model?.name || modelId,
            pred.prediction,
            pred.probability || pred.value || 'N/A',
            interp.text
          ];
        })
      ].map(row => row.join(',')).join('\n');

      const blob = new Blob([csv], { type: 'text/csv' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'prediction_results.csv';
      a.click();
    } else if (format === 'json') {
      const json = JSON.stringify(results, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'prediction_results.json';
      a.click();
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg shadow-primary-500/10">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-2">Multi-Property Prediction</h1>
        <p className="text-gray-400">
          Predict individual ADMET properties and toxicity using independently trained GIN models
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Input & Model Selection */}
        <div className="lg:col-span-2 space-y-6">
          {/* Input Section */}
          <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg">
            <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-4">Input Method</h2>

            <div className="flex space-x-2 mb-6">
              <button
                onClick={() => setInputType('smiles')}
                className={clsx(
                  'px-4 py-2 rounded-lg font-medium transition-all',
                  inputType === 'smiles'
                    ? 'bg-gradient-to-r from-primary-600 to-accent-600 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                )}
              >
                SMILES Input
              </button>
              <button
                onClick={() => setInputType('batch')}
                className={clsx(
                  'px-4 py-2 rounded-lg font-medium transition-all',
                  inputType === 'batch'
                    ? 'bg-gradient-to-r from-primary-600 to-accent-600 text-white shadow-lg shadow-primary-500/30'
                    : 'bg-gray-800 text-gray-300 hover:bg-gray-700'
                )}
              >
                Batch Upload
              </button>
            </div>

            {inputType === 'smiles' && (
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-2">
                  SMILES String
                </label>
                <input
                  type="text"
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  placeholder="Enter SMILES notation (e.g., CC(C)Cc1ccc(cc1)C(C)C(O)=O)"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 font-mono text-sm text-gray-200 placeholder-gray-500"
                />
                <p className="text-xs text-gray-500 mt-2">
                  Enter a valid SMILES string for molecular structure
                </p>
              </div>
            )}

            {inputType === 'batch' && (
              <div className="border-2 border-dashed border-primary-500/30 rounded-lg p-8 text-center bg-gray-800/30 hover:border-primary-500/50 transition-all">
                <BeakerIcon className="h-12 w-12 text-primary-400 mx-auto mb-3" />
                <p className="text-gray-400 mb-2">Upload CSV file with SMILES column</p>
                <button className="px-4 py-2 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-lg hover:from-primary-500 hover:to-accent-500 shadow-lg shadow-primary-500/30 transition-all">
                  Browse Files
                </button>
              </div>
            )}
          </div>

          {/* Model Selection */}
          <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">Select Models</h2>
              <span className="text-sm text-gray-400">
                {selectedModels.length} selected
              </span>
            </div>

            <div className="space-y-3">
              {availableModels.map((model) => (
                <div
                  key={model.id}
                  onClick={() => handleModelToggle(model.id)}
                  className={clsx(
                    'p-4 rounded-lg border-2 cursor-pointer transition-all group',
                    selectedModels.includes(model.id)
                      ? 'border-primary-500 bg-gradient-to-br from-primary-500/20 to-accent-500/20 shadow-lg shadow-primary-500/20'
                      : 'border-gray-700 bg-gray-800/30 hover:border-primary-500/50'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start space-x-3 flex-1">
                      <div className={clsx(
                        'h-10 w-10 rounded-lg flex items-center justify-center flex-shrink-0 transition-transform group-hover:scale-110',
                        selectedModels.includes(model.id)
                          ? 'bg-gradient-to-br from-primary-500 to-accent-600 shadow-lg shadow-primary-500/50'
                          : 'bg-gradient-to-br from-primary-500/20 to-accent-500/20'
                      )}>
                        <CubeIcon className={clsx(
                          'h-5 w-5',
                          selectedModels.includes(model.id) ? 'text-white' : 'text-primary-400'
                        )} />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <h3 className="font-semibold text-gray-200">{model.name}</h3>
                          <span className="text-xs px-2 py-0.5 bg-gray-700 text-gray-300 rounded-md">
                            {model.type}
                          </span>
                        </div>
                        <p className="text-sm text-gray-400 mt-1">{model.description}</p>
                        <div className="flex items-center space-x-4 mt-2">
                          <span className="text-xs text-primary-400 font-medium">
                            {model.accuracy}
                          </span>
                        </div>
                        {model.examples && (
                          <div className="mt-2 text-xs text-gray-500">
                            Examples: {model.examples}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className={clsx(
                      'h-5 w-5 rounded border-2 flex items-center justify-center flex-shrink-0',
                      selectedModels.includes(model.id)
                        ? 'border-primary-500 bg-primary-500 shadow-sm shadow-primary-500/50'
                        : 'border-gray-600'
                    )}>
                      {selectedModels.includes(model.id) && (
                        <CheckCircleIcon className="h-4 w-4 text-white" />
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            <button
              onClick={handleSubmit}
              disabled={!inputValue.trim() || selectedModels.length === 0 || isLoading}
              className="w-full mt-6 px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 text-white font-semibold rounded-lg hover:from-primary-500 hover:to-accent-500 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2 shadow-lg shadow-primary-500/30"
            >
              {isLoading ? (
                <>
                  <ClockIcon className="h-5 w-5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <PlayIcon className="h-5 w-5" />
                  <span>Run Prediction</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Right Column - Results */}
        <div className="lg:col-span-1">
          <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 sticky top-6 shadow-lg">
            <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-4">Prediction Results</h2>

            {!results && !isLoading && (
              <div className="text-center py-12">
                <ChartBarIcon className="h-16 w-16 text-gray-700 mx-auto mb-3" />
                <p className="text-gray-500 text-sm">
                  Results will appear here after prediction
                </p>
              </div>
            )}

            {isLoading && (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500 mx-auto mb-3 shadow-sm shadow-primary-500/50"></div>
                <p className="text-gray-400">Running models...</p>
              </div>
            )}

            {results && results.error && (
              <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-4">
                <div className="flex items-start space-x-2">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <h3 className="font-medium text-red-300">Prediction Error</h3>
                    <p className="text-sm text-red-400 mt-1">{results.error}</p>
                  </div>
                </div>
              </div>
            )}

            {results && results.predictions && (
              <div className="space-y-4">
                {/* Results Table */}
                <div className="border border-gray-700 rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-800/50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase">Model</th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-400 uppercase">Result</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800">
                      {Object.entries(results.predictions).map(([endpointName, pred]) => {
                        // Try to find a matching model definition or creating a generic one
                        let modelDef = availableModels.find(m => m.id === endpointName.toLowerCase()) ||
                          availableModels.find(m => m.name === endpointName);

                        // Custom mapping for complex cases
                        if (!modelDef) {
                          if (endpointName === 'FDA_APPROVED' || endpointName === 'CT_TOX') {
                            modelDef = availableModels.find(m => m.id === 'clintox');
                          } else if (endpointName.startsWith('NR-') || endpointName.startsWith('SR-')) {
                            modelDef = availableModels.find(m => m.id === 'tox21');
                          }
                        }

                        const interpretation = getInterpretation(endpointName, modelDef, pred.prediction, pred.probability, results);

                        // Format the display value
                        let displayValue = '';

                        if (endpointName === 'Clearance' && pred.value !== undefined) {
                          // Regression output (Clearance)
                          displayValue = `${pred.value.toFixed(2)} ${pred.unit}`;
                        } else if (pred.probability !== undefined) {
                          // Classification output
                          displayValue = `Probability: ${(pred.probability * 100).toFixed(1)}%`;
                        } else if (typeof pred.prediction === 'number') {
                          displayValue = `Value: ${pred.prediction.toFixed(3)}`;
                        } else {
                          displayValue = pred.prediction || 'N/A';
                        }

                        // Override display for specific endpoints
                        const displayName = {
                          'FDA_APPROVED': 'FDA Approval',
                          'CT_TOX': 'Clinical Toxicity',
                          'BBBP': 'BBB Permeability',
                          'Clearance': 'Intrinsic Clearance'
                        }[endpointName] || endpointName;

                        return (
                          <tr key={endpointName} className="hover:bg-gray-800/30 transition-colors">
                            <td className="px-3 py-3">
                              <div className="font-medium text-gray-200">{displayName}</div>
                              <div className="text-xs text-gray-500">{modelDef?.name || 'Prediction Endpoint'}</div>
                            </td>
                            <td className="px-3 py-3">
                              <div className={clsx(
                                'inline-flex px-2 py-1 text-xs font-medium rounded-md',
                                interpretation.color === 'red' && 'bg-red-900/30 text-red-300 border border-red-500/30',
                                interpretation.color === 'yellow' && 'bg-yellow-900/30 text-yellow-300 border border-yellow-500/30',
                                interpretation.color === 'green' && 'bg-green-900/30 text-green-300 border border-green-500/30',
                                interpretation.color === 'blue' && 'bg-blue-900/30 text-blue-300 border border-blue-500/30',
                                !interpretation.color && 'bg-gray-700 text-gray-300'
                              )}>
                                {interpretation.text}
                              </div>
                              <div className="text-xs text-gray-500 mt-1">
                                {displayValue}
                              </div>
                              {interpretation.interpretation && (
                                <div className="text-xs text-gray-400 mt-1">
                                  {interpretation.interpretation}
                                </div>
                              )}
                              {pred.source && (
                                <div className="text-[10px] text-gray-600 mt-0.5">
                                  Source: {pred.source}
                                </div>
                              )}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>

                {/* Molecular Structure Visualization */}
                <div className="border border-gray-700 rounded-lg overflow-hidden bg-gray-800/30">
                  <div className="px-4 py-3 bg-gray-800/50 border-b border-gray-700">
                    <h3 className="text-sm font-semibold text-gray-300 flex items-center">
                      <CubeIcon className="w-4 h-4 mr-2 text-primary-400" />
                      Molecular Structure
                    </h3>
                  </div>

                  {isLoadingImage ? (
                    <div className="flex items-center justify-center p-8">
                      <div className="text-center">
                        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-500 mx-auto mb-2"></div>
                        <p className="text-xs text-gray-500">Generating structure...</p>
                      </div>
                    </div>
                  ) : moleculeImage ? (
                    <div className="p-4 space-y-3">
                      {/* Molecular Image */}
                      <div className="flex justify-center bg-white/5 rounded-lg p-3">
                        <img
                          src={moleculeImage}
                          alt="Molecular Structure"
                          className="max-w-full h-auto rounded"
                        />
                      </div>

                      {/* Molecular Properties */}
                      {moleculeProps && (
                        <div className="grid grid-cols-2 gap-2 text-xs">
                          <div className="bg-blue-900/20 border border-blue-500/30 rounded p-2">
                            <div className="text-blue-400 font-medium mb-0.5">MW</div>
                            <div className="text-gray-200 font-semibold">
                              {moleculeProps.molecular_weight} g/mol
                            </div>
                          </div>
                          <div className="bg-green-900/20 border border-green-500/30 rounded p-2">
                            <div className="text-green-400 font-medium mb-0.5">Atoms</div>
                            <div className="text-gray-200 font-semibold">
                              {moleculeProps.num_atoms}
                            </div>
                          </div>
                          <div className="bg-purple-900/20 border border-purple-500/30 rounded p-2">
                            <div className="text-purple-400 font-medium mb-0.5">Bonds</div>
                            <div className="text-gray-200 font-semibold">
                              {moleculeProps.num_bonds}
                            </div>
                          </div>
                          <div className="bg-orange-900/20 border border-orange-500/30 rounded p-2">
                            <div className="text-orange-400 font-medium mb-0.5">Rings</div>
                            <div className="text-gray-200 font-semibold">
                              {moleculeProps.num_rings}
                            </div>
                          </div>
                        </div>
                      )}

                      {/* SMILES Display */}
                      <div className="bg-gray-900/50 rounded p-2">
                        <div className="text-xs text-gray-500 mb-1">SMILES</div>
                        <div className="font-mono text-xs text-gray-300 break-all">
                          {inputValue}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-6 px-4">
                      <CubeIcon className="w-10 h-10 text-gray-600 mx-auto mb-2" />
                      <p className="text-xs text-gray-500">Visualization unavailable</p>
                    </div>
                  )}
                </div>

                <div className="bg-primary-500/10 border border-primary-500/30 rounded-lg p-3 backdrop-blur-sm">
                  <div className="flex items-start space-x-2">
                    <InformationCircleIcon className="h-5 w-5 text-primary-400 flex-shrink-0 mt-0.5" />
                    <p className="text-xs text-gray-300">
                      Predictions based on trained GIN models. Results should be validated experimentally.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default EnhancedPredictions;
