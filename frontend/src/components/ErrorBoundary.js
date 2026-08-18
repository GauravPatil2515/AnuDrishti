import React from 'react';
import { clsx } from 'clsx';
import {
  ExclamationTriangleIcon,
  ArrowPathIcon,
  BugAntIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';

/**
 * Error Boundary for graceful error handling
 * Catches JavaScript errors in child component tree
 * Logs errors and shows fallback UI
 */

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      errorInfo: null 
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error,
      errorInfo,
    });
    
    // Log error to console (in production, send to error tracking service)
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Call optional callback
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleRetry = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.handleRetry);
      }

      return (
        <div className="flex flex-col items-center justify-center p-8 text-center rounded-xl border border-border bg-surface">
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10 text-red-500 mb-4 mx-auto">
            <ExclamationTriangleIcon className="h-8 w-8" />
          </div>
          
          <h3 className="text-lg font-semibold text-primary mb-2">
            Something went wrong
          </h3>
          
          <p className="text-secondary mb-4 max-w-md">
            We encountered an unexpected error. The development team has been notified.
          </p>
          
          <details className="text-left max-w-md mx-auto mb-4 p-3 bg-canvas rounded-lg border border-border text-xs text-secondary">
            <summary className="cursor-pointer font-medium text-secondary mb-1">
              Error Details
            </summary>
            <pre className="whitespace-pre-wrap text-xs text-muted">{this.state.error?.message || 'Unknown error'}</pre>
          </details>
          
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={this.handleRetry}
              className="btn btn-primary flex items-center gap-2"
            >
              <ArrowPathIcon className="h-4 w-4" />
              Try Again
            </button>
            
            <button
              onClick={() => window.location.reload()}
              className="btn btn-secondary flex items-center gap-2"
            >
              <InformationCircleIcon className="h-4 w-4" />
              Reload Page
            </button>
          </div>
          
          {process.env.NODE_ENV === 'development' && (
            <details className="mt-6 text-left max-w-2xl mx-auto p-3 bg-red-500/5 rounded-lg border border-red-500/20 text-xs text-red-400">
              <summary className="cursor-pointer font-medium">Stack Trace (Development)</summary>
              <pre className="whitespace-pre-wrap mt-2">{this.state.errorInfo?.componentStack || 'No stack trace available'}</pre>
            </details>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

/**
 * Specialized error boundary for async components
 * Shows skeleton while loading, error state on failure
 */
export class AsyncBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null,
      isLoading: true 
    };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, isLoading: false };
  }

  componentDidCatch(error, errorInfo) {
    console.error('AsyncBoundary caught an error:', error, errorInfo);
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  render() {
    const { children, fallback, errorFallback, loadingFallback } = this.props;
    
    if (this.state.isLoading && loadingFallback) {
      return loadingFallback;
    }
    
    if (this.state.hasError) {
      if (errorFallback) {
        return errorFallback(this.state.error, () => this.setState({ hasError: false, error: null }));
      }
      return (
        <div className="p-4 rounded-lg border border-red-500/30 bg-red-500/5">
          <p className="text-red-500">Failed to load component</p>
          <button 
            onClick={() => this.setState({ hasError: false, isLoading: true })}
            className="btn btn-secondary mt-2"
          >
            Retry
          </button>
        </div>
      );
    }
    
    return children;
  }
}

/**
 * HOC to wrap a component with ErrorBoundary
 */
export const withErrorBoundary = (WrappedComponent, errorBoundaryProps = {}) => {
  return function WithErrorBoundary(props) {
    return (
      <ErrorBoundary {...errorBoundaryProps}>
        <WrappedComponent {...props} />
      </ErrorBoundary>
    );
  };
};

export default ErrorBoundary;