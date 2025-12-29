import React, { useState, useEffect } from 'react';
import { 
  MagnifyingGlassIcon, 
  XMarkIcon, 
  CheckIcon,
  ClockIcon
} from '@heroicons/react/24/outline';

const MoleculeSearch = ({ onSelect }) => {
  const [search, setSearch] = useState('');
  const [suggestions, setSuggestions] = useState([]);

  const commonMolecules = [
    { name: 'Ethanol', smiles: 'CCO', description: 'Simple alcohol' },
    { name: 'Caffeine', smiles: 'CN1C=NC2=C1C(=O)N(C(=O)N2C)C', description: 'Stimulant compound' },
    { name: 'Aspirin', smiles: 'CC(=O)OC1=CC=CC=C1C(=O)O', description: 'Pain reliever' },
    { name: 'Ibuprofen', smiles: 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O', description: 'Anti-inflammatory' },
    { name: 'Penicillin', smiles: 'CC1([C@@H](N2[C@H](S1)[C@@H](C2=O)NC(=O)CC3=CC=CC=C3)C(=O)O)C', description: 'Antibiotic' },
    { name: 'Dopamine', smiles: 'C1=CC(=C(C=C1CCN)O)O', description: 'Neurotransmitter' },
    { name: 'Glucose', smiles: 'C([C@@H]1[C@H]([C@@H]([C@H]([C@H](O1)O)O)O)O)O', description: 'Simple sugar' },
    { name: 'Benzene', smiles: 'C1=CC=CC=C1', description: 'Aromatic hydrocarbon' }
  ];

  useEffect(() => {
    if (search.trim()) {
      const filtered = commonMolecules.filter(mol => 
        mol.name.toLowerCase().includes(search.toLowerCase()) ||
        mol.description.toLowerCase().includes(search.toLowerCase())
      );
      setSuggestions(filtered);
    } else {
      setSuggestions([]);
    }
  }, [search]);

  return (
    <div className="relative">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          type="text"
          placeholder="Search common molecules..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-10 pr-10 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-transparent text-sm"
        />
        {search && (
          <button
            onClick={() => {setSearch(''); setSuggestions([]);}}
            className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        )}
      </div>
      
      {suggestions.length > 0 && (
        <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          {suggestions.map((mol, index) => (
            <button
              key={index}
              onClick={() => {
                onSelect(mol.smiles);
                setSearch('');
                setSuggestions([]);
              }}
              className="w-full px-4 py-3 text-left hover:bg-gray-50 border-b border-gray-100 last:border-b-0"
            >
              <div className="font-medium text-gray-900">{mol.name}</div>
              <div className="text-xs text-gray-500 mt-1">{mol.description}</div>
              <div className="text-xs font-mono text-pink-600 mt-1 truncate">{mol.smiles}</div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

const PredictionHistory = ({ history, onRerun }) => {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-700">Recent Predictions</h3>
      {history.length === 0 ? (
        <p className="text-sm text-gray-500">No recent predictions</p>
      ) : (
        <div className="space-y-2">
          {history.slice(0, 5).map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div className="flex-1 min-w-0">
                <div className="text-xs font-mono text-gray-600 truncate">{item.smiles}</div>
                <div className="text-xs text-gray-500">{item.timestamp}</div>
              </div>
              <button
                onClick={() => onRerun(item.smiles)}
                className="ml-2 p-1 text-pink-600 hover:text-pink-700"
              >
                <ClockIcon className="h-4 w-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export { MoleculeSearch, PredictionHistory };