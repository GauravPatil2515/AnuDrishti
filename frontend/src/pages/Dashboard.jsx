import React, { useState, useEffect, useRef } from 'react';
import {
  BeakerIcon,
  ChartBarIcon,
  ClockIcon,
  CheckCircleIcon,
  CubeIcon,
  ArrowTrendingUpIcon,
  DocumentCheckIcon,
  BoltIcon,
  SignalIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';

const Dashboard = () => {
  // Sample data for demonstration (will be replaced with real API data)
  const sampleStats = {
    total_predictions: 1247,
    toxicity_predictions: 456,
    bbbp_predictions: 312,
    permeability_predictions: 289,
    clearance_predictions: 190,
    processing_time: '0.8s'
  };

  const samplePredictions = [
    {
      smiles: 'CC(C)Cc1ccc(cc1)[C@@H](C)C(=O)O',
      model: 'Clinical Toxicity',
      result: 0.12,
      timestamp: '2 min ago'
    },
    {
      smiles: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C',
      model: 'BBB Penetration',
      result: 0.89,
      timestamp: '5 min ago'
    },
    {
      smiles: 'CC(=O)Oc1ccccc1C(=O)O',
      model: 'Caco-2',
      result: 0.45,
      timestamp: '8 min ago'
    },
    {
      smiles: 'CC(C)NCC(COc1ccccc1)O',
      model: 'HLM Clearance',
      result: 0.67,
      timestamp: '12 min ago'
    },
    {
      smiles: 'c1ccc2c(c1)ccc3c2cccc3',
      model: 'Clinical Toxicity',
      result: 0.78,
      timestamp: '15 min ago'
    },
    {
      smiles: 'Nc1nc(O)c2nc[nH]c2n1',
      model: 'BBB Penetration',
      result: 0.23,
      timestamp: '18 min ago'
    },
    {
      smiles: 'CC1=C(C(=O)N(N1C)c2ccccc2)N',
      model: 'Intrinsic Clearance',
      result: 0.56,
      timestamp: '22 min ago'
    },
    {
      smiles: 'COc1ccc(cc1)C(=O)Nc2ccccc2',
      model: 'Caco-2',
      result: 0.34,
      timestamp: '25 min ago'
    }
  ];

  const [platformStats, setPlatformStats] = useState(sampleStats);
  const [recentPredictions, setRecentPredictions] = useState(samplePredictions);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [isLive, setIsLive] = useState(true);
  const [systemStatus, setSystemStatus] = useState('online');
  const counterRefs = useRef({});

  // Animated counter function
  const animateCounter = (element, start, end, duration = 1000) => {
    if (!element) return;
    const range = end - start;
    const increment = range / (duration / 16);
    let current = start;
    
    const timer = setInterval(() => {
      current += increment;
      if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
        current = end;
        clearInterval(timer);
      }
      element.textContent = Math.floor(current).toLocaleString();
    }, 16);
  };

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setSystemStatus('fetching');
        const statsResponse = await fetch('http://localhost:5000/api/stats');
        
        if (statsResponse.ok) {
          const statsData = await statsResponse.json();
          
          // Animate counters if stats changed
          if (platformStats && statsData.total_predictions !== platformStats.total_predictions) {
            const element = counterRefs.current.totalPredictions;
            if (element) {
              animateCounter(element, platformStats.total_predictions || 0, statsData.total_predictions || 0);
            }
          }
          
          setPlatformStats(statsData);
          setSystemStatus('online');
        } else {
          // Keep using sample data if API fails
          console.log('Using sample data - API not available');
          setSystemStatus('demo');
        }

        const predictionsResponse = await fetch('http://localhost:5000/api/predictions?recent=true&limit=10');
        
        if (predictionsResponse.ok) {
          const predictionsData = await predictionsResponse.json();
          if (predictionsData.predictions && predictionsData.predictions.length > 0) {
            setRecentPredictions(predictionsData.predictions);
          }
        }

        setLastUpdate(new Date());
        setIsLoading(false);
      } catch (err) {
        console.log('Using sample data - Backend not connected:', err.message);
        setSystemStatus('demo');
        setIsLoading(false);
        // Keep sample data, don't show error
      }
    };

    // Initial load
    setTimeout(() => {
      fetchDashboardData();
    }, 500);
    
    // Auto-refresh every 5 seconds for real-time feel
    const interval = setInterval(() => {
      if (isLive) {
        fetchDashboardData();
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [isLive]);

  const modelsList = [
    { name: 'Clinical Toxicity', type: 'Classification', status: 'Active', accuracy: '94.2%', property: 'Toxicity' },
    { name: 'BBB Penetration', type: 'Classification', status: 'Active', accuracy: '91.8%', property: 'Distribution' },
    { name: 'Caco-2 Permeability', type: 'Regression', status: 'Active', accuracy: 'R²: 0.87', property: 'Absorption' },
    { name: 'Intrinsic Clearance', type: 'Regression', status: 'Active', accuracy: 'R²: 0.83', property: 'Metabolism' },
    { name: 'HLM Clearance', type: 'Regression', status: 'Active', accuracy: 'R²: 0.85', property: 'Metabolism' }
  ];

  const predictionTypes = [
    { name: 'Toxicity', count: platformStats?.toxicity_predictions || 456, color: 'primary' },
    { name: 'BBBP', count: platformStats?.bbbp_predictions || 312, color: 'accent' },
    { name: 'Permeability', count: platformStats?.permeability_predictions || 289, color: 'success' },
    { name: 'Clearance', count: platformStats?.clearance_predictions || 190, color: 'warning' }
  ];

  const stats = [
    {
      name: 'Total Predictions',
      value: platformStats?.total_predictions?.toLocaleString() || '0',
      icon: BeakerIcon,
      change: '+12.5%',
      changeType: 'increase'
    },
    {
      name: 'Models Available',
      value: '5',
      icon: CubeIcon,
      change: 'ClinTox, BBBP, Caco-2, CLint, HLM',
      changeType: 'neutral'
    },
    {
      name: 'Recent Predictions',
      value: recentPredictions.length?.toString() || '0',
      icon: ArrowTrendingUpIcon,
      change: 'Last 24 hours',
      changeType: 'neutral'
    },
    {
      name: 'Avg Processing',
      value: platformStats?.processing_time || '<1s',
      icon: ClockIcon,
      change: '98% under 2s',
      changeType: 'increase'
    }
  ];

  const getRiskBadge = (prediction) => {
    if (!prediction) return 'Unknown';
    if (prediction === 'Toxic' || prediction > 0.7) return 'High Risk';
    if (prediction === 'Non-toxic' || prediction < 0.3) return 'Low Risk';
    return 'Moderate Risk';
  };

  const getRiskColor = (risk) => {
    switch (risk) {
      case 'High Risk':
        return 'bg-red-100 text-red-800';
      case 'Low Risk':
        return 'bg-green-100 text-green-800';
      case 'Moderate Risk':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-xl p-6">
        <h3 className="font-semibold text-red-800">Error Loading Dashboard</h3>
        <p className="text-red-700 text-sm mt-1">{error}</p>
        <button 
          onClick={() => window.location.reload()} 
          className="mt-2 text-sm text-red-600 hover:text-red-500 underline"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header Section with Live Status */}
      <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg shadow-primary-500/10 relative overflow-hidden">
        {/* Animated background pulse */}
        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/5 via-accent-500/5 to-primary-500/5 animate-pulse"></div>
        
        <div className="flex items-center justify-between relative z-10">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                Scientific Control Panel
              </h1>
              {/* Live indicator */}
              <div className="flex items-center gap-2 px-3 py-1 bg-primary-500/10 border border-primary-500/30 rounded-full backdrop-blur-sm">
                <div className={clsx(
                  "h-2 w-2 rounded-full",
                  systemStatus === 'online' && "bg-green-500 animate-pulse shadow-lg shadow-green-500/50",
                  systemStatus === 'fetching' && "bg-yellow-500 animate-pulse",
                  systemStatus === 'demo' && "bg-blue-500 animate-pulse shadow-lg shadow-blue-500/50",
                  systemStatus === 'offline' && "bg-red-500"
                )}></div>
                <span className="text-xs font-semibold text-gray-300">
                  {systemStatus === 'online' ? 'LIVE' : systemStatus === 'demo' ? 'DEMO' : systemStatus.toUpperCase()}
                </span>
              </div>
            </div>
            <p className="text-gray-400">
              {systemStatus === 'demo' 
                ? 'Sample Data Mode • Backend not connected • Displaying demonstration data'
                : `Real-time monitoring • Auto-refresh every 5s • Last update: ${lastUpdate.toLocaleTimeString()}`
              }
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsLive(!isLive)}
              className={clsx(
                "px-4 py-2 rounded-lg font-medium transition-all",
                isLive 
                  ? "bg-primary-600/20 text-primary-400 border border-primary-500/30"
                  : "bg-gray-800 text-gray-400 border border-gray-700"
              )}
            >
              <div className="flex items-center gap-2">
                <SignalIcon className="h-4 w-4" />
                {isLive ? 'Live' : 'Paused'}
              </div>
            </button>
            <button
              onClick={() => window.location.href = '/app/predictions'}
              className="px-6 py-2.5 bg-gradient-to-r from-primary-600 to-accent-600 text-white font-medium rounded-lg hover:from-primary-500 hover:to-accent-500 transition-all shadow-lg shadow-primary-500/30 hover:scale-105 transform"
            >
              <div className="flex items-center gap-2">
                <BoltIcon className="h-5 w-5" />
                New Prediction
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Grid with Animations */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div 
            key={index} 
            className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 hover:shadow-xl hover:shadow-primary-500/20 transition-all group hover:scale-105 transform relative overflow-hidden"
            style={{ animationDelay: `${index * 100}ms` }}
          >
            {/* Animated background gradient */}
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary-500/5 to-transparent translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
            
            <div className="relative z-10">
              <div className="flex items-center justify-between mb-4">
                <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center group-hover:scale-110 group-hover:rotate-3 transition-all">
                  <stat.icon className="h-6 w-6 text-primary-400" />
                </div>
                {stat.changeType === 'increase' && (
                  <div className="flex items-center gap-1 text-xs text-green-400 bg-green-500/10 px-2 py-1 rounded-md">
                    <ArrowTrendingUpIcon className="h-3 w-3" />
                    {stat.change}
                  </div>
                )}
              </div>
              <div 
                ref={el => stat.name === 'Total Predictions' && (counterRefs.current.totalPredictions = el)}
                className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent"
              >
                {stat.value}
              </div>
              <div className="text-sm text-gray-400 mt-1">{stat.name}</div>
              {stat.changeType === 'neutral' && (
                <div className="text-xs mt-2 text-gray-500">
                  {stat.change}
                </div>
              )}
              
              {/* Progress bar animation for processing time */}
              {stat.name === 'Avg Processing' && (
                <div className="mt-3 w-full bg-gray-800 rounded-full h-1.5 overflow-hidden">
                  <div className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full animate-pulse" style={{ width: '98%' }}></div>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Predictions Table with Real-time Updates */}
        <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg relative overflow-hidden">
          {/* Shimmer effect on data update */}
          {systemStatus === 'fetching' && (
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-primary-500/10 to-transparent animate-shimmer"></div>
          )}
          
          <div className="flex items-center justify-between mb-6 relative z-10">
            <div className="flex items-center gap-3">
              <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                Recent Predictions
              </h2>
              {isLive && (
                <div className="flex items-center gap-1 text-xs text-primary-400">
                  <div className="h-2 w-2 rounded-full bg-primary-500 animate-ping"></div>
                  <span>{systemStatus === 'demo' ? 'Demo Mode' : 'Live Feed'}</span>
                </div>
              )}
            </div>
            <button className="text-sm text-primary-400 hover:text-primary-300 font-medium transition-colors hover:underline">
              View All
            </button>
          </div>
          
          <div className="overflow-x-auto relative z-10">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-800">
                  <th className="text-left text-xs font-medium text-gray-500 uppercase pb-3">Molecule</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase pb-3">Model</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase pb-3">Result</th>
                  <th className="text-left text-xs font-medium text-gray-500 uppercase pb-3">Time</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {recentPredictions.length > 0 ? (
                  recentPredictions.map((prediction, idx) => (
                    <tr 
                      key={idx} 
                      className="hover:bg-gray-800/50 transition-all group animate-fadeIn"
                      style={{ animationDelay: `${idx * 50}ms` }}
                    >
                      <td className="py-3 text-sm font-mono text-gray-400 truncate max-w-xs group-hover:text-primary-400 transition-colors">
                        {prediction.smiles?.substring(0, 20)}...
                      </td>
                      <td className="py-3 text-sm text-gray-300">
                        {prediction.model || 'ClinTox'}
                      </td>
                      <td className="py-3">
                        <span className={clsx(
                          'px-2 py-1 text-xs font-medium rounded-md transition-all group-hover:scale-105 inline-block',
                          getRiskColor(getRiskBadge(prediction.result))
                        )}>
                          {getRiskBadge(prediction.result)}
                        </span>
                      </td>
                      <td className="py-3 text-sm text-gray-400">
                        {prediction.timestamp || 'Just now'}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="4" className="py-8 text-center text-gray-500">
                      <div className="flex flex-col items-center gap-2">
                        <div className="h-8 w-8 border-2 border-gray-700 border-t-primary-500 rounded-full animate-spin"></div>
                        <span>Waiting for predictions...</span>
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Models Status with Real-time Indicators */}
        <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">Available Models</h2>
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse shadow-lg shadow-green-500/50"></span>
              <span className="text-sm text-gray-400">{modelsList.length} Active</span>
            </div>
          </div>
          
          <div className="space-y-3">
            {modelsList.map((model, idx) => (
              <div 
                key={idx} 
                className="flex items-center justify-between p-4 bg-gray-800/30 rounded-lg border border-gray-700 hover:border-primary-500/50 transition-all group hover:scale-[1.02] transform animate-fadeIn"
                style={{ animationDelay: `${idx * 100}ms` }}
              >
                <div className="flex items-center space-x-3">
                  <div className="h-10 w-10 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center group-hover:scale-110 group-hover:rotate-6 transition-all">
                    <CubeIcon className="h-5 w-5 text-primary-400" />
                  </div>
                  <div>
                    <div className="font-semibold text-gray-200 group-hover:text-primary-400 transition-colors">{model.name}</div>
                    <div className="text-sm text-gray-500">{model.type}</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-sm font-medium text-primary-400 mb-1">{model.accuracy}</div>
                  <div className="flex items-center justify-end space-x-1">
                    <div className="relative">
                      <span className="h-2 w-2 rounded-full bg-primary-500 shadow-sm shadow-primary-500/50 inline-block"></span>
                      <span className="absolute h-2 w-2 rounded-full bg-primary-500 animate-ping inline-block left-0"></span>
                    </div>
                    <span className="text-xs text-gray-400">{model.status}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Prediction Type Breakdown with Animated Bars */}
      <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg">
        <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-6">Prediction Type Breakdown</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {predictionTypes.map((type, idx) => (
            <div 
              key={idx} 
              className="p-4 border border-gray-800 rounded-lg bg-gray-800/30 hover:border-primary-500/50 transition-all group hover:scale-105 transform animate-fadeIn"
              style={{ animationDelay: `${idx * 100}ms` }}
            >
              <div className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent group-hover:scale-110 transform transition-transform inline-block">
                {type.count}
              </div>
              <div className="text-sm text-gray-400 mt-1">{type.name}</div>
              <div className="mt-3 w-full bg-gray-800 rounded-full h-2.5 overflow-hidden">
                <div 
                  className={clsx(
                    'h-2.5 rounded-full transition-all duration-1000 ease-out',
                    type.color === 'primary' && 'bg-gradient-to-r from-primary-500 to-accent-500 shadow-sm shadow-primary-500/50',
                    type.color === 'accent' && 'bg-gradient-to-r from-accent-500 to-primary-500 shadow-sm shadow-accent-500/50',
                    type.color === 'success' && 'bg-gradient-to-r from-green-500 to-emerald-500',
                    type.color === 'warning' && 'bg-gradient-to-r from-yellow-500 to-orange-500'
                  )}
                  style={{ 
                    width: `${Math.min((type.count / (platformStats?.total_predictions || 1)) * 100, 100)}%`,
                    transition: 'width 1s ease-out'
                  }}
                >
                  {/* Shimmer effect */}
                  <div className="h-full w-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                </div>
              </div>
              <div className="text-xs text-gray-500 mt-2">
                {((type.count / (platformStats?.total_predictions || 1)) * 100).toFixed(1)}% of total
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Batch Jobs Status */}
      <div className="bg-gradient-to-br from-gray-900 to-black rounded-xl border border-primary-500/20 p-6 shadow-lg">
        <h2 className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-6">Batch Processing Status</h2>
        <div className="text-center py-8 text-gray-400">
          <DocumentCheckIcon className="h-12 w-12 mx-auto text-gray-600 mb-3" />
          <p>No active batch jobs</p>
          <button
            onClick={() => window.location.href = '/app/batch'}
            className="mt-4 px-6 py-2.5 text-sm bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-lg hover:from-primary-500 hover:to-accent-500 shadow-lg shadow-primary-500/30 transition-all"
          >
            Start Batch Processing
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
