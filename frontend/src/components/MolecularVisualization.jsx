import React, { useEffect, useRef } from 'react';

const MolecularVisualization = ({ smiles, width = 300, height = 200 }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!smiles || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Set canvas size
    canvas.width = width;
    canvas.height = height;
    
    // Simple molecular structure visualization
    // This is a simplified representation - in production, use RDKit or similar
    drawMolecularStructure(ctx, smiles, width, height);
  }, [smiles, width, height]);

  const drawMolecularStructure = (ctx, smiles, width, height) => {
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, width, height);
    
    // Border
    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    ctx.strokeRect(0, 0, width, height);
    
    // Title
    ctx.fillStyle = '#334155';
    ctx.font = '12px Inter, sans-serif';
    ctx.fillText('Molecular Structure', 10, 20);
    
    // SMILES string (wrapped)
    ctx.fillStyle = '#64748b';
    ctx.font = '10px Monaco, monospace';
    const maxCharsPerLine = Math.floor(width / 6);
    const lines = [];
    for (let i = 0; i < smiles.length; i += maxCharsPerLine) {
      lines.push(smiles.substring(i, i + maxCharsPerLine));
    }
    
    lines.forEach((line, index) => {
      ctx.fillText(line, 10, 40 + (index * 12));
    });
    
    // Simple atom representation
    const centerX = width / 2;
    const centerY = height / 2 + 20;
    
    // Draw some basic molecular visualization based on SMILES patterns
    if (smiles.includes('c1ccccc1') || smiles.includes('C1=CC=CC=C1')) {
      // Benzene ring
      drawBenzeneRing(ctx, centerX, centerY, 30);
    } else if (smiles.includes('OH') || smiles.includes('O')) {
      // Alcohol or ether
      drawSimpleMolecule(ctx, centerX, centerY, ['C', 'O', 'H']);
    } else if (smiles.includes('N')) {
      // Contains nitrogen
      drawSimpleMolecule(ctx, centerX, centerY, ['C', 'N', 'H']);
    } else {
      // Generic hydrocarbon
      drawSimpleMolecule(ctx, centerX, centerY, ['C', 'H']);
    }
    
    // Molecular properties
    ctx.fillStyle = '#475569';
    ctx.font = '10px Inter, sans-serif';
    ctx.fillText(`Length: ${smiles.length} chars`, 10, height - 20);
  };

  const drawBenzeneRing = (ctx, centerX, centerY, radius) => {
    const vertices = 6;
    const angleStep = (2 * Math.PI) / vertices;
    
    // Draw ring
    ctx.strokeStyle = '#3b82f6';
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    for (let i = 0; i <= vertices; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();
    
    // Draw carbon atoms
    ctx.fillStyle = '#1e293b';
    for (let i = 0; i < vertices; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fill();
    }
  };

  const drawSimpleMolecule = (ctx, centerX, centerY, atoms) => {
    const colors = {
      'C': '#1e293b',
      'O': '#dc2626',
      'N': '#2563eb',
      'H': '#6b7280',
      'S': '#eab308',
      'P': '#7c3aed'
    };
    
    atoms.forEach((atom, index) => {
      const angle = (index * 2 * Math.PI) / atoms.length;
      const radius = 25;
      const x = centerX + radius * Math.cos(angle);
      const y = centerY + radius * Math.sin(angle);
      
      // Draw bond to center
      if (index > 0) {
        ctx.strokeStyle = '#64748b';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(x, y);
        ctx.stroke();
      }
      
      // Draw atom
      ctx.fillStyle = colors[atom] || '#6b7280';
      ctx.beginPath();
      ctx.arc(x, y, 8, 0, 2 * Math.PI);
      ctx.fill();
      
      // Draw atom label
      ctx.fillStyle = 'white';
      ctx.font = 'bold 10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(atom, x, y);
    });
    
    // Reset text alignment
    ctx.textAlign = 'left';
    ctx.textBaseline = 'alphabetic';
  };

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-4">
      <canvas
        ref={canvasRef}
        className="w-full h-auto border border-gray-100 rounded"
        style={{ maxWidth: width, maxHeight: height }}
      />
      <div className="mt-2 text-xs text-gray-500">
        Simplified 2D representation
      </div>
    </div>
  );
};

export default MolecularVisualization;