import React, { useState, useRef, useEffect } from 'react';
import {
  PaperAirplaneIcon,
  SparklesIcon,
  UserIcon,
  CpuChipIcon,
  XMarkIcon,
  ChatBubbleLeftRightIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

const ChemBioBot = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [configStatus, setConfigStatus] = useState(null);
  const [showConfigHelp, setShowConfigHelp] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: "Hello! I'm your **ChemBio AI Assistant** 🧬\n\nI specialize in providing detailed, scientific information about:\n\n💊 **Drug Safety & Toxicology**\n• Toxicity endpoints (NR-AR-LBD, NR-AhR, SR-MMP, etc.)\n• Safety testing protocols\n• Risk assessment methods\n\n⚗️ **Chemical & Molecular Science**\n• SMILES notation & molecular structures\n• Drug mechanisms of action\n• QSAR modeling & computational chemistry\n\n🔬 **Pharmaceutical Development**\n• ADME properties\n• Drug metabolism\n• Clinical trial design\n\nAsk me anything from basic concepts to advanced topics! 🚀",
      timestamp: new Date().toISOString()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Check configuration status on mount
  useEffect(() => {
    const checkConfig = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/config/status');
        if (response.ok) {
          const data = await response.json();
          setConfigStatus(data);
          // Show config help if API key is not set
          if (!data.groq?.api_key_set) {
            setShowConfigHelp(true);
          }
        }
      } catch (error) {
        console.error('Failed to check config status:', error);
      }
    };
    checkConfig();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Comprehensive knowledge base for chemistry/biology questions
  const knowledgeBase = {
    'drug safety': {
      definition: 'Drug safety testing is a comprehensive process to evaluate the potential harmful effects of pharmaceutical compounds before and after market approval.',
      process: 'The process includes: 1) Preclinical testing (in vitro and animal studies), 2) Clinical trials (Phase I-III), 3) Regulatory review, 4) Post-market surveillance.',
      endpoints: 'Key safety endpoints include acute toxicity, chronic toxicity, carcinogenicity, reproductive toxicity, genotoxicity, and organ-specific toxicities.',
      regulations: 'Governed by FDA, EMA, and other regulatory agencies following ICH guidelines for safety assessment.',
      technologies: 'Modern approaches include computational toxicology, organ-on-chip models, and AI-powered prediction platforms like DeNovo.'
    },
    'toxicity testing': {
      definition: 'Systematic evaluation of adverse effects caused by chemical exposure to living organisms.',
      types: 'Types include acute (single dose), subacute (repeated dose 14-28 days), subchronic (90 days), and chronic (>6 months) toxicity studies.',
      endpoints: 'Major endpoints: LD50, NOAEL, LOAEL, carcinogenicity, mutagenicity, reproductive toxicity, developmental toxicity.',
      methods: 'In vitro assays, animal models, computational models, and alternative methods following 3Rs principle (Replace, Reduce, Refine).'
    },
    'nr-ar-lbd': {
      definition: 'Nuclear Receptor Androgen Receptor Ligand Binding Domain - assesses if compounds bind to androgen receptor.',
      mechanism: 'Compounds binding to AR-LBD can activate or block androgen signaling pathways affecting male sexual development.',
      toxicity: 'Unwanted AR activation can cause endocrine disruption, reproductive toxicity, and hormonal imbalances.',
      clinical: 'Important for drug safety, especially for compounds that might interfere with hormonal systems.'
    },
    'nr-ahr': {
      definition: 'Nuclear Receptor Aryl Hydrocarbon Receptor - detects compounds that activate the AhR pathway.',
      mechanism: 'AhR mediates responses to environmental pollutants and regulates xenobiotic metabolism.',
      toxicity: 'AhR activation can lead to enzyme induction, immunotoxicity, and developmental abnormalities.',
      examples: 'Dioxins, PAHs, and some pharmaceuticals are known AhR activators.'
    },
    'sr-mmp': {
      definition: 'Stress Response Mitochondrial Membrane Potential - measures mitochondrial dysfunction.',
      mechanism: 'Assesses compounds that disrupt mitochondrial membrane potential, affecting cellular energy production.',
      toxicity: 'Mitochondrial dysfunction can lead to cell death, organ failure, and metabolic disorders.',
      organs: 'Particularly important for liver, heart, and muscle toxicity assessment.'
    },
    'nr-er-lbd': {
      definition: 'Nuclear Receptor Estrogen Receptor Ligand Binding Domain - evaluates estrogen receptor binding.',
      mechanism: 'Compounds binding to ER-LBD can mimic or block estrogen effects in the body.',
      toxicity: 'Can cause endocrine disruption, reproductive issues, and increased cancer risk.',
      applications: 'Critical for evaluating environmental estrogens and pharmaceutical safety.'
    },
    'aspirin': {
      mechanism: 'Aspirin irreversibly inhibits cyclooxygenase (COX) enzymes by acetylating Ser530 in COX-1 and Ser516 in COX-2, reducing prostaglandin synthesis.',
      pharmacology: 'Low doses (75-100mg) provide antiplatelet effects; higher doses (300-1000mg) have anti-inflammatory and analgesic effects.',
      sideEffects: 'GI irritation, increased bleeding risk, tinnitus at high doses, Reye\'s syndrome in children with viral infections.',
      toxicity: 'LD50 ~200mg/kg in rats. Salicylate poisoning causes tinnitus, confusion, hyperventilation, and metabolic acidosis.'
    },
    'ibuprofen': {
      mechanism: 'Non-selective NSAID that reversibly inhibits both COX-1 and COX-2 through competitive binding to the active site.',
      pharmacology: 'Peak plasma levels in 1-2 hours, half-life 2-4 hours, extensively protein bound (>99%).',
      sideEffects: 'GI upset, cardiovascular risk with long-term use, nephrotoxicity, CNS effects (headache, dizziness).',
      toxicity: 'Generally well-tolerated. Overdose can cause kidney damage, GI bleeding, and CNS depression.'
    },
    'caffeine': {
      mechanism: 'Adenosine receptor antagonist (A1, A2A, A2B, A3) that prevents adenosine-mediated sedation and promotes alertness.',
      pharmacology: 'Rapidly absorbed, peak levels in 30-60 minutes, half-life 3-5 hours, metabolized by CYP1A2.',
      sideEffects: 'Insomnia, jitteriness, increased heart rate, anxiety, dependency with regular use >400mg/day.',
      toxicity: 'LD50 ~192mg/kg. Acute toxicity >1g can cause seizures, arrhythmias, and hyperthermia.'
    },
    'smiles': {
      definition: 'Simplified Molecular Input Line Entry System - ASCII string notation for chemical structures.',
      rules: 'Atoms as symbols, bonds as connections, branches in parentheses, rings as numbers, aromatic lowercase.',
      examples: 'CCO (ethanol), CC(=O)OC1=CC=CC=C1C(=O)O (aspirin), c1ccccc1 (benzene), CC(C)CC1=CC=C(C=C1)C(C)C(=O)O (ibuprofen)',
      applications: 'Chemical databases, computational chemistry, drug discovery, QSAR modeling, and AI toxicity prediction.'
    },
    'qsar': {
      definition: 'Quantitative Structure-Activity Relationship - mathematical models relating chemical structure to biological activity.',
      principle: 'Similar chemical structures tend to have similar biological activities and properties.',
      descriptors: 'Molecular descriptors include topological, electronic, geometric, and physicochemical properties.',
      applications: 'Drug discovery, toxicity prediction, environmental risk assessment, and lead optimization.'
    },
    'pharmacokinetics': {
      definition: 'Study of drug absorption, distribution, metabolism, and excretion (ADME) in the body.',
      adme: 'Absorption (uptake), Distribution (tissue distribution), Metabolism (biotransformation), Excretion (elimination).',
      parameters: 'Key parameters: bioavailability, half-life, clearance, volume of distribution, protein binding.',
      clinical: 'Essential for dose optimization, drug interactions, and personalized medicine.'
    },
    'drug metabolism': {
      definition: 'Biochemical modification of drugs by living organisms, primarily in the liver.',
      phases: 'Phase I (oxidation, reduction, hydrolysis by CYPs), Phase II (conjugation reactions), Phase III (transport).',
      enzymes: 'Major enzymes: CYP3A4, CYP2D6, CYP2C9, CYP2C19, UGTs, SULTs, GSTs.',
      interactions: 'Drug-drug interactions often involve CYP enzyme inhibition or induction.'
    }
  };

  const getAIResponse = async (message) => {
    try {
      const response = await fetch('http://localhost:5000/api/ai/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      if (data.response && data.response.length > 50) {
        return data.response;
      }
      throw new Error('Empty or invalid AI response');
      
    } catch (error) {
      console.error('AI Chat Error:', error);
      
      // Enhanced fallback to comprehensive knowledge base
      const lowerMessage = message.toLowerCase();
      
      // Check for specific topics with detailed responses
      for (const [key, knowledge] of Object.entries(knowledgeBase)) {
        if (lowerMessage.includes(key.replace('-', ' ')) || lowerMessage.includes(key)) {
          
          // Drug safety and toxicity testing
          if (lowerMessage.includes('safety') || lowerMessage.includes('testing')) {
            return `**Drug Safety Testing** 🧪\n\n${knowledge.definition}\n\n**Process:** ${knowledge.process || knowledge.types || knowledge.mechanism}\n\n**Key Points:** ${knowledge.endpoints || knowledge.sideEffects || knowledge.toxicity}\n\n**Regulations:** ${knowledge.regulations || knowledge.clinical || knowledge.applications || 'Regulated by FDA, EMA following international guidelines'}`;
          }
          
          // Mechanism queries
          if (lowerMessage.includes('mechanism') || lowerMessage.includes('work') || lowerMessage.includes('function')) {
            return `**How ${key.toUpperCase()} Works** ⚙️\n\n${knowledge.mechanism || knowledge.definition}\n\n${knowledge.pharmacology ? `**Pharmacology:** ${knowledge.pharmacology}\n\n` : ''}**Clinical Significance:** ${knowledge.clinical || knowledge.applications || knowledge.toxicity}`;
          }
          
          // Toxicity and safety queries
          if (lowerMessage.includes('toxic') || lowerMessage.includes('safe') || lowerMessage.includes('danger')) {
            return `**${key.toUpperCase()} Safety Profile** ⚠️\n\n${knowledge.toxicity || knowledge.definition}\n\n${knowledge.sideEffects ? `**Side Effects:** ${knowledge.sideEffects}\n\n` : ''}**Important Notes:** ${knowledge.clinical || knowledge.endpoints || 'Always consult healthcare professionals for specific medical advice'}`;
          }
          
          // Examples and applications
          if (lowerMessage.includes('example') || lowerMessage.includes('application') || lowerMessage.includes('use')) {
            return `**${key.toUpperCase()} Examples & Applications** 📋\n\n${knowledge.examples || knowledge.applications || knowledge.definition}\n\n**Additional Info:** ${knowledge.rules || knowledge.usage || knowledge.clinical || 'Used in pharmaceutical research and development'}`;
          }
          
          // Default comprehensive response
          return `**About ${key.toUpperCase()}** 📚\n\n${knowledge.definition}\n\n${knowledge.mechanism ? `**Mechanism:** ${knowledge.mechanism}\n\n` : ''}${knowledge.applications ? `**Applications:** ${knowledge.applications}\n\n` : ''}**Key Information:** ${knowledge.endpoints || knowledge.sideEffects || knowledge.toxicity || knowledge.examples || 'Important topic in chemistry and biology'}`;
        }
      }

      // Enhanced general topic responses
      if (lowerMessage.includes('drug safety') || lowerMessage.includes('pharmaceutical testing')) {
        return `**Drug Safety Testing Overview** 🧪\n\nDrug safety testing is a comprehensive, multi-stage process:\n\n**1. Preclinical Testing:**\n• In vitro assays (cell-based)\n• Animal studies (toxicology)\n• ADME studies\n\n**2. Clinical Trials:**\n• Phase I: Safety in humans\n• Phase II: Efficacy studies\n• Phase III: Large-scale trials\n\n**3. Regulatory Review:**\n• FDA/EMA evaluation\n• Risk-benefit analysis\n\n**4. Post-Market Surveillance:**\n• Ongoing safety monitoring\n• Adverse event reporting\n\n**Modern Approaches:**\n• Computational toxicology\n• AI-powered prediction (like DeNovo)\n• Organ-on-chip technologies\n• Alternative testing methods (3Rs principle)`;
      }

      if (lowerMessage.includes('toxicity endpoint') || lowerMessage.includes('tox screen')) {
        return `**Toxicity Endpoints in Drug Development** 📊\n\nToxicity endpoints are specific biological effects measured to assess drug safety:\n\n**Primary Endpoints:**\n• **NR-AR-LBD:** Androgen receptor binding\n• **NR-AhR:** Aryl hydrocarbon receptor activation\n• **SR-MMP:** Mitochondrial membrane potential\n• **NR-ER-LBD:** Estrogen receptor binding\n• **NR-AR:** Nuclear receptor assays\n\n**Organ-Specific Toxicity:**\n• Hepatotoxicity (liver damage)\n• Nephrotoxicity (kidney damage)\n• Cardiotoxicity (heart effects)\n• Neurotoxicity (nervous system)\n\n**Assessment Methods:**\n• In vitro cell assays\n• Computational prediction\n• Animal testing\n• Human clinical trials`;
      }

      if (lowerMessage.includes('hello') || lowerMessage.includes('hi')) {
        return "Hello! 👋 I'm your ChemBio AI assistant, ready to help with detailed information about:\n\n🧬 **Molecular Biology**\n💊 **Drug Mechanisms & Safety**\n🔬 **Toxicology & Risk Assessment**\n⚗️ **Chemical Structures & Properties**\n📊 **QSAR & Computational Chemistry**\n🧪 **Pharmaceutical Development**\n\nWhat specific topic interests you?";
      }
      
      if (lowerMessage.includes('help')) {
        return `**I can provide detailed information on:** 📚\n\n🧬 **Molecular Topics:**\n• Protein structure & function\n• DNA, RNA, and genetics\n• Enzyme kinetics & metabolism\n\n💊 **Pharmacology:**\n• Drug mechanisms of action\n• ADME properties\n• Drug-drug interactions\n\n🔬 **Toxicology:**\n• Safety assessment endpoints\n• Risk evaluation methods\n• Regulatory guidelines\n\n⚗️ **Chemistry:**\n• SMILES notation\n• Chemical properties\n• Structure-activity relationships\n\nJust ask about any specific topic!`;
      }

      if (lowerMessage.includes('computational') || lowerMessage.includes('ai') || lowerMessage.includes('prediction')) {
        return `**Computational Chemistry & AI in Drug Discovery** 🤖\n\n**AI Applications:**\n• Toxicity prediction (like DeNovo)\n• Drug-target interaction modeling\n• ADME property prediction\n• Lead optimization\n\n**Methods:**\n• Machine learning algorithms\n• Deep neural networks\n• QSAR modeling\n• Molecular dynamics simulations\n\n**Benefits:**\n• Faster screening\n• Reduced animal testing\n• Cost-effective development\n• Better success rates\n\n**Our Platform:** DeNovo predicts toxicity across 5 key endpoints using advanced ML models trained on comprehensive datasets.`;
      }

      // Default enhanced response
      return `I'd be happy to help with that topic! 🧬\n\nI specialize in:\n• **Drug Safety & Toxicology**\n• **Molecular Mechanisms**\n• **Chemical Structures & Properties**\n• **Pharmacology & Therapeutics**\n• **Computational Chemistry**\n\nCould you be more specific? For example:\n• "How does aspirin work?"\n• "Explain the NR-AR-LBD endpoint"\n• "What is drug safety testing?"\n• "Tell me about SMILES notation"\n\nI'm here to provide detailed, scientific explanations! 🔬`;
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsTyping(true);

    // Simulate thinking time
    setTimeout(async () => {
      const response = await getAIResponse(inputMessage);
      
      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: response,
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsTyping(false);
    }, 1000 + Math.random() * 2000); // 1-3 seconds thinking time
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const quickQuestions = [
    "Explain drug safety testing",
    "How does toxicity prediction work?",
    "What are the 5 toxicity endpoints?",
    "Tell me about SMILES notation",
    "How do NSAIDs like aspirin work?",
    "What is QSAR modeling?",
    "Explain the NR-AR-LBD endpoint",
    "How are drugs metabolized?",
    "What is computational toxicology?",
    "Tell me about drug-drug interactions"
  ];

  return (
    <>
      {/* Chat Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-20 right-6 bg-gradient-to-r from-blue-500 to-purple-600 text-white p-3 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 z-40"
      >
        <ChatBubbleLeftRightIcon className="h-6 w-6" />
        {showConfigHelp && (
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-yellow-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-yellow-500"></span>
          </span>
        )}
      </button>

      {/* Chat Window */}
      {isOpen && (
        <div className="fixed bottom-6 right-6 w-96 h-[500px] bg-white rounded-2xl shadow-2xl border border-gray-200 flex flex-col z-50">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-t-2xl">
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white/20 rounded-full">
                <SparklesIcon className="h-5 w-5" />
              </div>
              <div>
                <h3 className="font-semibold">ChemBio AI Assistant</h3>
                <p className="text-xs opacity-90">Powered by Groq LLaMA3</p>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 hover:bg-white/20 rounded-full transition-colors duration-200"
            >
              <XMarkIcon className="h-5 w-5" />
            </button>
          </div>

          {/* Configuration Help Banner */}
          {showConfigHelp && configStatus && !configStatus.groq?.api_key_set && (
            <div className="p-3 bg-yellow-50 border-b border-yellow-200">
              <div className="flex items-start space-x-2">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <div className="flex-1 text-xs">
                  <p className="font-semibold text-yellow-800 mb-1">Groq API Key Required</p>
                  <p className="text-yellow-700 mb-2">
                    To use the AI assistant, you need to configure your Groq API key.
                  </p>
                  <button
                    onClick={() => {
                      const instructions = configStatus.groq?.instructions;
                      if (instructions) {
                        const msg = `📋 **Groq API Key Setup Instructions**\n\n**File Location:** \`${instructions.file}\`\n\n**Steps:**\n${instructions.steps.join('\n')}\n\n**Example:**\n\`\`\`\n${instructions.example}\n\`\`\`\n\nOnce configured, restart the backend server and I'll be fully operational! 🚀`;
                        
                        setMessages(prev => [...prev, {
                          id: Date.now(),
                          role: 'assistant',
                          content: msg,
                          timestamp: new Date().toISOString()
                        }]);
                        setShowConfigHelp(false);
                      }
                    }}
                    className="text-yellow-700 hover:text-yellow-900 font-medium underline"
                  >
                    Show setup instructions
                  </button>
                </div>
                <button
                  onClick={() => setShowConfigHelp(false)}
                  className="text-yellow-600 hover:text-yellow-800"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`flex items-start space-x-2 max-w-[80%] ${
                  message.role === 'user' ? 'flex-row-reverse space-x-reverse' : ''
                }`}>
                  <div className={`p-2 rounded-full ${
                    message.role === 'user' 
                      ? 'bg-blue-100' 
                      : 'bg-gradient-to-r from-purple-100 to-blue-100'
                  }`}>
                    {message.role === 'user' ? (
                      <UserIcon className="h-4 w-4 text-blue-600" />
                    ) : (
                      <CpuChipIcon className="h-4 w-4 text-purple-600" />
                    )}
                  </div>
                  <div className={`p-3 rounded-2xl ${
                    message.role === 'user'
                      ? 'bg-blue-500 text-white rounded-br-none'
                      : 'bg-gray-100 text-gray-800 rounded-bl-none'
                  }`}>
                    <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                  </div>
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="flex justify-start">
                <div className="flex items-start space-x-2 max-w-[80%]">
                  <div className="p-2 rounded-full bg-gradient-to-r from-purple-100 to-blue-100">
                    <CpuChipIcon className="h-4 w-4 text-purple-600" />
                  </div>
                  <div className="p-3 rounded-2xl bg-gray-100 text-gray-800 rounded-bl-none">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0ms'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '150ms'}}></div>
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '300ms'}}></div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Questions */}
          {messages.length === 1 && (
            <div className="px-4 pb-2">
              <p className="text-xs text-gray-500 mb-2">Quick questions:</p>
              <div className="flex flex-wrap gap-1">
                {quickQuestions.slice(0, 3).map((question, index) => (
                  <button
                    key={index}
                    onClick={() => setInputMessage(question)}
                    className="text-xs px-2 py-1 bg-blue-50 text-blue-600 rounded-full hover:bg-blue-100 transition-colors duration-200"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Input */}
          <div className="p-4 border-t border-gray-200">
            <div className="flex space-x-2">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about chemistry, biology, or drug mechanisms..."
                className="flex-1 px-3 py-2 border border-gray-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm"
                rows="2"
                disabled={isTyping}
              />
              <button
                onClick={handleSendMessage}
                disabled={!inputMessage.trim() || isTyping}
                className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl hover:shadow-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <PaperAirplaneIcon className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default ChemBioBot;