"""
ChemBERT Analyzer - Chemical Text Transformer Integration
Uses ChemBERTa model for molecular property analysis and predictions
"""
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
import warnings
warnings.filterwarnings('ignore')

class ChemBERTAnalyzer:
    """
    ChemBERT-based molecular analyzer for chemical text processing
    """
    
    def __init__(self, model_name="seyonec/ChemBERTa-zinc-base-v1"):
        """
        Initialize ChemBERT model and tokenizer
        
        Args:
            model_name (str): HuggingFace model identifier
        """
        self.model_name = model_name
        self.tokenizer = None
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._load_model()
    
    def _load_model(self):
        """Load ChemBERT model and tokenizer"""
        try:
            print(f"Loading ChemBERT model: {self.model_name}")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            print(f"✓ ChemBERT loaded successfully on {self.device}")
        except Exception as e:
            print(f"Error loading ChemBERT: {e}")
            raise
    
    def get_embeddings(self, smiles_list):
        """
        Generate molecular embeddings from SMILES strings
        
        Args:
            smiles_list (list): List of SMILES strings
            
        Returns:
            numpy.ndarray: Molecular embeddings (n_molecules, 768)
        """
        if isinstance(smiles_list, str):
            smiles_list = [smiles_list]
        
        embeddings = []
        
        with torch.no_grad():
            for smiles in smiles_list:
                # Tokenize
                inputs = self.tokenizer(
                    smiles, 
                    return_tensors="pt", 
                    padding=True, 
                    truncation=True,
                    max_length=512
                )
                
                # Move to device
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
                
                # Get model output
                outputs = self.model(**inputs)
                
                # Extract [CLS] token embedding (molecular representation)
                cls_embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()
                embeddings.append(cls_embedding[0])
        
        return np.array(embeddings)
    
    def analyze_molecule(self, smiles):
        """
        Analyze a single molecule and return embedding
        
        Args:
            smiles (str): SMILES string
            
        Returns:
            dict: Analysis results with embedding and metadata
        """
        try:
            embedding = self.get_embeddings([smiles])[0]
            
            return {
                'smiles': smiles,
                'embedding': embedding.tolist(),
                'embedding_shape': embedding.shape,
                'model': self.model_name,
                'success': True
            }
        except Exception as e:
            return {
                'smiles': smiles,
                'error': str(e),
                'success': False
            }
    
    def batch_analyze(self, smiles_list):
        """
        Analyze multiple molecules in batch
        
        Args:
            smiles_list (list): List of SMILES strings
            
        Returns:
            list: List of analysis results
        """
        results = []
        embeddings = self.get_embeddings(smiles_list)
        
        for i, smiles in enumerate(smiles_list):
            results.append({
                'smiles': smiles,
                'embedding': embeddings[i].tolist(),
                'embedding_shape': embeddings[i].shape,
                'model': self.model_name,
                'success': True
            })
        
        return results
    
    def similarity_analysis(self, smiles1, smiles2):
        """
        Calculate cosine similarity between two molecules
        
        Args:
            smiles1 (str): First SMILES string
            smiles2 (str): Second SMILES string
            
        Returns:
            dict: Similarity analysis results
        """
        embeddings = self.get_embeddings([smiles1, smiles2])
        
        # Calculate cosine similarity
        emb1 = embeddings[0]
        emb2 = embeddings[1]
        
        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
        
        return {
            'smiles1': smiles1,
            'smiles2': smiles2,
            'cosine_similarity': float(similarity),
            'interpretation': self._interpret_similarity(similarity)
        }
    
    def _interpret_similarity(self, similarity):
        """Interpret similarity score"""
        if similarity > 0.9:
            return "Very High Similarity"
        elif similarity > 0.7:
            return "High Similarity"
        elif similarity > 0.5:
            return "Moderate Similarity"
        elif similarity > 0.3:
            return "Low Similarity"
        else:
            return "Very Low Similarity"


# Singleton instance for reuse
_chembert_instance = None

def get_chembert_analyzer():
    """
    Get or create ChemBERT analyzer singleton instance
    
    Returns:
        ChemBERTAnalyzer: Initialized analyzer
    """
    global _chembert_instance
    if _chembert_instance is None:
        _chembert_instance = ChemBERTAnalyzer()
    return _chembert_instance
