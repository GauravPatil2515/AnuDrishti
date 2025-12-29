import React from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  BeakerIcon, 
  ChartBarIcon, 
  CpuChipIcon,
  ArrowRightIcon,
  ShieldCheckIcon,
  CheckCircleIcon,
  SparklesIcon,
  ClipboardDocumentCheckIcon
} from '@heroicons/react/24/outline';

const Home = () => {
  const navigate = useNavigate();

  const predictionModules = [
    {
      icon: ShieldCheckIcon,
      title: 'Clinical Toxicity',
      description: 'FDA clinical trial toxicity risk using ClinTox dataset',
      models: ['Clinical Toxicity'],
      property: 'Toxicity Assessment'
    },
    {
      icon: BeakerIcon,
      title: 'BBB Penetration (Distribution)',
      description: 'Blood-brain barrier permeability for CNS targeting',
      models: ['BBBP'],
      property: 'ADMET: Distribution'
    },
    {
      icon: ClipboardDocumentCheckIcon,
      title: 'Caco-2 Permeability (Absorption)',
      description: 'Intestinal epithelial permeability for oral bioavailability',
      models: ['Caco-2'],
      property: 'ADMET: Absorption'
    },
    {
      icon: CpuChipIcon,
      title: 'Hepatic Clearance (Metabolism)',
      description: 'HLM and intrinsic clearance for metabolic stability',
      models: ['HLM CLint', 'Intrinsic Clearance'],
      property: 'ADMET: Metabolism'
    }
  ];

  const workflow = [
    {
      step: '01',
      title: 'Input Data',
      description: 'Submit SMILES strings or batch upload CSV files with molecular structures'
    },
    {
      step: '02',
      title: 'Property Selection',
      description: 'Select individual ADMET properties or toxicity endpoints (each uses a dedicated trained model)'
    },
    {
      step: '03',
      title: 'AI Inference',
      description: 'State-of-the-art GIN-based models process molecular features'
    },
    {
      step: '04',
      title: 'Structured Output',
      description: 'Receive predictions with confidence scores and interpretations'
    }
  ];

  const benefits = [
    'Multi-model inference pipeline',
    'Research-grade accuracy',
    'Batch processing capabilities',
    'Exportable results (CSV/JSON)',
    'Explainable predictions',
    'API integration ready'
  ];

  return (
    <div className="min-h-screen bg-black">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-black/95 backdrop-blur-md border-b border-primary-500/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center shadow-lg shadow-primary-500/50">
                <BeakerIcon className="h-5 w-5 text-white" />
              </div>
              <span className="text-xl font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                DeNovo Platform
              </span>
            </div>
            
            <div className="flex items-center space-x-6">
              <button
                onClick={() => navigate('/app/dashboard')}
                className="text-gray-300 hover:text-primary-400 font-medium transition-colors"
              >
                Dashboard
              </button>
              <button
                onClick={() => navigate('/app/predictions')}
                className="px-6 py-2.5 bg-gradient-to-r from-primary-600 to-accent-600 text-white font-medium rounded-lg hover:from-primary-500 hover:to-accent-500 transition-all shadow-lg shadow-primary-500/30 hover:shadow-primary-500/50"
              >
                Start Prediction
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-24 px-4 sm:px-6 lg:px-8 bg-gradient-to-b from-black via-gray-950 to-black relative overflow-hidden min-h-[90vh] flex items-center">
        {/* Animated background gradients */}
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary-500/20 rounded-full filter blur-3xl opacity-20 animate-pulse"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-accent-500/20 rounded-full filter blur-3xl opacity-20 animate-pulse" style={{ animationDelay: '1s' }}></div>
          <div className="absolute top-1/2 left-1/2 w-64 h-64 bg-primary-400/10 rounded-full filter blur-2xl opacity-30 animate-pulse" style={{ animationDelay: '0.5s' }}></div>
        </div>
        
        {/* Grid pattern overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(6,182,212,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(6,182,212,0.03)_1px,transparent_1px)] bg-[size:64px_64px]"></div>
        
        <div className="max-w-7xl mx-auto relative z-10 w-full">
          <div className="text-center max-w-5xl mx-auto">
            {/* Badge */}
            <div className="inline-flex items-center px-5 py-2 mb-8 bg-gradient-to-r from-primary-500/20 to-accent-500/20 border border-primary-500/30 rounded-full backdrop-blur-sm hover:border-primary-500/50 transition-all duration-300 shadow-lg shadow-primary-500/10">
              <SparklesIcon className="h-5 w-5 text-primary-400 mr-2 animate-pulse" />
              <span className="text-sm font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent tracking-wide">
                AI-Powered Drug Discovery Platform
              </span>
            </div>
            
            {/* Main Heading */}
            <h1 className="text-5xl md:text-7xl font-bold text-white mb-8 leading-[1.1] tracking-tight">
              <span className="block bg-gradient-to-r from-primary-400 via-accent-400 to-primary-500 bg-clip-text text-transparent animate-gradient">
                AI-Powered Drug
              </span>
              <span className="block bg-gradient-to-r from-accent-400 via-primary-400 to-accent-500 bg-clip-text text-transparent mt-2 animate-gradient" style={{ animationDelay: '0.2s' }}>
                Toxicity & ADMET
              </span>
              <span className="block bg-gradient-to-r from-primary-500 via-accent-400 to-primary-400 bg-clip-text text-transparent mt-2 animate-gradient" style={{ animationDelay: '0.4s' }}>
                Prediction
              </span>
            </h1>
            
            {/* Subtitle */}
            <p className="text-lg md:text-xl text-gray-300 mb-12 leading-relaxed max-w-3xl mx-auto font-light">
              Predict drug properties using deep learning models. 
              <span className="block mt-2 text-gray-400">Accelerate your drug discovery with AI-powered predictions.</span>
            </p>
            
            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row items-center justify-center gap-5 mb-12">
              <button
                onClick={() => navigate('/app/predictions')}
                className="group relative px-10 py-5 bg-gradient-to-r from-primary-600 via-accent-600 to-primary-600 bg-[length:200%_100%] text-white font-bold text-lg rounded-xl hover:bg-[position:100%_0] transition-all duration-500 shadow-2xl shadow-primary-500/40 hover:shadow-primary-500/60 hover:scale-105 transform w-full sm:w-auto"
              >
                <span className="flex items-center justify-center">
                  Start Prediction
                  <ArrowRightIcon className="ml-3 h-6 w-6 group-hover:translate-x-2 transition-transform duration-300" />
                </span>
                <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-transparent via-white/20 to-transparent translate-x-[-200%] group-hover:translate-x-[200%] transition-transform duration-1000"></div>
              </button>
              
              <button
                onClick={() => navigate('/app/chat')}
                className="group px-10 py-5 bg-transparent text-white font-bold text-lg rounded-xl border-2 border-primary-500/50 hover:border-primary-400 hover:bg-primary-500/10 transition-all backdrop-blur-sm hover:scale-105 transform w-full sm:w-auto shadow-lg shadow-primary-500/20"
              >
                <span className="flex items-center justify-center">
                  <SparklesIcon className="mr-3 h-6 w-6 group-hover:rotate-180 transition-transform duration-500" />
                  AI Assistant
                </span>
              </button>
            </div>
            
            {/* Stats Bar */}
            <div className="flex flex-wrap items-center justify-center gap-8 pt-8 border-t border-primary-500/20">
              <div className="text-center">
                <div className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">6+</div>
                <div className="text-sm text-gray-400 mt-1">GIN Models</div>
              </div>
              <div className="h-8 w-px bg-primary-500/30"></div>
              <div className="text-center">
                <div className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">95%+</div>
                <div className="text-sm text-gray-400 mt-1">Accuracy</div>
              </div>
              <div className="h-8 w-px bg-primary-500/30"></div>
              <div className="text-center">
                <div className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">&lt;1s</div>
                <div className="text-sm text-gray-400 mt-1">Response Time</div>
              </div>
              <div className="h-8 w-px bg-primary-500/30"></div>
              <div className="text-center">
                <div className="text-3xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">API</div>
                <div className="text-sm text-gray-400 mt-1">Ready</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Supported Prediction Modules */}
      <section className="py-20 bg-gradient-to-b from-black to-gray-950">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-4">
              Independent Property Predictors
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Each property is predicted by a dedicated GIN model trained on specialized pharmaceutical datasets
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {predictionModules.map((module, index) => (
              <div
                key={index}
                className="group bg-gradient-to-br from-gray-900 to-black rounded-xl p-6 border border-primary-500/20 hover:border-primary-500/50 hover:shadow-2xl hover:shadow-primary-500/20 transition-all cursor-pointer relative overflow-hidden"
              >
                <div className="absolute inset-0 bg-gradient-to-br from-primary-500/5 to-accent-500/5 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="relative z-10">
                  <div className="h-12 w-12 rounded-lg bg-gradient-to-br from-primary-500/20 to-accent-500/20 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                    <module.icon className="h-6 w-6 text-primary-400" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {module.title}
                  </h3>
                  <p className="text-sm text-gray-400 mb-4">
                    {module.description}
                  </p>
                  <div className="mb-3">
                    <span className="text-xs font-semibold text-primary-400 uppercase tracking-wider">
                      {module.property}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {module.models.map((model, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 text-xs font-medium bg-gradient-to-r from-primary-500/20 to-accent-500/20 text-primary-300 rounded-md border border-primary-500/30"
                      >
                        {model}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-black">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-4">
              How It Works
            </h2>
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Simple four-step workflow from input to actionable insights
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {workflow.map((item, index) => (
              <div key={index} className="relative">
                <div className="flex flex-col items-center text-center">
                  <div className="h-16 w-16 rounded-full bg-gradient-to-br from-primary-500/20 to-accent-500/20 border-4 border-primary-500/30 flex items-center justify-center mb-4 shadow-lg shadow-primary-500/20">
                    <span className="text-2xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                      {item.step}
                    </span>
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-2">
                    {item.title}
                  </h3>
                  <p className="text-sm text-gray-400">
                    {item.description}
                  </p>
                </div>
                {index < workflow.length - 1 && (
                  <div className="hidden lg:block absolute top-8 left-full w-full h-0.5 bg-gradient-to-r from-primary-500/30 to-accent-500/30" style={{ width: 'calc(100% - 4rem)', marginLeft: '2rem' }} />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Why This Platform */}
      <section className="py-20 bg-gradient-to-b from-gray-950 to-black text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-6">
                Why Choose This Platform
              </h2>
              <p className="text-lg text-gray-300 mb-8">
                Built for pharmaceutical researchers, medicinal chemists, and computational biologists 
                who demand accuracy and reliability in their drug discovery workflows.
              </p>
              
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {benefits.map((benefit, index) => (
                  <div key={index} className="flex items-start space-x-3">
                    <CheckCircleIcon className="h-6 w-6 text-primary-400 flex-shrink-0 mt-0.5" />
                    <span className="text-gray-300">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="bg-gradient-to-br from-primary-500/10 to-accent-500/10 backdrop-blur-sm rounded-xl p-8 border border-primary-500/20">
              <div className="grid grid-cols-2 gap-6">
                <div className="text-center">
                  <div className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-2">5+</div>
                  <div className="text-sm text-gray-400">Trained Models</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-2">95%+</div>
                  <div className="text-sm text-gray-400">Accuracy</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-2">&lt;1s</div>
                  <div className="text-sm text-gray-400">Processing</div>
                </div>
                <div className="text-center">
                  <div className="text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-2">API</div>
                  <div className="text-sm text-gray-400">Ready</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-black relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-primary-500/10 via-accent-500/10 to-primary-500/10"></div>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <h2 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent mb-6">
            Ready to Accelerate Your Research?
          </h2>
          <p className="text-lg text-gray-400 mb-8">
            Start predicting drug toxicity and ADMET properties with our AI-powered platform
          </p>
          <button
            onClick={() => navigate('/app/predictions')}
            className="inline-flex items-center px-8 py-4 bg-gradient-to-r from-primary-600 to-accent-600 text-white font-semibold rounded-lg hover:from-primary-500 hover:to-accent-500 transition-all shadow-xl shadow-primary-500/30 hover:shadow-2xl hover:shadow-primary-500/50"
          >
            Get Started
            <ArrowRightIcon className="ml-2 h-5 w-5" />
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-black border-t border-primary-500/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center shadow-lg shadow-primary-500/50">
                <BeakerIcon className="h-4 w-4 text-white" />
              </div>
              <span className="text-lg font-semibold bg-gradient-to-r from-primary-400 to-accent-400 bg-clip-text text-transparent">
                DeNovo Platform
              </span>
            </div>
            <p className="text-sm text-gray-400">
              AI-Powered Drug Discovery Platform
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;