/**
 * User-friendly error messages for MedToXAi
 */

export const getErrorMessage = (error) => {
    // Network errors
    if (error.message?.includes('Network Error') || error.message?.includes('ERR_NETWORK') || error.message?.includes('Failed to fetch')) {
        return {
            title: 'Connection Error',
            message: 'Unable to connect to the server. Please check your internet connection and try again.',
            suggestion: 'Make sure the backend server is running on port 5000.',
            type: 'network'
        };
    }

    // HTTP status codes
    if (error.response) {
        const status = error.response.status;
        const data = error.response.data;

        switch (status) {
            case 400:
                return {
                    title: 'Invalid Input',
                    message: data.error || 'The input provided is invalid.',
                    suggestion: 'Please check your SMILES string format or chemical name.',
                    type: 'validation'
                };

            case 404:
                return {
                    title: 'Not Found',
                    message: 'The requested resource was not found.',
                    suggestion: 'The API endpoint may have changed. Please refresh the page.',
                    type: 'client'
                };

            case 500:
                return {
                    title: 'Server Error',
                    message: 'The server encountered an error while processing your request.',
                    suggestion: 'Please try again in a moment. If the problem persists, contact support.',
                    type: 'server'
                };

            case 503:
                return {
                    title: 'Service Unavailable',
                    message: 'The service is temporarily unavailable.',
                    suggestion: 'The server may be starting up. Please wait a moment and try again.',
                    type: 'server'
                };

            default:
                return {
                    title: 'Request Failed',
                    message: data.error || `Request failed with status ${status}`,
                    suggestion: 'Please try again or contact support if the problem persists.',
                    type: 'unknown'
                };
        }
    }

    // Timeout errors
    if (error.code === 'ECONNABORTED') {
        return {
            title: 'Request Timeout',
            message: 'The request took too long to complete.',
            suggestion: 'The server may be busy. Please try again.',
            type: 'timeout'
        };
    }

    // OCR-specific errors
    if (error.message?.includes('OCR') || error.message?.includes('Tesseract') || error.message?.includes('WebAssembly')) {
        return {
            title: 'OCR Engine Error',
            message: 'The text recognition system encountered an error.',
            suggestion: 'You can manually enter chemical information below instead.',
            type: 'ocr'
        };
    }

    // Default error
    return {
        title: 'Error',
        message: error.message || 'An unexpected error occurred.',
        suggestion: 'Please try again or refresh the page.',
        type: 'unknown'
    };
};

/**
 * Format error for display
 */
export const formatError = (error) => {
    const { title, message, suggestion } = getErrorMessage(error);

    return {
        title,
        message: `${message}${suggestion ? `\n\n💡 ${suggestion}` : ''}`
    };
};

/**
 * Get user-friendly error message for specific error types
 */
export const getSpecificErrorMessage = (errorType, details = {}) => {
    const messages = {
        'invalid_smiles': {
            title: 'Invalid SMILES String',
            message: 'The SMILES notation you entered is not valid.',
            suggestion: 'Check for balanced brackets and valid SMILES characters. Example: CCO for ethanol'
        },
        'empty_input': {
            title: 'Empty Input',
            message: 'Please enter a SMILES string or chemical name.',
            suggestion: 'You can also upload an image for automatic analysis.'
        },
        'image_too_large': {
            title: 'Image Too Large',
            message: `The image is too large (${details.size || 'unknown size'}).`,
            suggestion: 'Please use an image under 10MB.'
        },
        'invalid_image_format': {
            title: 'Invalid Image Format',
            message: `The file format (${details.format || 'unknown'}) is not supported.`,
            suggestion: 'Please use PNG, JPEG, WEBP, or BMP images.'
        },
        'no_text_found': {
            title: 'No Text Found',
            message: 'No readable text was found in the image.',
            suggestion: 'Try using a clearer image with visible text, or enter the information manually.'
        },
        'prediction_failed': {
            title: 'Prediction Failed',
            message: 'Unable to predict toxicity for this molecule.',
            suggestion: 'Please verify the SMILES string is correct and try again.'
        },
        'database_offline': {
            title: 'Database Unavailable',
            message: 'The database is currently offline.',
            suggestion: 'Predictions will still work, but results won\'t be saved to history.'
        }
    };

    return messages[errorType] || {
        title: 'Error',
        message: details.message || 'An error occurred.',
        suggestion: 'Please try again.'
    };
};
