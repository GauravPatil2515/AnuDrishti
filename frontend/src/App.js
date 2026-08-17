import React, { createContext, useContext, useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import Layout from './components/Layout/Layout';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Predictions from './pages/Predictions';
import EnhancedPredictions from './pages/EnhancedPredictions';
import BatchProcessing from './pages/BatchProcessing';
import Chat from './pages/Chat';
import PharmaGuardWorkbench from './pages/PharmaGuardWorkbench';
import { NotificationProvider } from './components/NotificationSystem';
import { OnboardingTutorial, QuickHelp } from './components/OnboardingTutorial';
import ChemBioBot from './components/ChemBioBot';

// Theme Context for Light/Dark Mode
export const ThemeContext = createContext();

export const useTheme = () => useContext(ThemeContext);

const ThemeProvider = ({ children }) => {
  const [theme, setTheme] = useState(localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};

// Placeholder components for pages not yet created
const Settings = () => <div className="text-2xl font-bold p-8">Settings</div>;
const Help = () => <div className="text-2xl font-bold p-8">Help & Documentation</div>;
const Contact = () => <div className="text-2xl font-bold p-8">Contact Support</div>;

const AppContent = () => {
  const { theme } = useTheme();
  
  return (
    <>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: theme === 'dark' ? '#111d2e' : '#ffffff',
            color: theme === 'dark' ? '#e2f0fb' : '#0f172a',
            border: `1px solid ${theme === 'dark' ? 'rgba(56, 189, 248, 0.2)' : 'rgba(15, 23, 42, 0.1)'}`,
            borderRadius: '0.5rem',
            padding: '12px 16px',
            fontSize: '14px',
          },
          success: {
            duration: 3000,
            iconTheme: { primary: '#10b981', secondary: '#ffffff' },
          },
          error: {
            duration: 5000,
            iconTheme: { primary: '#ef4444', secondary: '#ffffff' },
          },
        }}
      />
      
      <div className="App min-h-screen">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/app" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="predictions" element={<EnhancedPredictions />} />
            <Route path="batch" element={<BatchProcessing />} />
            <Route path="chat" element={<Chat />} />
            <Route path="pharmaguard" element={<PharmaGuardWorkbench />} />
            <Route path="settings" element={<Settings />} />
            <Route path="help" element={<Help />} />
            <Route path="contact" element={<Contact />} />
          </Route>
        </Routes>
        <OnboardingTutorial />
      </div>
    </>
  );
};

function App() {
  return (
    <ThemeProvider>
      <NotificationProvider>
        <AppContent />
      </NotificationProvider>
    </ThemeProvider>
  );
}

export default App;