import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Predictions from './pages/Predictions';
import EnhancedPredictions from './pages/EnhancedPredictions';
import BatchProcessing from './pages/BatchProcessing';
import Chat from './pages/Chat';
import { NotificationProvider } from './components/NotificationSystem';
import { OnboardingTutorial, QuickHelp } from './components/OnboardingTutorial';
import ChemBioBot from './components/ChemBioBot';

// Placeholder components for pages not yet created
const Settings = () => <div className="text-2xl font-bold">Settings</div>;
const Help = () => <div className="text-2xl font-bold">Help & Documentation</div>;
const Contact = () => <div className="text-2xl font-bold">Contact Support</div>;

function App() {
  return (
    <NotificationProvider>
      {/* Toast Notifications - Pink/Purple Theme */}
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#ffffff',
            color: '#374151',
            border: '1px solid #e5e7eb',
            borderRadius: '0.75rem',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            padding: '16px',
          },
          success: {
            duration: 3000,
            style: {
              background: '#f0fdf4',
              border: '1px solid #86efac',
            },
            iconTheme: {
              primary: '#10b981',
              secondary: '#ffffff',
            },
          },
          error: {
            duration: 5000,
            style: {
              background: '#fef2f2',
              border: '1px solid #fca5a5',
            },
            iconTheme: {
              primary: '#ef4444',
              secondary: '#ffffff',
            },
          },
          loading: {
            style: {
              background: '#fdf4ff',
              border: '1px solid #f0abfc',
            },
            iconTheme: {
              primary: '#ec4899',
              secondary: '#ffffff',
            },
          },
        }}
      />

      <div className="App">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/app" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="predictions" element={<EnhancedPredictions />} />
            <Route path="batch" element={<BatchProcessing />} />
            <Route path="chat" element={<Chat />} />
            <Route path="settings" element={<Settings />} />
            <Route path="help" element={<Help />} />
            <Route path="contact" element={<Contact />} />
          </Route>
        </Routes>

        {/* Global Components */}
        <OnboardingTutorial />
      </div>
    </NotificationProvider>
  );
}

export default App;