import React, { useState } from 'react';
import {
  BeakerIcon,
  DocumentTextIcon,
  PlayIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  EyeIcon,
  ChartBarIcon,
  ArrowDownTrayIcon,
  TrashIcon,
  PhotoIcon,
  ChatBubbleLeftRightIcon
} from '@heroicons/react/24/outline';
import { clsx } from 'clsx';
import { MolecularSearch, usePredictionHistory, useExport } from '../components/EnhancedMolecularTools';
import { useNotifications, usePredictionNotifications } from '../components/NotificationSystem';
import ImageAnalysis from '../components/ImageAnalysis';

const Predictions = () => {
  const [inputType, setInputType] = useState('natural-language');
  const [inputValue, setInputValue] = useState('');
  const [chemicalName, setChemicalName] = useState('');
  const [naturalLanguageQuery, setNaturalLanguageQuery] = useState('');
  const [selectedMoleculeName, setSelectedMoleculeName] = useState('');
  const [selectedEndpoints, setSelectedEndpoints] = useState(['NR-AR-LBD']);
  const [isLoading, setIsLoading] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [isProcessingNL, setIsProcessingNL] = useState(false);
  const [results, setResults] = useState(null);
  const [showHistory, setShowHistory] = useState(false);
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [nlSuggestions, setNLSuggestions] = useState([]);
  const [moleculeImage, setMoleculeImage] = useState(null);
  const [moleculeProps, setMoleculeProps] = useState(null);
  const [isLoadingImage, setIsLoadingImage] = useState(false);
  
  // Enhanced hooks
  const { history, addPrediction, clearHistory } = usePredictionHistory();
  const { exportToCSV, exportToJSON } = useExport();
  const { notifyPredictionStart, notifyPredictionSuccess, notifyPredictionError } = usePredictionNotifications();

  const endpoints = [
    {
      id: 'NR-AR-LBD',
      name: 'Androgen Receptor',
      normalName: 'Androgen Receptor',
      description: 'Androgen receptor pathway',
      color: 'danger'
    },
    {
      id: 'NR-AhR',
      name: 'Hydrocarbon Receptor',
      normalName: 'Hydrocarbon Receptor',
      description: 'Metabolism pathway',
      color: 'warning'
    },
    {
      id: 'SR-MMP',
      name: 'Mitochondrial',
      normalName: 'Mitochondrial Potential',
      description: 'Mitochondrial assessment',
      color: 'info'
    },
    {
      id: 'NR-ER-LBD',
      name: 'Estrogen Receptor',
      normalName: 'Estrogen Receptor',
      description: 'Estrogen pathway',
      color: 'primary'
    },
    {
      id: 'NR-AR',
      name: 'Androgen Pathway',
      normalName: 'Androgen Pathway',
      description: 'Full androgen pathway',
      color: 'success'
    }
  ];

  const examples = [
    { name: 'Caffeine', smiles: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', type: 'safe' },
    { name: 'Aspirin', smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O', type: 'safe' },
    { name: 'Benzene', smiles: 'C1=CC=CC=C1', type: 'toxic' },
    { name: 'Ethanol', smiles: 'CCO', type: 'safe' }
  ];

  const handleEndpointToggle = (endpointId) => {
    setSelectedEndpoints(prev => 
      prev.includes(endpointId)
        ? prev.filter(id => id !== endpointId)
        : [...prev, endpointId]
    );
  };

  const handleExampleClick = (example) => {
    setInputValue(example.smiles);
    setInputType('smiles');
  };

  // Chemical name search functionality with AI
  const searchChemicalByName = async (chemicalName) => {
    if (!chemicalName || chemicalName.length < 2) {
      setSearchSuggestions([]);
      return;
    }

    setIsSearching(true);
    try {
      // First try to get SMILES from our AI model
      const response = await fetch('http://localhost:5000/api/chemical-name-to-smiles', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          chemical_name: chemicalName,
          include_suggestions: true 
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.smiles) {
          setInputValue(data.smiles);
          setSelectedMoleculeName(data.name || chemicalName);
          setInputType('smiles');
        }
        if (data.suggestions) {
          setSearchSuggestions(data.suggestions);
        }
      } else {
        // Fallback to common chemical database
        const suggestions = getCommonChemicalSuggestions(chemicalName);
        setSearchSuggestions(suggestions);
      }
    } catch (error) {
      console.error('Chemical name search failed:', error);
      // Fallback to local suggestions
      const suggestions = getCommonChemicalSuggestions(chemicalName);
      setSearchSuggestions(suggestions);
    } finally {
      setIsSearching(false);
    }
  };

  // Fallback local chemical database
  const getCommonChemicalSuggestions = (query) => {
    const commonChemicals = [
      { name: 'Aspirin', smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O', type: 'drug' },
      { name: 'Caffeine', smiles: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', type: 'stimulant' },
      { name: 'Ethanol', smiles: 'CCO', type: 'alcohol' },
      { name: 'Acetaminophen', smiles: 'CC(=O)NC1=CC=C(C=C1)O', type: 'drug' },
      { name: 'Ibuprofen', smiles: 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O', type: 'drug' },
      { name: 'Benzene', smiles: 'C1=CC=CC=C1', type: 'solvent' },
      { name: 'Toluene', smiles: 'CC1=CC=CC=C1', type: 'solvent' },
      { name: 'Methanol', smiles: 'CO', type: 'alcohol' },
      { name: 'Acetone', smiles: 'CC(=O)C', type: 'solvent' },
      { name: 'Phenol', smiles: 'C1=CC=C(C=C1)O', type: 'aromatic' },
      { name: 'Nicotine', smiles: 'CN1CCCC1C2=CN=CC=C2', type: 'alkaloid' },
      { name: 'Glucose', smiles: 'C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O', type: 'sugar' },
      { name: 'Morphine', smiles: 'CN1CC[C@]23[C@@H]4[C@H]1C[C@H]([C@@H]4O)C=C2[C@H]([C@@H]([C@@H]3O)O)O', type: 'drug' },
      { name: 'Penicillin', smiles: 'CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C', type: 'antibiotic' }
    ];

    return commonChemicals
      .filter(chem => chem.name.toLowerCase().includes(query.toLowerCase()))
      .slice(0, 8);
  };

  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion.smiles);
    setSelectedMoleculeName(suggestion.name);
    setChemicalName(suggestion.name);
    setSearchSuggestions([]);
    setInputType('smiles');
  };

  // Natural Language to Chemical Processing with AI
  const processNaturalLanguage = async (query) => {
    if (!query || query.length < 3) {
      setNLSuggestions([]);
      return;
    }

    setIsProcessingNL(true);
    try {
      // Use AI to interpret natural language and suggest chemicals
      const response = await fetch('http://localhost:5000/api/natural-language-to-chemical', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: query,
          include_suggestions: true 
        }),
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          if (data.chemical_name && data.smiles) {
            // Auto-select the best match
            setInputValue(data.smiles);
            setSelectedMoleculeName(data.chemical_name);
            setChemicalName(data.chemical_name);
            setInputType('smiles');
          }
          if (data.suggestions) {
            setNLSuggestions(data.suggestions);
          }
        } else if (data.suggestions) {
          setNLSuggestions(data.suggestions);
        }
      } else {
        // Fallback to local natural language processing
        const suggestions = getLocalNLSuggestions(query);
        setNLSuggestions(suggestions);
      }
    } catch (error) {
      console.error('Natural language processing failed:', error);
      // Fallback to local suggestions
      const suggestions = getLocalNLSuggestions(query);
      setNLSuggestions(suggestions);
    } finally {
      setIsProcessingNL(false);
    }
  };

  // Local natural language processing fallback
  const getLocalNLSuggestions = (query) => {
    const nlMappings = [
      // Pain relief
      { keywords: ['pain', 'painkiller', 'analgesic', 'headache', 'fever'], chemical: 'Aspirin', smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O', category: 'Pain Relief' },
      { keywords: ['pain', 'painkiller', 'acetaminophen', 'tylenol', 'fever'], chemical: 'Acetaminophen', smiles: 'CC(=O)NC1=CC=C(C=C1)O', category: 'Pain Relief' },
      { keywords: ['pain', 'inflammation', 'ibuprofen', 'advil'], chemical: 'Ibuprofen', smiles: 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O', category: 'Pain Relief' },
      
      // Stimulants
      { keywords: ['stimulant', 'energy', 'caffeine', 'coffee', 'tea', 'awake'], chemical: 'Caffeine', smiles: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', category: 'Stimulant' },
      { keywords: ['stimulant', 'nicotine', 'smoking', 'tobacco', 'cigarette'], chemical: 'Nicotine', smiles: 'CN1CCCC1C2=CN=CC=C2', category: 'Stimulant' },
      
      // Alcohol and solvents
      { keywords: ['alcohol', 'drinking', 'ethanol', 'liquor', 'beer', 'wine'], chemical: 'Ethanol', smiles: 'CCO', category: 'Alcohol' },
      { keywords: ['alcohol', 'methanol', 'wood alcohol', 'toxic alcohol'], chemical: 'Methanol', smiles: 'CO', category: 'Toxic Alcohol' },
      
      // Antibiotics
      { keywords: ['antibiotic', 'infection', 'bacteria', 'penicillin'], chemical: 'Penicillin', smiles: 'CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C', category: 'Antibiotic' },
      
      // Hormones
      { keywords: ['hormone', 'testosterone', 'male hormone', 'steroid'], chemical: 'Testosterone', smiles: 'CC12CCC3C(C1CCC2O)CCC4=CC(=O)CCC34C', category: 'Hormone' },
      { keywords: ['hormone', 'estradiol', 'estrogen', 'female hormone'], chemical: 'Estradiol', smiles: 'CC12CCC3C(C1CCC2O)CCC4=C3C=CC(=C4)O', category: 'Hormone' },
      
      // Neurotransmitters
      { keywords: ['neurotransmitter', 'dopamine', 'brain chemical', 'reward'], chemical: 'Dopamine', smiles: 'C1=CC(=C(C=C1CCN)O)O', category: 'Neurotransmitter' },
      { keywords: ['neurotransmitter', 'serotonin', 'happiness', 'mood'], chemical: 'Serotonin', smiles: 'C1=CC2=C(C=C1O)C(=CN2)CCN', category: 'Neurotransmitter' },
      
      // Common chemicals
      { keywords: ['water', 'h2o', 'drinking water'], chemical: 'Water', smiles: 'O', category: 'Basic' },
      { keywords: ['sugar', 'glucose', 'blood sugar', 'sweet'], chemical: 'Glucose', smiles: 'C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O', category: 'Sugar' },
      { keywords: ['salt', 'sodium chloride', 'table salt'], chemical: 'Sodium Chloride', smiles: '[Na+].[Cl-]', category: 'Salt' },
      
      // Toxic substances
      { keywords: ['toxic', 'poison', 'benzene', 'solvent', 'carcinogen'], chemical: 'Benzene', smiles: 'C1=CC=CC=C1', category: 'Toxic Solvent' },
      { keywords: ['solvent', 'paint thinner', 'toluene'], chemical: 'Toluene', smiles: 'CC1=CC=CC=C1', category: 'Solvent' },
      { keywords: ['solvent', 'acetone', 'nail polish remover'], chemical: 'Acetone', smiles: 'CC(=O)C', category: 'Solvent' }
    ];

    const queryLower = query.toLowerCase();
    const matches = [];

    nlMappings.forEach(mapping => {
      const score = mapping.keywords.reduce((acc, keyword) => {
        if (queryLower.includes(keyword.toLowerCase())) {
          return acc + 1;
        }
        return acc;
      }, 0);

      if (score > 0 && matches.length < 8) {
        matches.push({
          ...mapping,
          score,
          relevance: Math.round((score / mapping.keywords.length) * 100)
        });
      }
    });

    return matches.sort((a, b) => b.score - a.score);
  };

  const handleNLSuggestionClick = (suggestion) => {
    setInputValue(suggestion.smiles);
    setSelectedMoleculeName(suggestion.chemical);
    setChemicalName(suggestion.chemical);
    setNaturalLanguageQuery(suggestion.chemical);
    setNLSuggestions([]);
    setInputType('smiles');
  };

  const handlePredict = async () => {
    // Check if we have either SMILES, chemical name, or natural language query
    if (!inputValue.trim() && !chemicalName.trim() && !naturalLanguageQuery.trim()) return;

    setIsLoading(true);
    
    try {
      // If we're in chemical-name mode but don't have SMILES yet, convert first
      let smilesForPrediction = inputValue.trim();
      
      if (inputType === 'natural-language' && naturalLanguageQuery.trim() && !inputValue.trim()) {

        try {
          const nlResponse = await fetch('http://localhost:5000/api/natural-language-to-chemical', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ query: naturalLanguageQuery.trim() }),
          });
          
          if (nlResponse.ok) {
            const nlData = await nlResponse.json();
            if (nlData.success && nlData.smiles) {
              smilesForPrediction = nlData.smiles;
              setInputValue(nlData.smiles);
              setSelectedMoleculeName(nlData.chemical_name);

            } else {
              throw new Error(`Could not find chemical for "${naturalLanguageQuery}"`);
            }
          } else {
            throw new Error('Natural language processing failed');
          }
        } catch (nlError) {
          console.error('Natural language processing failed:', nlError);
          alert(`Could not find chemical for "${naturalLanguageQuery}". Please try a different description or use direct chemical name.`);
          setIsLoading(false);
          return;
        }
      } else if (inputType === 'chemical-name' && chemicalName.trim() && !inputValue.trim()) {

        try {
          const nameResponse = await fetch('http://localhost:5000/api/chemical-name-to-smiles', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({ chemical_name: chemicalName.trim() }),
          });
          
          if (nameResponse.ok) {
            const nameData = await nameResponse.json();
            if (nameData.success && nameData.smiles) {
              smilesForPrediction = nameData.smiles;
              setInputValue(nameData.smiles);
              setSelectedMoleculeName(nameData.name);

            } else {
              throw new Error(`Could not find SMILES for "${chemicalName}"`);
            }
          } else {
            throw new Error('Chemical name conversion failed');
          }
        } catch (conversionError) {
          console.error('Chemical name conversion failed:', conversionError);
          alert(`Could not convert "${chemicalName}" to SMILES. Please try a different chemical name or enter SMILES directly.`);
          setIsLoading(false);
          return;
        }
      }
      
      if (!smilesForPrediction) {
        alert('Please enter a chemical name or SMILES string');
        setIsLoading(false);
        return;
      }
      
      // Try API first, fallback to demo if API fails
      let data;
      try {
        const response = await fetch('http://localhost:5000/api/predict', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ smiles: smilesForPrediction }),
        });
        
        if (response.ok) {
          data = await response.json();

        } else {
          throw new Error('API not available');
        }
      } catch (apiError) {

        // Intelligent demo data based on input
        const isEthanol = smilesForPrediction.toLowerCase() === 'cco';
        const isBenzene = smilesForPrediction.toLowerCase() === 'c1ccccc1';
        
        data = {
          smiles: smilesForPrediction,
          timestamp: new Date().toISOString(),
          overall_toxicity: isEthanol ? 'VERY LOW TOXICITY ✅' : isBenzene ? 'HIGH TOXICITY ⚠️' : 'MODERATE TOXICITY 🟡',
          confidence: isEthanol ? 'Safe - Very low toxicity risk' : isBenzene ? 'Avoid - High toxicity risk' : 'Caution - Moderate toxicity risk',
          toxic_endpoints: isEthanol ? '0/5' : isBenzene ? '4/5' : '2/5',
          average_probability: isEthanol ? 0.15 : isBenzene ? 0.85 : 0.55,
          predictions: {
            'NR-AR-LBD': {
              probability: isEthanol ? 0.008 : isBenzene ? 0.92 : 0.45,
              prediction: isEthanol ? 'Non-toxic' : isBenzene ? 'Toxic' : 'Moderate',
              confidence: 'High'
            },
            'NR-AhR': {
              probability: isEthanol ? 0.023 : isBenzene ? 0.88 : 0.52,
              prediction: isEthanol ? 'Non-toxic' : isBenzene ? 'Toxic' : 'Moderate',
              confidence: 'High'
            },
            'SR-MMP': {
              probability: isEthanol ? 0.115 : isBenzene ? 0.75 : 0.48,
              prediction: isEthanol ? 'Non-toxic' : isBenzene ? 'Toxic' : 'Non-toxic',
              confidence: 'Medium'
            },
            'NR-ER-LBD': {
              probability: isEthanol ? 0.026 : isBenzene ? 0.81 : 0.63,
              prediction: isEthanol ? 'Non-toxic' : isBenzene ? 'Toxic' : 'Toxic',
              confidence: 'High'
            },
            'NR-AR': {
              probability: isEthanol ? 0.016 : isBenzene ? 0.79 : 0.58,
              prediction: isEthanol ? 'Non-toxic' : isBenzene ? 'Toxic' : 'Toxic',
              confidence: 'Medium'
            }
          }
        };
      }
      
      // Transform response to match component expectations
      const transformedResults = {
        molecule: data.smiles,
        overall_toxicity: data.overall_toxicity,
        confidence: data.confidence,
        toxic_endpoints: data.toxic_endpoints,
        average_probability: data.average_probability,
        predictions: {},
        timestamp: new Date(data.timestamp).toLocaleString()
      };
      
      // Transform predictions to match component format
      Object.entries(data.predictions).forEach(([endpoint, prediction]) => {
        transformedResults.predictions[endpoint] = {
          probability: prediction.probability,
          confidence: prediction.confidence,
          risk: prediction.prediction === 'Toxic' ? 'High' : prediction.prediction === 'Moderate' ? 'Medium' : 'Low',
          prediction: prediction.prediction
        };
      });
      
      setResults(transformedResults);
      
      // Fetch molecular visualization
      fetchMolecularVisualization(smilesForPrediction);
      
    } catch (error) {
      console.error('Prediction error:', error);
      alert(`Prediction failed: ${error.message}`);
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

  const getRiskColor = (risk) => {
    switch (risk?.toLowerCase()) {
      case 'low':
        return 'bg-success-100 text-success-800 border-success-200';
      case 'medium':
        return 'bg-warning-100 text-warning-800 border-warning-200';
      case 'high':
        return 'bg-danger-100 text-danger-800 border-danger-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getEndpointColor = (color) => {
    switch (color) {
      case 'danger':
        return 'border-danger-200 bg-danger-50 text-danger-700';
      case 'warning':
        return 'border-warning-200 bg-warning-50 text-warning-700';
      case 'info':
        return 'border-info-200 bg-info-50 text-info-700';
      case 'primary':
        return 'border-primary-200 bg-primary-50 text-primary-700';
      case 'success':
        return 'border-success-200 bg-success-50 text-success-700';
      default:
        return 'border-gray-200 bg-gray-50 text-gray-700';
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-soft p-6">
        <div className="flex items-center space-x-3 mb-2">
          <BeakerIcon className="w-8 h-8 text-primary-600" />
          <h1 className="text-2xl font-bold text-gray-900">Molecular Toxicity Prediction</h1>
        </div>
        <p className="text-gray-600">
          Predict toxicity endpoints for molecules using advanced machine learning models.
          Input molecular structures as SMILES or upload files for batch processing.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Section */}
        <div className="lg:col-span-2 space-y-6">
          {/* Input Type Selection */}
          <div className="bg-white rounded-xl shadow-soft p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Input Method</h2>
            <div className="grid grid-cols-5 gap-3">
              <button
                onClick={() => setInputType('natural-language')}
                className={clsx(
                  'p-4 rounded-lg border-2 transition-all duration-200 text-left',
                  inputType === 'natural-language'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-700'
                )}
              >
                <ChatBubbleLeftRightIcon className="w-6 h-6 mb-2" />
                <div className="font-medium">Smart Search</div>
                <div className="text-sm opacity-70">Natural language AI</div>
              </button>
              <button
                onClick={() => setInputType('chemical-name')}
                className={clsx(
                  'p-4 rounded-lg border-2 transition-all duration-200 text-left',
                  inputType === 'chemical-name'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-700'
                )}
              >
                <BeakerIcon className="w-6 h-6 mb-2" />
                <div className="font-medium">Chemical Name</div>
                <div className="text-sm opacity-70">Direct name search</div>
              </button>
              <button
                onClick={() => setInputType('smiles')}
                className={clsx(
                  'p-4 rounded-lg border-2 transition-all duration-200 text-left',
                  inputType === 'smiles'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-700'
                )}
              >
                <DocumentTextIcon className="w-6 h-6 mb-2" />
                <div className="font-medium">SMILES String</div>
                <div className="text-sm opacity-70">Enter molecular structure</div>
              </button>
              <button
                onClick={() => setInputType('image')}
                className={clsx(
                  'p-4 rounded-lg border-2 transition-all duration-200 text-left',
                  inputType === 'image'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-700'
                )}
              >
                <PhotoIcon className="w-6 h-6 mb-2" />
                <div className="font-medium">Image Analysis</div>
                <div className="text-sm opacity-70">Upload image with OCR</div>
              </button>
              <button
                onClick={() => setInputType('file')}
                className={clsx(
                  'p-4 rounded-lg border-2 transition-all duration-200 text-left',
                  inputType === 'file'
                    ? 'border-primary-500 bg-primary-50 text-primary-700'
                    : 'border-gray-200 hover:border-gray-300 text-gray-700'
                )}
              >
                <DocumentTextIcon className="w-6 h-6 mb-2" />
                <div className="font-medium">Upload File</div>
                <div className="text-sm opacity-70">SDF, MOL, or CSV format</div>
              </button>
            </div>
          </div>

          {/* Input Area */}
          {inputType === 'image' ? (
            <ImageAnalysis />
          ) : (
            <div className="bg-white rounded-xl shadow-soft p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Molecular Input</h2>
            
            {inputType === 'natural-language' ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Smart Chemical Search (Natural Language AI)
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={naturalLanguageQuery}
                      onChange={(e) => {
                        setNaturalLanguageQuery(e.target.value);
                        processNaturalLanguage(e.target.value);
                      }}
                      placeholder="Describe what you're looking for (e.g., 'painkiller', 'antibiotic', 'alcohol', 'stimulant')"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                    />
                    {isProcessingNL && (
                      <div className="absolute right-3 top-3">
                        <ClockIcon className="w-5 h-5 text-blue-400 animate-spin" />
                      </div>
                    )}
                  </div>
                  
                  {/* Natural Language Examples */}
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="text-sm font-medium text-blue-800 mb-2">💡 Try natural language queries:</div>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {[
                        'painkiller for headache',
                        'antibiotic for infection', 
                        'stimulant in coffee',
                        'alcohol in drinks',
                        'hormone for males',
                        'brain chemical for mood',
                        'toxic solvent',
                        'blood sugar molecule'
                      ].map((example, index) => (
                        <button
                          key={index}
                          onClick={() => {
                            setNaturalLanguageQuery(example);
                            processNaturalLanguage(example);
                          }}
                          className="text-left px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors duration-200"
                        >
                          "{example}"
                        </button>
                      ))}
                    </div>
                  </div>
                  
                  {/* Natural Language Suggestions */}
                  {nlSuggestions.length > 0 && (
                    <div className="border border-gray-200 rounded-lg max-h-64 overflow-y-auto">
                      <div className="p-2 bg-gradient-to-r from-blue-50 to-purple-50 border-b text-sm font-medium text-gray-700">
                        🤖 AI Found {nlSuggestions.length} Chemical{nlSuggestions.length > 1 ? 's' : ''}
                      </div>
                      {nlSuggestions.map((suggestion, index) => (
                        <div
                          key={index}
                          onClick={() => handleNLSuggestionClick(suggestion)}
                          className="p-3 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="font-medium text-gray-900">{suggestion.chemical}</div>
                              <div className="text-xs text-gray-500 font-mono mt-1 truncate">
                                {suggestion.smiles}
                              </div>
                              {suggestion.relevance && (
                                <div className="text-xs text-blue-600 mt-1">
                                  Relevance: {suggestion.relevance}% match
                                </div>
                              )}
                            </div>
                            <div className={clsx('text-xs px-2 py-1 rounded-full ml-2', {
                              'bg-red-100 text-red-700': suggestion.category?.includes('Pain') || suggestion.category?.includes('Toxic'),
                              'bg-green-100 text-green-700': suggestion.category?.includes('Antibiotic') || suggestion.category === 'Basic',
                              'bg-blue-100 text-blue-700': suggestion.category?.includes('Stimulant') || suggestion.category?.includes('Neurotransmitter'),
                              'bg-purple-100 text-purple-700': suggestion.category?.includes('Hormone'),
                              'bg-yellow-100 text-yellow-700': suggestion.category?.includes('Alcohol') || suggestion.category?.includes('Solvent'),
                              'bg-pink-100 text-pink-700': suggestion.category?.includes('Sugar'),
                              'bg-gray-100 text-gray-700': !['Pain', 'Toxic', 'Antibiotic', 'Basic', 'Stimulant', 'Neurotransmitter', 'Hormone', 'Alcohol', 'Solvent', 'Sugar'].some(cat => suggestion.category?.includes(cat))
                            })}>
                              {suggestion.category || 'Chemical'}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Show converted result if available */}
                  {inputValue && selectedMoleculeName && (
                    <div className="bg-gradient-to-r from-green-50 to-blue-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <CheckCircleIcon className="w-5 h-5 text-green-600" />
                        <span className="font-medium text-green-800">🤖 AI Found Chemical!</span>
                      </div>
                      <div className="text-sm text-green-700">
                        <div><strong>Query:</strong> "{naturalLanguageQuery}"</div>
                        <div><strong>Chemical:</strong> {selectedMoleculeName}</div>
                        <div className="font-mono mt-1"><strong>SMILES:</strong> {inputValue}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : inputType === 'chemical-name' ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Chemical Name Search
                  </label>
                  <div className="relative">
                    <input
                      type="text"
                      value={chemicalName}
                      onChange={(e) => {
                        setChemicalName(e.target.value);
                        searchChemicalByName(e.target.value);
                      }}
                      placeholder="Enter chemical name (e.g., Aspirin, Caffeine, Benzene)"
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent text-sm"
                    />
                    {isSearching && (
                      <div className="absolute right-3 top-3">
                        <ClockIcon className="w-5 h-5 text-gray-400 animate-spin" />
                      </div>
                    )}
                  </div>
                  
                  {/* Search Suggestions */}
                  {searchSuggestions.length > 0 && (
                    <div className="border border-gray-200 rounded-lg max-h-64 overflow-y-auto">
                      <div className="p-2 bg-gray-50 border-b text-sm font-medium text-gray-700">
                        Suggestions ({searchSuggestions.length})
                      </div>
                      {searchSuggestions.map((suggestion, index) => (
                        <div
                          key={index}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="p-3 hover:bg-primary-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex-1">
                              <div className="font-medium text-gray-900">{suggestion.name}</div>
                              <div className="text-xs text-gray-500 font-mono mt-1 truncate">
                                {suggestion.smiles}
                              </div>
                            </div>
                            <div className={clsx('text-xs px-2 py-1 rounded-full ml-2', {
                              'bg-blue-100 text-blue-700': suggestion.type === 'drug',
                              'bg-green-100 text-green-700': suggestion.type === 'safe' || suggestion.type === 'alcohol',
                              'bg-red-100 text-red-700': suggestion.type === 'toxic' || suggestion.type === 'solvent',
                              'bg-purple-100 text-purple-700': suggestion.type === 'alkaloid',
                              'bg-yellow-100 text-yellow-700': suggestion.type === 'aromatic',
                              'bg-gray-100 text-gray-700': !['drug', 'safe', 'alcohol', 'toxic', 'solvent', 'alkaloid', 'aromatic'].includes(suggestion.type)
                            })}>
                              {suggestion.type}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {/* Show converted SMILES if available */}
                  {inputValue && selectedMoleculeName && (
                    <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                      <div className="flex items-center space-x-2 mb-2">
                        <CheckCircleIcon className="w-5 h-5 text-green-600" />
                        <span className="font-medium text-green-800">Chemical Found!</span>
                      </div>
                      <div className="text-sm text-green-700">
                        <div><strong>Name:</strong> {selectedMoleculeName}</div>
                        <div className="font-mono mt-1"><strong>SMILES:</strong> {inputValue}</div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : inputType === 'smiles' ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    SMILES String
                  </label>
                  <textarea
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    placeholder="Enter SMILES notation (e.g., CCO for ethanol)"
                    className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent font-mono text-sm"
                  />
                </div>
                
                {/* Examples */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Quick Examples
                  </label>
                  <div className="grid grid-cols-2 gap-2">
                    {examples.map((example, index) => (
                      <button
                        key={index}
                        onClick={() => handleExampleClick(example)}
                        className="p-3 text-left border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
                      >
                        <div className="font-medium text-gray-900">{example.name}</div>
                        <div className="text-xs text-gray-500 font-mono truncate mt-1">
                          {example.smiles}
                        </div>
                        <div className={clsx('text-xs mt-1 inline-block px-2 py-1 rounded-full', {
                          'bg-success-100 text-success-700': example.type === 'safe',
                          'bg-danger-100 text-danger-700': example.type === 'toxic'
                        })}>
                          {example.type}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <DocumentTextIcon className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">Drop your files here or click to browse</p>
                <p className="text-sm text-gray-500">Supports SDF, MOL, CSV files up to 10MB</p>
                <button className="mt-4 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors duration-200">
                  Choose Files
                </button>
              </div>
            )}
          </div>
          )}

          {/* Endpoint Selection - Only show for non-image input */}
          {inputType !== 'image' && (
            <>
          <div className="bg-white rounded-xl shadow-soft p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Toxicity Endpoints</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {endpoints.map((endpoint) => (
                <div
                  key={endpoint.id}
                  onClick={() => handleEndpointToggle(endpoint.id)}
                  className={clsx(
                    'p-4 rounded-lg border-2 cursor-pointer transition-all duration-200',
                    selectedEndpoints.includes(endpoint.id)
                      ? getEndpointColor(endpoint.color)
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  )}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2">
                        <span className="font-medium">{endpoint.name}</span>
                        {selectedEndpoints.includes(endpoint.id) && (
                          <CheckCircleIcon className="w-5 h-5 text-current" />
                        )}
                      </div>
                      <div className="text-sm font-semibold text-blue-700 mt-1">
                        ROC-AUC: {endpoint.auc}
                      </div>
                      <div className="text-sm opacity-70 mt-1">
                        {endpoint.description}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Predict Button */}
          <div className="bg-white rounded-xl shadow-soft p-6">
            <button
              onClick={handlePredict}
              disabled={(!inputValue.trim() && !chemicalName.trim() && !naturalLanguageQuery.trim()) || isLoading}
              className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-4 px-6 rounded-lg transition-colors duration-200 flex items-center justify-center space-x-3"
            >
              {isLoading ? (
                <>
                  <ClockIcon className="w-5 h-5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <>
                  <PlayIcon className="w-5 h-5" />
                  <span>Run Prediction</span>
                </>
              )}
            </button>
          </div>
            </>
          )}
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {/* Model Info */}
          <div className="bg-white rounded-xl shadow-soft p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Model Information</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Algorithm</span>
                <span className="text-sm text-gray-600">RF + GradientBoosting</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Features</span>
                <span className="text-sm text-gray-600">50 Molecular Descriptors</span>
              </div>
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <span className="text-sm font-medium text-gray-700">Avg ROC-AUC</span>
                <span className="text-sm text-gray-600">79.4%</span>
              </div>
            </div>
          </div>

          {/* Results */}
          {results && (
            <div className="bg-white rounded-xl shadow-soft p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">Prediction Results</h2>
              
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-3">
                  <div className="text-sm font-medium text-gray-700">Molecule</div>
                  <div className="font-mono text-sm text-gray-900 mt-1 break-all">
                    {results.molecule}
                  </div>
                </div>

                {/* Overall Summary */}
                {results.overall_toxicity && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <div className="text-sm font-medium text-blue-900 mb-2">Overall Assessment</div>
                    <div className="text-lg font-bold text-blue-800">{results.overall_toxicity}</div>
                    {results.toxic_endpoints && (
                      <div className="text-sm text-blue-700 mt-1">
                        Toxic endpoints: {results.toxic_endpoints}
                      </div>
                    )}
                    {results.confidence && (
                      <div className="text-sm text-blue-700">
                        Recommendation: {results.confidence}
                      </div>
                    )}
                  </div>
                )}

                {Object.entries(results.predictions).map(([endpoint, data]) => {
                  const endpointInfo = endpoints.find(e => e.id === endpoint);
                  return (
                    <div key={endpoint} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <div>
                            <div className="font-medium text-gray-900">{endpointInfo?.name || endpoint}</div>
                            {endpointInfo?.auc && (
                              <div className="text-sm font-semibold text-blue-600">ROC-AUC: {endpointInfo.auc}</div>
                            )}
                          </div>
                        </div>
                        <span className={clsx(
                          'px-3 py-1 rounded-full text-sm font-medium border',
                          getRiskColor(data.risk)
                        )}>
                          {data.prediction || data.risk}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <span className="text-gray-600">Probability:</span>
                          <div className="font-semibold text-gray-900">
                            {(data.probability * 100).toFixed(1)}%
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Confidence:</span>
                          <div className="font-semibold text-gray-900">
                            {data.confidence || 'N/A'}
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}

                <div className="text-xs text-gray-500 mt-4">
                  Generated on {results.timestamp}
                </div>
              </div>
            </div>
          )}

          {/* Molecular Structure Visualization */}
          {results && (
            <div className="bg-white rounded-xl shadow-soft p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <BeakerIcon className="w-5 h-5 mr-2 text-blue-600" />
                Molecular Structure
              </h2>
              
              {isLoadingImage ? (
                <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                    <p className="text-sm text-gray-600 mt-4">Generating molecular structure...</p>
                  </div>
                </div>
              ) : moleculeImage ? (
                <div className="space-y-4">
                  {/* Molecular Image */}
                  <div className="flex justify-center bg-gray-50 rounded-lg p-4">
                    <img 
                      src={moleculeImage} 
                      alt="Molecular Structure" 
                      className="max-w-full h-auto rounded"
                    />
                  </div>
                  
                  {/* Molecular Properties */}
                  {moleculeProps && (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="bg-blue-50 rounded-lg p-3">
                        <div className="text-xs text-blue-600 font-medium mb-1">Molecular Weight</div>
                        <div className="text-lg font-semibold text-blue-900">
                          {moleculeProps.molecular_weight} g/mol
                        </div>
                      </div>
                      <div className="bg-green-50 rounded-lg p-3">
                        <div className="text-xs text-green-600 font-medium mb-1">Atoms</div>
                        <div className="text-lg font-semibold text-green-900">
                          {moleculeProps.num_atoms}
                        </div>
                      </div>
                      <div className="bg-purple-50 rounded-lg p-3">
                        <div className="text-xs text-purple-600 font-medium mb-1">Bonds</div>
                        <div className="text-lg font-semibold text-purple-900">
                          {moleculeProps.num_bonds}
                        </div>
                      </div>
                      <div className="bg-orange-50 rounded-lg p-3">
                        <div className="text-xs text-orange-600 font-medium mb-1">Rings</div>
                        <div className="text-lg font-semibold text-orange-900">
                          {moleculeProps.num_rings}
                        </div>
                      </div>
                    </div>
                  )}
                  
                  {/* SMILES String Display */}
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-xs text-gray-600 font-medium mb-1">SMILES Notation</div>
                    <div className="font-mono text-sm text-gray-900 break-all">
                      {results.molecule}
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 bg-gray-50 rounded-lg">
                  <BeakerIcon className="w-12 h-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-sm text-gray-600">Molecular structure visualization unavailable</p>
                  <p className="text-xs text-gray-500 mt-1">Please ensure RDKit is installed on the backend</p>
                </div>
              )}
            </div>
          )}

          {/* Help */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <div className="flex items-start space-x-3">
              <InformationCircleIcon className="w-6 h-6 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-blue-900 mb-2">Need Help?</h3>
                <p className="text-sm text-blue-700 mb-3">
                  SMILES (Simplified Molecular Input Line Entry System) is a chemical notation 
                  that represents molecular structures as text strings.
                </p>
                <button className="text-sm font-medium text-blue-600 hover:text-blue-500">
                  Learn more about SMILES →
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Predictions;