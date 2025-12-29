/**
 * Validation utilities for MedToXAi
 */

/**
 * Validate SMILES string
 * @param {string} smiles - SMILES string to validate
 * @returns {object} - { valid: boolean, error: string }
 */
export const validateSMILES = (smiles) => {
  // Check if empty
  if (!smiles || typeof smiles !== 'string') {
    return { valid: false, error: 'SMILES string is required' };
  }
  
  const trimmed = smiles.trim();
  
  if (trimmed.length === 0) {
    return { valid: false, error: 'SMILES string cannot be empty' };
  }
  
  // Check length
  if (trimmed.length > 500) {
    return { valid: false, error: 'SMILES string too long (maximum 500 characters)' };
  }
  
  if (trimmed.length < 2) {
    return { valid: false, error: 'SMILES string too short (minimum 2 characters)' };
  }
  
  // Check for valid SMILES characters
  // Valid: letters, numbers, @, +, -, [, ], (, ), =, #, $, /, \, ., %
  const validChars = /^[A-Za-z0-9@+\-\[\]\(\)=#$\/\\\.%]+$/;
  if (!validChars.test(trimmed)) {
    return { 
      valid: false, 
      error: 'Invalid characters in SMILES string. Only alphanumeric and SMILES symbols allowed.' 
    };
  }
  
  // Check for balanced brackets
  const openBrackets = (trimmed.match(/\[/g) || []).length;
  const closeBrackets = (trimmed.match(/\]/g) || []).length;
  if (openBrackets !== closeBrackets) {
    return { valid: false, error: 'Unbalanced square brackets in SMILES string' };
  }
  
  const openParens = (trimmed.match(/\(/g) || []).length;
  const closeParens = (trimmed.match(/\)/g) || []).length;
  if (openParens !== closeParens) {
    return { valid: false, error: 'Unbalanced parentheses in SMILES string' };
  }
  
  return { valid: true, error: null };
};

/**
 * Validate chemical name
 */
export const validateChemicalName = (name) => {
  if (!name || typeof name !== 'string') {
    return { valid: false, error: 'Chemical name is required' };
  }
  
  const trimmed = name.trim();
  
  if (trimmed.length === 0) {
    return { valid: false, error: 'Chemical name cannot be empty' };
  }
  
  if (trimmed.length > 200) {
    return { valid: false, error: 'Chemical name too long (maximum 200 characters)' };
  }
  
  return { valid: true, error: null };
};

/**
 * Sanitize text input (remove HTML, scripts, etc.)
 */
export const sanitizeText = (text) => {
  if (!text) return '';
  
  return text
    .replace(/<[^>]*>/g, '') // Remove HTML tags
    .replace(/[<>]/g, '') // Remove angle brackets
    .trim();
};

/**
 * Validate image file
 */
export const validateImage = (file) => {
  if (!file) {
    return { valid: false, error: 'No file selected' };
  }
  
  // Check file size (max 10MB)
  const maxSize = 10 * 1024 * 1024;
  if (file.size > maxSize) {
    return { 
      valid: false, 
      error: `Image too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Maximum size is 10MB.` 
    };
  }
  
  // Check file type
  const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/webp', 'image/bmp'];
  if (!validTypes.includes(file.type)) {
    return { 
      valid: false, 
      error: `Invalid image format (${file.type}). Please use PNG, JPEG, WEBP, or BMP.` 
    };
  }
  
  return { valid: true, error: null };
};
