import React, { useState } from 'react';
import toast, { Toaster } from 'react-hot-toast';

/**
 * RegulatorySignoffModal
 * A modal dialog that displays the results of regulatory PDF generation
 * and provides a one-click signature verification button.
 *
 * Props:
 *   pdfResult  — object with success, pdf_path, file_size_bytes, etc.
 *   onClose    — () => void  — close the modal
 *   onVerify   — async (pdf_path) => verification object
 */
const RegulatorySignoffModal = ({ pdfResult, onClose, onVerify }) => {
  const [verifying, setVerifying] = useState(false);
  const [verifyResult, setVerifyResult] = useState(null);

  const handleVerify = async () => {
    if (!pdfResult?.pdf_path) return;
    setVerifying(true);
    try {
      const res = await onVerify(pdfResult.pdf_path);
      setVerifyResult(res);
      if (res?.valid) {
        toast.success('Signature verified — document is authentic');
      } else {
        toast.error('Signature verification failed — document may be tampered');
      }
    } catch (err) {
      toast.error(`Verification error: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  const handleDownload = () => {
    if (pdfResult?.pdf_path) {
      window.open(`/api/report/download?pdf_path=${encodeURIComponent(pdfResult.pdf_path)}`, '_blank');
    }
  };

  const handleOpenDirectly = () => {
    if (pdfResult?.pdf_path) {
      window.open(pdfResult.pdf_path, '_blank');
    }
  };

  return (
    <div className="fixed inset-0 bg-canvas/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-surface border border-border rounded-xl shadow-xl max-w-2xl w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-border">
          <h2 className="text-xl font-bold text-text-primary">Regulatory PDF — Signoff</h2>
          <button
            onClick={onClose}
            className="p-2 text-text-muted hover:text-text-primary rounded-lg hover:bg-canvas-elevated transition-colors"
          >
            ✕
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4">
          <Toaster />

          {/* Status banner */}
          {pdfResult?.success ? (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2 text-green-800">
                <span className="text-green-600">✓</span>
                <span className="font-medium">Regulatory PDF generated successfully</span>
              </div>
              <p className="text-sm text-green-700 mt-1">
                Document is 21 CFR Part 11 compliant with HMAC-SHA256 digital signature.
              </p>
            </div>
          ) : (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center gap-2 text-red-800">
                <span className="text-red-600">✗</span>
                <span className="font-medium">PDF generation failed</span>
              </div>
            </div>
          )}

          {/* File details */}
          {pdfResult && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div className="bg-canvas-elevated rounded-lg p-3">
                <span className="text-xs text-text-muted">File Size</span>
                <div className="text-text-primary font-medium">
                  {pdfResult.file_size_bytes
                    ? `${(pdfResult.file_size_bytes / 1024).toFixed(1)} KB`
                    : 'N/A'}
                </div>
              </div>
              <div className="bg-canvas-elevated rounded-lg p-3">
                <span className="text-xs text-text-muted">Ruleset Version</span>
                <div className="text-text-primary font-medium">{pdfResult.ruleset_version || 'N/A'}</div>
              </div>
              <div className="bg-canvas-elevated rounded-lg p-3">
                <span className="text-xs text-text-muted">Batch ID</span>
                <div className="text-text-primary font-medium">{pdfResult.batch_id || 'N/A'}</div>
              </div>
              <div className="bg-canvas-elevated rounded-lg p-3">
                <span className="text-xs text-text-muted">Model Hash</span>
                <div className="text-xs font-mono text-text-muted break-all">
                  {pdfResult.model_hash || 'N/A'}
                </div>
              </div>
            </div>
          )}

          {/* Verification results */}
          {verifyResult && (
            <div>
              <h3 className="text-sm font-semibold text-text-primary mb-2">Signature Verification</h3>
              <div className="space-y-2">
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-sm text-text-muted">Document Hash Match</span>
                  <span className={`text-sm font-medium ${
                    verifyResult.file_hash_match ? 'text-green-500' : 'text-red-500'
                  }`}>
                    {verifyResult.file_hash_match ? 'PASS' : 'FAIL'}
                  </span>
                </div>
                <div className="flex justify-between py-1 border-b border-border/30">
                  <span className="text-sm text-text-muted">Signature Match</span>
                  <span className={`text-sm font-medium ${
                    verifyResult.signature_match ? 'text-green-500' : 'text-red-500'
                  }`}>
                    {verifyResult.signature_match ? 'PASS' : 'FAIL'}
                  </span>
                </div>
                <div className="flex justify-between py-1">
                  <span className="text-sm text-text-muted">Overall Status</span>
                  <span className={`text-sm font-bold ${
                    verifyResult.valid ? 'text-green-500' : 'text-red-500'
                  }`}>
                    {verifyResult.valid ? 'VERIFIED' : 'NOT VERIFIED'}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex justify-end gap-3 p-6 border-t border-border">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-border rounded-lg hover:bg-canvas-elevated transition-colors text-sm font-medium"
          >
            Close
          </button>
          <button
            onClick={handleVerify}
            disabled={verifying || !pdfResult?.pdf_path}
            className="px-4 py-2 bg-accent-green text-white rounded-lg hover:bg-accent-green/90 disabled:opacity-50 transition-colors text-sm font-medium"
          >
            {verifying ? 'Verifying...' : 'Verify Signature'}
          </button>
          <button
            onClick={handleOpenDirectly}
            disabled={!pdfResult?.pdf_path}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors text-sm font-medium"
          >
            View PDF
          </button>
        </div>
      </div>
    </div>
  );
};

export default RegulatorySignoffModal;
