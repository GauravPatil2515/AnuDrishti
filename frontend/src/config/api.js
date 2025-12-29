// API Configuration
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const ENV = process.env.REACT_APP_ENV || 'development';

export const config = {
  apiUrl: API_URL,
  environment: ENV,
  isProduction: ENV === 'production',
  isDevelopment: ENV === 'development',
  
  // API Endpoints
  endpoints: {
    health: `${API_URL}/api/health`,
    predict: `${API_URL}/api/predict`,
    predictBatch: `${API_URL}/api/predict/batch`,
    endpoints: `${API_URL}/api/endpoints`,
    analyzeImageVision: `${API_URL}/api/analyze-image-vision`,
    analyzeChemicalText: `${API_URL}/api/analyze-chemical-text`,
    chemicalNameToSmiles: `${API_URL}/api/chemical-name-to-smiles`,
    naturalLanguageToChemical: `${API_URL}/api/natural-language-to-chemical`,
    chatAsk: `${API_URL}/api/chat/ask`,
    aiAnalyze: `${API_URL}/api/ai/analyze`,
    aiExplain: (endpointId) => `${API_URL}/api/ai/explain/${endpointId}`,
    aiSuggestModifications: `${API_URL}/api/ai/suggest-modifications`,
    stats: `${API_URL}/api/stats`,
    predictions: `${API_URL}/api/predictions`,
    analytics: `${API_URL}/api/analytics`,
    downloadResults: `${API_URL}/api/download/results`,
    modelsStatus: `${API_URL}/api/models/status`,
    molecules: `${API_URL}/api/molecules`,
  },
  
  // Request configuration
  timeout: 30000, // 30 seconds
  retryAttempts: 3,
  retryDelay: 1000, // 1 second
};

// Helper function for API calls with retry logic and timeout
export const apiCall = async (url, options = {}, attempt = 1) => {
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    // Create abort controller for timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config.timeout);
    
    // Make fetch request
    const response = await fetch(url, {
      ...defaultOptions,
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Request failed' }));
      const errorMessage = error.error || `HTTP error! status: ${response.status}`;
      
      // Retry on server errors (5xx) or specific cases
      if (response.status >= 500 && attempt < config.retryAttempts) {
        console.warn(`[API] Server error (${response.status}). Retry attempt ${attempt}/${config.retryAttempts} in ${config.retryDelay}ms`);
        await sleep(config.retryDelay);
        return apiCall(url, options, attempt + 1);
      }
      
      throw new Error(errorMessage);
    }
    
    return await response.json();
  } catch (error) {
    // Handle timeout errors
    if (error.name === 'AbortError') {
      if (attempt < config.retryAttempts) {
        console.warn(`[API] Request timeout. Retry attempt ${attempt}/${config.retryAttempts} in ${config.retryDelay}ms`);
        await sleep(config.retryDelay);
        return apiCall(url, options, attempt + 1);
      }
      throw new Error(`Request timeout after ${config.timeout}ms. Server may be unresponsive.`);
    }
    
    // Handle network errors
    if (!navigator.onLine) {
      throw new Error('No internet connection. Please check your network and try again.');
    }
    
    // Don't retry on client errors (4xx) or if max attempts exceeded
    if (error.message.includes('HTTP error! status: 4')) {
      throw error;
    }
    
    if (attempt < config.retryAttempts) {
      console.warn(`[API] Network error. Retry attempt ${attempt}/${config.retryAttempts} in ${config.retryDelay}ms`);
      await sleep(config.retryDelay);
      return apiCall(url, options, attempt + 1);
    }
    
    console.error(`[API] Failed after ${config.retryAttempts} attempts:`, error);
    throw error;
  }
};

// Utility function for sleep/delay
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

export default config;
