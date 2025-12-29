import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';

// Comprehensive molecular database
const MOLECULAR_DATABASE = [
  // Pain Relievers
  { name: 'Aspirin', smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O', category: 'Pain Relievers', description: 'Anti-inflammatory, reduces fever and pain' },
  { name: 'Ibuprofen', smiles: 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O', category: 'Pain Relievers', description: 'Nonsteroidal anti-inflammatory drug (NSAID)' },
  { name: 'Acetaminophen', smiles: 'CC(=O)NC1=CC=C(C=C1)O', category: 'Pain Relievers', description: 'Pain reliever and fever reducer' },
  { name: 'Naproxen', smiles: 'CC(C1=CC2=C(C=C1)C=C(C=C2)C(C)C(=O)O)C(=O)O', category: 'Pain Relievers', description: 'Long-acting NSAID' },
  
  // Antibiotics
  { name: 'Penicillin', smiles: 'CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C', category: 'Antibiotics', description: 'Beta-lactam antibiotic' },
  { name: 'Amoxicillin', smiles: 'CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)[C@@H](C3=CC=C(C=C3)O)N)C(=O)O)C', category: 'Antibiotics', description: 'Broad-spectrum penicillin antibiotic' },
  { name: 'Ciprofloxacin', smiles: 'C1CC1N2C=C(C(=O)C3=CC(=C(C=C32)N4CCNCC4)F)C(=O)O', category: 'Antibiotics', description: 'Fluoroquinolone antibiotic' },
  
  // Cardiovascular
  { name: 'Lisinopril', smiles: 'CCCCN1CCCC1C(=O)N[C@@H](CCCNC(=N)N)C(=O)N2CCC[C@H]2C(=O)O', category: 'Cardiovascular', description: 'ACE inhibitor for blood pressure' },
  { name: 'Atorvastatin', smiles: 'CC(C)C1=C(C(=C(N1CC[C@H](C[C@H](CC(=O)O)O)O)C2=CC=C(C=C2)F)C3=CC=CC=C3)C(=O)NC4=CC=CC=C4', category: 'Cardiovascular', description: 'Statin for cholesterol management' },
  { name: 'Metoprolol', smiles: 'CC(C)NCC(COC1=CC=C(C=C1)CC(=O)C)O', category: 'Cardiovascular', description: 'Beta-blocker for heart conditions' },
  
  // Mental Health
  { name: 'Sertraline', smiles: 'CN[C@H]1CCC2=CC=CC=C2C1C3=CC=C(C=C3)Cl', category: 'Mental Health', description: 'SSRI antidepressant' },
  { name: 'Fluoxetine', smiles: 'CNCCC(C1=CC=CC=C1)OC2=CC=C(C=C2)C(F)(F)F', category: 'Mental Health', description: 'SSRI antidepressant (Prozac)' },
  { name: 'Lorazepam', smiles: 'CC1=NN=C2CN=C(C3=C2C=C(C=C3Cl)Cl)C4=CC=CC=C4Cl', category: 'Mental Health', description: 'Benzodiazepine for anxiety' },
  
  // Diabetes
  { name: 'Metformin', smiles: 'CN(C)C(=N)NC(=N)N', category: 'Diabetes', description: 'First-line diabetes medication' },
  { name: 'Insulin Glargine', smiles: 'CC[C@H](C)[C@H]1NC(=O)[C@H](CC2=CC=CC=C2)NC(=O)[C@H](CC(C)C)NC(=O)[C@H](CCCNC(=N)N)NC(=O)[C@H](CC(=O)N)NC(=O)[C@H](CC(=O)O)NC1=O', category: 'Diabetes', description: 'Long-acting insulin analog' },
  
  // Common Molecules
  { name: 'Ethanol', smiles: 'CCO', category: 'Common', description: 'Simple alcohol' },
  { name: 'Caffeine', smiles: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', category: 'Common', description: 'Central nervous system stimulant' },
  { name: 'Nicotine', smiles: 'CN1CCCC1C2=CN=CC=C2', category: 'Common', description: 'Alkaloid found in tobacco' },
  { name: 'Glucose', smiles: 'C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O', category: 'Common', description: 'Simple sugar, primary energy source' },
  
  // Cancer Treatment
  { name: 'Doxorubicin', smiles: 'COC1=C(C=C2C(=C1)C(=O)C3=C(C2=O)C=CC=C3O)OCC4CC(C(C(O4)O)N)O', category: 'Cancer Treatment', description: 'Anthracycline chemotherapy drug' },
  { name: 'Tamoxifen', smiles: 'CCC(=C(C1=CC=CC=C1)C2=CC=C(C=C2)OCCN(C)C)C3=CC=CC=C3', category: 'Cancer Treatment', description: 'Selective estrogen receptor modulator' },
  
  // Neurotransmitters
  { name: 'Dopamine', smiles: 'C1=CC(=C(C=C1CCN)O)O', category: 'Neurotransmitters', description: 'Neurotransmitter involved in reward and motivation' },
  { name: 'Serotonin', smiles: 'C1=CC2=C(C=C1O)C(=CN2)CCN', category: 'Neurotransmitters', description: 'Neurotransmitter regulating mood' },
  { name: 'GABA', smiles: 'C(CC(=O)O)CN', category: 'Neurotransmitters', description: 'Primary inhibitory neurotransmitter' },
  
  // Vitamins
  { name: 'Vitamin C', smiles: 'C([C@H]([C@H]([C@@H](C(=O)O)O)O)O)O', category: 'Vitamins', description: 'Essential vitamin, antioxidant' },
  { name: 'Vitamin B12', smiles: 'CC1=CC2=C(C=C1C)N(C=N2)[C@@H]3[C@@H]([C@@H]([C@H](O3)CO)OP(=O)([O-])OC(C)C)O', category: 'Vitamins', description: 'Essential for nerve function and red blood cell formation' },
  
  // Hormones
  { name: 'Testosterone', smiles: 'C[C@]12CC[C@H]3[C@H]([C@@H]1CC[C@@H]2O)CCC4=CC(=O)CC[C@]34C', category: 'Hormones', description: 'Primary male sex hormone' },
  { name: 'Estradiol', smiles: 'C[C@]12CC[C@H]3[C@H]([C@@H]1CC[C@@H]2O)CCC4=C3C=CC(=C4)O', category: 'Hormones', description: 'Primary female sex hormone' },
  { name: 'Cortisol', smiles: 'C[C@]12CC[C@H]3[C@H]([C@@H]1CC[C@@H]2C(=O)CO)CCC4=CC(=O)CC[C@]34C', category: 'Hormones', description: 'Stress hormone produced by adrenal glands' },
  
  // Recreational/Controlled
  { name: 'THC', smiles: 'CCCCCC1=CC2=C(C3C=C(CCC3C(O2)(C)C)C)C(=C1)O', category: 'Controlled', description: 'Psychoactive compound in cannabis' },
  { name: 'Morphine', smiles: 'CN1CC[C@]23[C@@H]4[C@H](CC[C@]2([C@H]1CC5=C3C(=C(C=C5)O)O)O)[C@H](C=C4)O', category: 'Controlled', description: 'Opioid pain medication' },
  
  // Simple Test Molecules
  { name: 'Benzene', smiles: 'C1=CC=CC=C1', category: 'Test Molecules', description: 'Simple aromatic hydrocarbon' },
  { name: 'Methane', smiles: 'C', category: 'Test Molecules', description: 'Simplest hydrocarbon' },
  { name: 'Water', smiles: 'O', category: 'Test Molecules', description: 'Essential for life' },
];

const MolecularSearch = ({ onSelect, currentSmiles }) => {
  const [search, setSearch] = useState('');
  const [suggestions, setSuggestions] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const categories = ['All', ...new Set(MOLECULAR_DATABASE.map(mol => mol.category))];

  useEffect(() => {
    if (search.trim()) {
      let filtered = MOLECULAR_DATABASE.filter(mol => 
        mol.name.toLowerCase().includes(search.toLowerCase()) ||
        mol.description.toLowerCase().includes(search.toLowerCase()) ||
        mol.category.toLowerCase().includes(search.toLowerCase())
      );

      if (selectedCategory !== 'All') {
        filtered = filtered.filter(mol => mol.category === selectedCategory);
      }

      setSuggestions(filtered.slice(0, 10));
    } else {
      const categoryFiltered = selectedCategory === 'All' 
        ? MOLECULAR_DATABASE.slice(0, 8)
        : MOLECULAR_DATABASE.filter(mol => mol.category === selectedCategory).slice(0, 8);
      setSuggestions(categoryFiltered);
    }
  }, [search, selectedCategory]);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-700">Molecular Search Database</h3>
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="text-sm text-pink-600 hover:text-pink-700"
        >
          {showAdvanced ? 'Simple' : 'Advanced'} Search
        </button>
      </div>

      <div className="space-y-3">
        <input
          type="text"
          placeholder="Search by drug name, category, or description..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-pink-500 focus:border-transparent text-sm"
        />

        {showAdvanced && (
          <div className="flex flex-wrap gap-2">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`px-3 py-1 rounded-full text-xs font-medium transition-all duration-200 ${
                  selectedCategory === category
                    ? 'bg-pink-100 text-pink-700 border border-pink-300'
                    : 'bg-gray-100 text-gray-600 border border-gray-200 hover:bg-gray-200'
                }`}
              >
                {category}
              </button>
            ))}
          </div>
        )}
      </div>

      {suggestions.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-h-80 overflow-y-auto">
          {suggestions.map((mol, index) => (
            <button
              key={index}
              onClick={() => {
                onSelect(mol.smiles, mol.name);
                setSearch('');
              }}
              className={`text-left p-4 rounded-lg border transition-all duration-200 hover:shadow-md ${
                currentSmiles === mol.smiles
                  ? 'border-pink-300 bg-pink-50'
                  : 'border-gray-200 bg-white hover:border-pink-200'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="font-medium text-gray-900 text-sm">{mol.name}</div>
                  <div className="text-xs text-pink-600 mt-1">{mol.category}</div>
                  <div className="text-xs text-gray-500 mt-1 line-clamp-2">{mol.description}</div>
                  <div className="text-xs font-mono text-gray-400 mt-2 truncate">
                    {mol.smiles}
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      )}

      {search && suggestions.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <p className="text-sm">No molecules found matching "{search}"</p>
          <p className="text-xs mt-1">Try a different search term or category</p>
        </div>
      )}
    </div>
  );
};

// Prediction History Storage
const usePredictionHistory = () => {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    const savedHistory = localStorage.getItem('medtoxai_prediction_history');
    if (savedHistory) {
      setHistory(JSON.parse(savedHistory));
    }
  }, []);

  const addPrediction = (prediction) => {
    const newPrediction = {
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      ...prediction
    };

    const updatedHistory = [newPrediction, ...history.slice(0, 49)]; // Keep last 50
    setHistory(updatedHistory);
    localStorage.setItem('medtoxai_prediction_history', JSON.stringify(updatedHistory));

    // Update analytics
    const analytics = JSON.parse(localStorage.getItem('medtoxai_analytics') || '{}');
    analytics.totalPredictions = (analytics.totalPredictions || 0) + 1;
    if (prediction.overall_toxicity?.includes('HIGH')) {
      analytics.toxicCompounds = (analytics.toxicCompounds || 0) + 1;
    } else {
      analytics.safeCompounds = (analytics.safeCompounds || 0) + 1;
    }
    localStorage.setItem('medtoxai_analytics', JSON.stringify(analytics));

    // Update activity log
    const activity = JSON.parse(localStorage.getItem('drugtox_activity') || '[]');
    activity.unshift({
      compound: prediction.molecule || prediction.smiles,
      result: prediction.overall_toxicity,
      timestamp: new Date().toLocaleString()
    });
    localStorage.setItem('drugtox_activity', JSON.stringify(activity.slice(0, 20)));
  };

  const clearHistory = () => {
    setHistory([]);
    localStorage.removeItem('drugtox_prediction_history');
  };

  return { history, addPrediction, clearHistory };
};

// Export functionality
const useExport = () => {
  const exportToCSV = (data, filename = 'drugtox_predictions.csv') => {
    if (!Array.isArray(data) || data.length === 0) return;

    const headers = ['Molecule', 'SMILES', 'Overall Toxicity', 'Confidence', 'Toxic Endpoints', 'Timestamp'];
    const csvContent = [
      headers.join(','),
      ...data.map(item => [
        `"${item.molecule || item.smiles}"`,
        `"${item.smiles}"`,
        `"${item.overall_toxicity || 'N/A'}"`,
        `"${item.confidence || 'N/A'}"`,
        `"${item.toxic_endpoints || 'N/A'}"`,
        `"${new Date(item.timestamp).toLocaleString()}"`
      ].join(','))
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const exportToJSON = (data, filename = 'drugtox_predictions.json') => {
    const jsonContent = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return { exportToCSV, exportToJSON };
};

export { MolecularSearch, usePredictionHistory, useExport, MOLECULAR_DATABASE };