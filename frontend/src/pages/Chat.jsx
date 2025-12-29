import React, { useState, useRef, useEffect } from 'react';
import { 
  PaperAirplaneIcon, 
  UserIcon, 
  BeakerIcon,
  ClipboardDocumentIcon,
  TrashIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const Chat = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: 'assistant',
      content: 'Hi! I\'m your AI assistant for drug discovery and ADMET analysis.\n\nI can help you understand:\n• Toxicity predictions\n• ADMET properties\n• Drug-like characteristics\n• Model interpretations\n\nWhat would you like to know?',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const exampleQuestions = [
    "What does BBB penetration mean?",
    "Explain clinical toxicity",
    "What is intrinsic clearance?",
    "How to interpret ADMET results?"
  ];

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:5000/api/chat/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: userMessage.content,
          context: 'scientific_admet'
        })
      });

      if (response.ok) {
        const data = await response.json();
        const assistantMessage = {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.response || 'I apologize, but I encountered an issue processing your request. Please try again.',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error('Failed to get response from AI assistant');
      }
    } catch (error) {
      console.error('Chat error:', error);
      const errorMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'I am currently unable to connect to the AI service. Please ensure the backend server is running and try again.',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 1,
        role: 'assistant',
        content: 'Chat cleared. How can I assist you with your ADMET analysis today?',
        timestamp: new Date()
      }
    ]);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
  };

  const handleExampleQuestion = (question) => {
    setInputMessage(question);
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col bg-black rounded-xl overflow-hidden border border-primary-500/20">
      {/* Simple Header */}
      <div className="bg-gradient-to-r from-gray-900 to-black px-6 py-4 flex items-center justify-between border-b border-primary-500/20">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-primary-500 to-accent-600 flex items-center justify-center">
            <SparklesIcon className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-white">AI Assistant</h1>
            <p className="text-xs text-gray-400">Ask me anything about drug discovery</p>
          </div>
        </div>
        <button
          onClick={clearChat}
          className="p-2 text-gray-400 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
          title="Clear chat"
        >
          <TrashIcon className="h-4 w-4" />
        </button>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4 bg-gradient-to-b from-black to-gray-950">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
          >
            <div
              className={`flex items-start gap-3 max-w-2xl ${
                message.role === 'user' ? 'flex-row-reverse' : ''
              }`}
            >
              {/* Avatar */}
              <div
                className={`h-8 w-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-primary-500 to-accent-600'
                    : 'bg-gray-800 border border-primary-500/30'
                }`}
              >
                {message.role === 'user' ? (
                  <UserIcon className="h-4 w-4 text-white" />
                ) : (
                  <BeakerIcon className="h-4 w-4 text-primary-400" />
                )}
              </div>
              
              {/* Message Bubble */}
              <div className="flex flex-col gap-1">
                <div
                  className={`rounded-2xl px-4 py-3 ${
                    message.role === 'user'
                      ? 'bg-gradient-to-r from-primary-600 to-accent-600 text-white'
                      : 'bg-gray-900 text-gray-200 border border-gray-800'
                  }`}
                >
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">
                    {message.content}
                  </p>
                </div>
                
                {/* Timestamp & Actions */}
                <div className={`flex items-center gap-2 px-2 ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <span className="text-xs text-gray-500">
                    {message.timestamp.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit'
                    })}
                  </span>
                  {message.role === 'assistant' && (
                    <button
                      onClick={() => copyToClipboard(message.content)}
                      className="text-gray-500 hover:text-primary-400 transition-colors"
                      title="Copy message"
                    >
                      <ClipboardDocumentIcon className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start animate-fadeIn">
            <div className="flex items-start gap-3 max-w-2xl">
              <div className="h-8 w-8 rounded-full bg-gray-800 border border-primary-500/30 flex items-center justify-center">
                <BeakerIcon className="h-4 w-4 text-primary-400" />
              </div>
              <div className="bg-gray-900 border border-gray-800 rounded-2xl px-4 py-3">
                <div className="flex gap-1.5">
                  <div className="h-2 w-2 bg-primary-500 rounded-full animate-bounce"></div>
                  <div className="h-2 w-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="h-2 w-2 bg-primary-500 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Example Questions - Compact */}
      {messages.length === 1 && (
        <div className="bg-gradient-to-r from-gray-900 to-black border-t border-primary-500/20 px-6 py-3">
          <p className="text-xs text-gray-500 mb-2">Try asking:</p>
          <div className="flex flex-wrap gap-2">
            {exampleQuestions.map((question, index) => (
              <button
                key={index}
                onClick={() => handleExampleQuestion(question)}
                className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 text-gray-300 rounded-lg transition-all border border-gray-700 hover:border-primary-500/50"
              >
                {question}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area - Simplified */}
      <div className="bg-gradient-to-r from-gray-900 to-black border-t border-primary-500/20 px-6 py-4">
        <div className="flex items-end gap-3">
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Ask about ADMET properties, toxicity, or drug discovery..."
            className="flex-1 px-4 py-3 bg-gray-800 border border-gray-700 text-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500 focus:border-transparent resize-none text-sm placeholder-gray-500"
            rows="1"
            disabled={isLoading}
          />
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="p-3 bg-gradient-to-r from-primary-600 to-accent-600 text-white rounded-xl hover:from-primary-500 hover:to-accent-500 disabled:from-gray-700 disabled:to-gray-700 disabled:cursor-not-allowed transition-all shadow-lg shadow-primary-500/30 hover:scale-105 transform"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Chat;
