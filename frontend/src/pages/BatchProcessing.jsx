import React, { useState } from 'react';
import {
  DocumentDuplicateIcon,
  CloudArrowUpIcon,
  PlayIcon,
  DocumentArrowDownIcon,
  ChartBarIcon,
  CheckCircleIcon,
  ClockIcon,
  ExclamationCircleIcon,
  CubeIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

const BatchProcessing = () => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [selectedModels, setSelectedModels] = useState(['clintox']);
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [progress, setProgress] = useState(0);
  const [results, setResults] = useState(null);

  const availableModels = [
    { id: 'tox21', name: 'Tox21', type: 'Toxicity (Multi-target)' },
    { id: 'clintox', name: 'Clinical Toxicity', type: 'Toxicity (FDA)' },
    { id: 'bbbp', name: 'BBB Penetration', type: 'Distribution (ADMET)' },
    { id: 'caco2', name: 'Caco-2 Permeability', type: 'Absorption (ADMET)' },
    { id: 'clearance', name: 'Intrinsic Clearance', type: 'Metabolism (ADMET)' },
    { id: 'hlm_clint', name: 'HLM Clearance', type: 'Metabolism (ADMET)' }
  ];

  const jobHistory = [
    {
      id: 1,
      filename: 'compound_library_001.csv',
      molecules: 1250,
      status: 'completed',
      progress: 100,
      timestamp: '2024-01-15 09:45:00',
      results: { successful: 1240, failed: 10 }
    },
    {
      id: 2,
      filename: 'screening_batch_002.csv',
      molecules: 850,
      status: 'completed',
      progress: 100,
      timestamp: '2024-01-15 10:32:00',
      results: { successful: 847, failed: 3 }
    }
  ];

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setUploadedFile(file);
    }
  };

  const handleModelToggle = (modelId) => {
    setSelectedModels(prev => {
      if (prev.includes(modelId)) {
        return prev.filter(id => id !== modelId);
      } else {
        return [...prev, modelId];
      }
    });
  };

  const handleStartProcessing = () => {
    if (!uploadedFile || selectedModels.length === 0) return;
    
    setProcessingStatus('running');
    setProgress(0);
    
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setProcessingStatus('completed');
          setResults({
            totalMolecules: 150,
            successful: 147,
            failed: 3,
            processingTime: '2m 15s',
            averageTime: '0.9s per molecule'
          });
          return 100;
        }
        return prev + Math.random() * 10;
      });
    }, 500);
  };

  const handleDownloadResults = async () => {
    if (!results) return;

    try {
      const downloadUrl = 'http://localhost:5000/api/download/results?format=csv';
      const response = await fetch(downloadUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `batch_results_${new Date().toISOString().slice(0, 10)}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg shadow-primary-500/10">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-2">Batch Inference</h1>
        <p className="text-gray-400">
          Process multiple molecules with selected property predictors (each property uses a dedicated model)
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Upload & Configuration */}
        <div className="lg:col-span-2 space-y-6">
          {/* File Upload */}
          <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg">
            <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-4">Upload Data</h2>
            
            {!uploadedFile ? (
              <div className="border-2 border-dashed border-primary-500/30 rounded-lg p-12 text-center hover:border-primary-500/60 transition-all bg-gray-800/30">
                <CloudArrowUpIcon className="h-16 w-16 text-primary-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-200 mb-2">Upload CSV File</h3>
                <p className="text-sm text-gray-400 mb-4">
                  File must contain a column with SMILES notation
                </p>
                <label className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 text-white font-medium rounded-lg hover:from-primary-500 hover:to-accent-500 cursor-pointer shadow-lg shadow-primary-500/30 transition-all">
                  <input
                    type="file"
                    accept=".csv,.sdf"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  Browse Files
                </label>
                <p className="text-xs text-gray-500 mt-3">
                  Supported formats: CSV, SDF
                </p>
              </div>
            ) : (
              <div className="border border-gray-700 rounded-lg p-4 bg-gray-800/50">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <DocumentDuplicateIcon className="h-10 w-10 text-primary-400" />
                    <div>
                      <h3 className="font-semibold text-gray-200">{uploadedFile.name}</h3>
                      <p className="text-sm text-gray-500">
                        {(uploadedFile.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={() => setUploadedFile(null)}
                    className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300 font-medium transition-colors"
                  >
                    Remove
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Model Selection */}
          <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">Select Models for Batch</h2>
              <span className="text-sm text-gray-400">
                {selectedModels.length} selected
              </span>
            </div>
            
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
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
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className={clsx(
                        'h-8 w-8 rounded-lg flex items-center justify-center transition-transform group-hover:scale-110',
                        selectedModels.includes(model.id) 
                          ? 'bg-gradient-to-br from-primary-500 to-accent-600 shadow-sm shadow-primary-500/50' 
                          : 'bg-gradient-to-br from-primary-500/20 to-accent-500/20'
                      )}>
                        <CubeIcon className={clsx(
                          'h-5 w-5',
                          selectedModels.includes(model.id) ? 'text-white' : 'text-primary-400'
                        )} />
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-200 text-sm">{model.name}</h3>
                        <p className="text-xs text-gray-500">{model.type}</p>
                      </div>
                    </div>
                    <div className={clsx(
                      'h-5 w-5 rounded border-2 flex items-center justify-center',
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
              onClick={handleStartProcessing}
              disabled={!uploadedFile || selectedModels.length === 0 || processingStatus === 'running'}
              className="w-full mt-6 px-6 py-3 bg-gradient-to-r from-primary-600 to-accent-600 text-white font-semibold rounded-lg hover:from-primary-500 hover:to-accent-500 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2 shadow-lg shadow-primary-500/30"
            >
              <PlayIcon className="h-5 w-5" />
              <span>Start Batch Processing</span>
            </button>
          </div>

          {/* Processing Status */}
          {processingStatus !== 'idle' && (
            <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg">
              <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-4">Processing Status</h2>
              
              <div className="space-y-4">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-400">
                      {processingStatus === 'running' ? 'Processing...' : 'Completed'}
                    </span>
                    <span className="text-sm font-medium text-primary-400">
                      {Math.round(progress)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-800 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-primary-500 to-accent-600 h-2 rounded-full transition-all shadow-sm shadow-primary-500/50"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>

                {results && (
                  <div className="grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
                    <div>
                      <div className="text-sm text-gray-600">Total Molecules</div>
                      <div className="text-2xl font-bold text-gray-900">{results.totalMolecules}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Successful</div>
                      <div className="text-2xl font-bold text-green-600">{results.successful}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Failed</div>
                      <div className="text-2xl font-bold text-red-600">{results.failed}</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-600">Processing Time</div>
                      <div className="text-2xl font-bold text-gray-900">{results.processingTime}</div>
                    </div>
                  </div>
                )}
              </div>

              {processingStatus === 'completed' && (
                <button
                  onClick={handleDownloadResults}
                  className="w-full mt-6 px-6 py-3 bg-green-600 text-white font-semibold rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
                >
                  <DocumentArrowDownIcon className="h-5 w-5" />
                  <span>Download Results</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Right Column - Job History */}
        <div className="lg:col-span-1">
          <div className="bg-gray-900/50 backdrop-blur-sm rounded-xl border border-cyan-500/20 p-6 sticky top-6">
            <h2 className="text-lg font-semibold text-cyan-400 mb-4">Job History</h2>
            
            {jobHistory.length > 0 ? (
              <div className="space-y-3">
                {jobHistory.map((job) => (
                  <div key={job.id} className="p-4 border border-gray-700 rounded-lg hover:border-cyan-500/50 transition-colors bg-gray-800/30">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <h3 className="font-medium text-gray-200 text-sm truncate">
                          {job.filename}
                        </h3>
                        <p className="text-xs text-gray-400 mt-1">
                          {job.molecules} molecules
                        </p>
                      </div>
                      <span className={clsx(
                        'px-2 py-1 text-xs font-medium rounded-md',
                        job.status === 'completed' && 'bg-green-900/30 text-green-400 border border-green-500/30',
                        job.status === 'running' && 'bg-blue-900/30 text-blue-400 border border-blue-500/30',
                        job.status === 'failed' && 'bg-red-900/30 text-red-400 border border-red-500/30'
                      )}>
                        {job.status}
                      </span>
                    </div>
                    {job.results && (
                      <div className="text-xs text-gray-400 mt-2 pt-2 border-t border-gray-700">
                        Success: {job.results.successful} / Failed: {job.results.failed}
                      </div>
                    )}
                    <div className="text-xs text-gray-500 mt-1">
                      {job.timestamp}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-400">
                <ChartBarIcon className="h-12 w-12 mx-auto text-gray-600 mb-2" />
                <p className="text-sm">No batch jobs yet</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default BatchProcessing;
