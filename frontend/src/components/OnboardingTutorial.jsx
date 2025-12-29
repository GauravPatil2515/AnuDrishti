import React, { useState, useEffect } from 'react';
import {
  XMarkIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  PlayIcon,
  CheckIcon
} from '@heroicons/react/24/outline';

const OnboardingTutorial = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const hasSeenTutorial = localStorage.getItem('medtoxai_tutorial_completed');
    if (!hasSeenTutorial) {
      setTimeout(() => setIsVisible(true), 1000);
    }
  }, []);

  const steps = [
    {
      title: "Welcome to DeNovo! 🧪",
      content: "Your advanced AI-powered drug toxicity prediction platform. Let's take a quick tour of the key features.",
      image: "🎯",
      highlight: null
    },
    {
      title: "Molecular Search Database 🔍",
      content: "Search from our comprehensive database of 40+ common drugs and molecules. Just type a drug name and we'll provide the SMILES string automatically.",
      image: "💊",
      highlight: "molecular-search"
    },
    {
      title: "SMILES Input & Visualization 🧬",
      content: "Enter SMILES notation directly or select from our database. See a real-time molecular structure visualization as you type.",
      image: "⚗️",
      highlight: "smiles-input"
    },
    {
      title: "Toxicity Prediction 🎯",
      content: "Get instant predictions across 5 toxicity endpoints with confidence scores and detailed analysis. Our AI models achieve 95%+ accuracy.",
      image: "📊",
      highlight: "prediction-results"
    },
    {
      title: "Analytics & History 📈",
      content: "Track your predictions, view usage analytics, and export results. All your data is stored locally for privacy.",
      image: "📋",
      highlight: "analytics-section"
    },
    {
      title: "Ready to Start! 🚀",
      content: "You're all set! Try predicting the toxicity of Aspirin or explore our molecular database. Need help? Check the help section anytime.",
      image: "✨",
      highlight: null
    }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      completeTutorial();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const completeTutorial = () => {
    localStorage.setItem('medtoxai_tutorial_completed', 'true');
    setIsVisible(false);
    if (onComplete) {
      onComplete();
    }
  };

  const skipTutorial = () => {
    completeTutorial();
  };

  if (!isVisible) return null;

  const currentStepData = steps[currentStep];

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full transform transition-all duration-300">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <div className="text-2xl">{currentStepData.image}</div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">
                {currentStepData.title}
              </h2>
              <p className="text-sm text-gray-500">
                Step {currentStep + 1} of {steps.length}
              </p>
            </div>
          </div>
          <button
            onClick={skipTutorial}
            className="text-gray-400 hover:text-gray-600 p-1"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="px-6 pt-4">
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-pink-500 to-purple-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
            />
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <p className="text-gray-600 leading-relaxed mb-6">
            {currentStepData.content}
          </p>

          {/* Interactive Elements */}
          {currentStep === 1 && (
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="text-sm font-medium text-gray-700 mb-2">Try it:</div>
              <input
                type="text"
                placeholder="Search for 'Aspirin' or 'Caffeine'..."
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm"
                disabled
              />
            </div>
          )}

          {currentStep === 2 && (
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="text-sm font-medium text-gray-700 mb-2">Example SMILES:</div>
              <code className="text-xs font-mono text-pink-600 bg-white px-2 py-1 rounded border">
                CC(=O)OC1=CC=CC=C1C(=O)O
              </code>
              <div className="text-xs text-gray-500 mt-1">Aspirin molecular structure</div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="bg-gradient-to-r from-green-50 to-blue-50 rounded-lg p-4 mb-4 border border-green-200">
              <div className="text-sm font-medium text-gray-700 mb-2">Sample Result:</div>
              <div className="text-lg font-bold text-green-600">✅ VERY LOW TOXICITY</div>
              <div className="text-sm text-gray-600">Confidence: High (95.2%)</div>
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 0}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-all duration-200 ${
              currentStep === 0
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
            }`}
          >
            <ChevronLeftIcon className="h-4 w-4" />
            <span className="text-sm">Previous</span>
          </button>

          <div className="flex space-x-2">
            {steps.map((_, index) => (
              <div
                key={index}
                className={`h-2 w-2 rounded-full transition-all duration-200 ${
                  index === currentStep
                    ? 'bg-pink-500'
                    : index < currentStep
                    ? 'bg-green-500'
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>

          <button
            onClick={handleNext}
            className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-pink-500 to-purple-600 text-white rounded-lg hover:shadow-lg transition-all duration-200"
          >
            {currentStep === steps.length - 1 ? (
              <>
                <CheckIcon className="h-4 w-4" />
                <span className="text-sm">Get Started</span>
              </>
            ) : (
              <>
                <span className="text-sm">Next</span>
                <ChevronRightIcon className="h-4 w-4" />
              </>
            )}
          </button>
        </div>

        {/* Skip Button */}
        <div className="px-6 pb-4">
          <button
            onClick={skipTutorial}
            className="w-full text-sm text-gray-500 hover:text-gray-700 transition-colors duration-200"
          >
            Skip tutorial
          </button>
        </div>
      </div>
    </div>
  );
};

// Quick Help Component for persistent help
const QuickHelp = () => {
  const [isOpen, setIsOpen] = useState(false);

  const helpItems = [
    {
      title: "SMILES Notation",
      content: "SMILES (Simplified Molecular Input Line Entry System) represents molecular structures as text strings. Example: CCO = Ethanol",
      icon: "🧬"
    },
    {
      title: "Toxicity Endpoints",
      content: "We analyze 5 key endpoints: NR-AR-LBD (Androgen Receptor), NR-AhR (Aryl Hydrocarbon), SR-MMP (Mitochondrial), NR-ER-LBD (Estrogen), NR-AR (Androgen)",
      icon: "🎯"
    },
    {
      title: "Confidence Scores",
      content: "Confidence indicates prediction reliability: Very High (90%+), High (80-90%), Medium (70-80%), Low (60-70%), Very Low (<60%)",
      icon: "📊"
    },
    {
      title: "Molecular Search",
      content: "Search our database of 40+ common drugs by name, category, or description. Includes pain relievers, antibiotics, cardiovascular drugs, and more.",
      icon: "🔍"
    }
  ];

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-6 right-6 bg-gradient-to-r from-pink-500 to-purple-600 text-white p-3 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 z-40"
      >
        <span className="text-lg">❓</span>
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto">
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Quick Help</h2>
              <button
                onClick={() => setIsOpen(false)}
                className="text-gray-400 hover:text-gray-600 p-1"
              >
                <XMarkIcon className="h-5 w-5" />
              </button>
            </div>
            
            <div className="p-6 space-y-4">
              {helpItems.map((item, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start space-x-3">
                    <span className="text-xl">{item.icon}</span>
                    <div>
                      <h3 className="font-medium text-gray-900 mb-1">{item.title}</h3>
                      <p className="text-sm text-gray-600">{item.content}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            
            <div className="p-6 border-t border-gray-200">
              <button
                onClick={() => {
                  localStorage.removeItem('medtoxai_tutorial_completed');
                  setIsOpen(false);
                  window.location.reload();
                }}
                className="w-full px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors duration-200"
              >
                Restart Tutorial
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export { OnboardingTutorial, QuickHelp };