"""
ChemBERT + Groq Integration for Enhanced Chemical Text Generation
Combines transformer embeddings with AI-powered insights
"""
import os
import sys
import warnings
warnings.filterwarnings('ignore')

# Add path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from models.chembert_analyzer import get_chembert_analyzer
from config.groq import groq_config

class ChemBERTGroqIntegration:
    """
    Combines ChemBERT molecular embeddings with Groq AI for enhanced analysis
    """
    
    def __init__(self):
        """Initialize ChemBERT and Groq clients"""
        self.chembert = get_chembert_analyzer()
        self.groq = groq_config
        print("✅ ChemBERT + Groq integration initialized")
    
    def analyze_with_embeddings(self, smiles, include_ai_report=True):
        """
        Analyze molecule using ChemBERT embeddings + Groq AI
        
        Args:
            smiles (str): SMILES string
            include_ai_report (bool): Generate AI report
            
        Returns:
            dict: Complete analysis with embeddings and AI insights
        """
        try:
            # Get ChemBERT embeddings
            chembert_result = self.chembert.analyze_molecule(smiles)
            
            if not chembert_result['success']:
                return chembert_result
            
            # Extract key features from embedding
            embedding = chembert_result['embedding']
            
            # Calculate embedding statistics
            import numpy as np
            embedding_array = np.array(embedding)
            
            embedding_stats = {
                'mean': float(np.mean(embedding_array)),
                'std': float(np.std(embedding_array)),
                'min': float(np.min(embedding_array)),
                'max': float(np.max(embedding_array)),
                'l2_norm': float(np.linalg.norm(embedding_array))
            }
            
            result = {
                'smiles': smiles,
                'chembert_embeddings': {
                    'vector': embedding[:10],  # First 10 values for preview
                    'dimension': len(embedding),
                    'statistics': embedding_stats
                },
                'success': True
            }
            
            # Generate AI report if requested
            if include_ai_report:
                ai_report = self._generate_ai_report(smiles, embedding_stats)
                result['ai_analysis'] = ai_report
            
            return result
            
        except Exception as e:
            return {
                'smiles': smiles,
                'error': str(e),
                'success': False
            }
    
    def _generate_ai_report(self, smiles, embedding_stats):
        """
        Generate AI report using ChemBERT embedding statistics
        
        Args:
            smiles (str): SMILES string
            embedding_stats (dict): Embedding statistics
            
        Returns:
            str: AI-generated analysis
        """
        try:
            prompt = f"""Analyze this chemical molecule using ChemBERT transformer embeddings:

SMILES: {smiles}

ChemBERT Embedding Statistics:
- Mean activation: {embedding_stats['mean']:.4f}
- Standard deviation: {embedding_stats['std']:.4f}
- L2 norm: {embedding_stats['l2_norm']:.4f}
- Value range: [{embedding_stats['min']:.4f}, {embedding_stats['max']:.4f}]

Based on the molecular structure and embedding characteristics, provide:

1. **Molecular Properties**: What can we infer about this molecule's properties?
2. **Chemical Class**: What type of compound is this likely to be?
3. **Structural Features**: Key functional groups or structural patterns
4. **Potential Applications**: Possible uses based on structure
5. **Safety Considerations**: Any notable safety or toxicity concerns
6. **Embedding Interpretation**: What do the embedding statistics suggest?

Provide a comprehensive, scientifically accurate analysis."""

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert chemoinformatics AI specializing in molecular property analysis using transformer models. Provide detailed, scientific insights."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            ai_response = self.groq.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1200
            )
            
            return ai_response
            
        except Exception as e:
            return f"AI analysis unavailable: {str(e)}"
    
    def compare_molecules(self, smiles1, smiles2):
        """
        Compare two molecules using ChemBERT + Groq AI
        
        Args:
            smiles1 (str): First SMILES
            smiles2 (str): Second SMILES
            
        Returns:
            dict: Comparison results
        """
        try:
            # Get ChemBERT similarity
            similarity_result = self.chembert.similarity_analysis(smiles1, smiles2)
            
            # Generate AI comparison
            prompt = f"""Compare these two molecules using their SMILES notation:

Molecule 1: {smiles1}
Molecule 2: {smiles2}

ChemBERT Cosine Similarity: {similarity_result['cosine_similarity']:.4f}
Interpretation: {similarity_result['interpretation']}

Provide a detailed comparison covering:

1. **Structural Similarities**: What structural features do they share?
2. **Structural Differences**: How do they differ?
3. **Property Comparison**: Expected differences in physical/chemical properties
4. **Biological Activity**: Likely differences in biological effects
5. **Similarity Interpretation**: What does the {similarity_result['cosine_similarity']:.4f} similarity score mean?
6. **Practical Implications**: What does this comparison tell us?

Be specific and scientific in your analysis."""

            messages = [
                {
                    "role": "system",
                    "content": "You are an expert medicinal chemist analyzing molecular similarities and structure-activity relationships."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            ai_comparison = self.groq.chat_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=1200
            )
            
            return {
                'smiles1': smiles1,
                'smiles2': smiles2,
                'chembert_similarity': similarity_result,
                'ai_comparison': ai_comparison,
                'success': True
            }
            
        except Exception as e:
            return {
                'smiles1': smiles1,
                'smiles2': smiles2,
                'error': str(e),
                'success': False
            }
    
    def batch_analyze_with_insights(self, smiles_list, generate_summary=True):
        """
        Analyze multiple molecules with ChemBERT + AI summary
        
        Args:
            smiles_list (list): List of SMILES strings
            generate_summary (bool): Generate AI summary
            
        Returns:
            dict: Batch analysis results
        """
        try:
            # Get ChemBERT batch analysis
            batch_results = self.chembert.batch_analyze(smiles_list)
            
            # Calculate dataset statistics
            import numpy as np
            all_embeddings = [r['embedding'] for r in batch_results if r['success']]
            
            if all_embeddings:
                embeddings_array = np.array(all_embeddings)
                dataset_stats = {
                    'total_molecules': len(smiles_list),
                    'successful_analyses': len(all_embeddings),
                    'embedding_dimension': embeddings_array.shape[1],
                    'average_similarity': self._calculate_average_similarity(embeddings_array),
                    'diversity_score': float(np.mean(np.std(embeddings_array, axis=0)))
                }
            else:
                dataset_stats = {
                    'total_molecules': len(smiles_list),
                    'successful_analyses': 0
                }
            
            result = {
                'molecules': batch_results,
                'dataset_statistics': dataset_stats,
                'success': True
            }
            
            # Generate AI summary if requested
            if generate_summary and all_embeddings:
                ai_summary = self._generate_batch_summary(smiles_list, dataset_stats)
                result['ai_summary'] = ai_summary
            
            return result
            
        except Exception as e:
            return {
                'smiles_list': smiles_list,
                'error': str(e),
                'success': False
            }
    
    def _calculate_average_similarity(self, embeddings_array):
        """Calculate average pairwise similarity"""
        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity
        
        try:
            similarities = cosine_similarity(embeddings_array)
            # Get upper triangle (exclude diagonal)
            upper_triangle = similarities[np.triu_indices_from(similarities, k=1)]
            return float(np.mean(upper_triangle)) if len(upper_triangle) > 0 else 0.0
        except:
            return 0.0
    
    def _generate_batch_summary(self, smiles_list, dataset_stats):
        """Generate AI summary for batch analysis"""
        try:
            prompt = f"""Analyze this molecular dataset using ChemBERT embeddings:

Dataset Overview:
- Total molecules: {dataset_stats['total_molecules']}
- Successfully analyzed: {dataset_stats['successful_analyses']}
- Embedding dimension: {dataset_stats.get('embedding_dimension', 'N/A')}
- Average pairwise similarity: {dataset_stats.get('average_similarity', 0):.4f}
- Diversity score: {dataset_stats.get('diversity_score', 0):.4f}

Sample SMILES (first 5):
{chr(10).join(['- ' + s for s in smiles_list[:5]])}

Provide insights on:

1. **Dataset Diversity**: What does the similarity/diversity tell us?
2. **Molecular Families**: Are there likely chemical families or clusters?
3. **Property Predictions**: Expected property distributions
4. **Recommendations**: Suggestions for further analysis
5. **Chemical Space Coverage**: How diverse is this chemical library?

Be analytical and provide actionable insights."""

            messages = [
                {
                    "role": "system",
                    "content": "You are a cheminformatics expert analyzing molecular datasets and chemical libraries."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            ai_summary = self.groq.chat_completion(
                messages=messages,
                temperature=0.4,
                max_tokens=1000
            )
            
            return ai_summary
            
        except Exception as e:
            return f"AI summary unavailable: {str(e)}"
    
    def predict_properties_with_context(self, smiles, property_type="toxicity"):
        """
        Predict molecular properties using ChemBERT + Groq contextual knowledge
        
        Args:
            smiles (str): SMILES string
            property_type (str): Type of property to predict
            
        Returns:
            dict: Property predictions with AI context
        """
        try:
            # Get ChemBERT analysis
            chembert_result = self.chembert.analyze_molecule(smiles)
            
            if not chembert_result['success']:
                return chembert_result
            
            # Generate AI prediction with context
            prompt = f"""Using chemical knowledge and structure analysis, predict properties for:

SMILES: {smiles}

Property Focus: {property_type.title()}

ChemBERT embedding has been generated (768-dimensional molecular representation).

Provide detailed predictions for:

1. **{property_type.title()} Assessment**: Likely {property_type} profile
2. **Molecular Mechanisms**: How structure affects {property_type}
3. **Key Structural Alerts**: Problematic or beneficial features
4. **Confidence Level**: High/Medium/Low with reasoning
5. **Recommendations**: Testing priorities or structural modifications
6. **Regulatory Considerations**: Relevant safety guidelines

Base your analysis on established structure-activity relationships and toxicophore knowledge."""

            messages = [
                {
                    "role": "system",
                    "content": f"You are an expert in computational {property_type} prediction and structure-activity relationships. Provide evidence-based, detailed predictions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            ai_prediction = self.groq.chat_completion(
                messages=messages,
                temperature=0.2,
                max_tokens=1500
            )
            
            return {
                'smiles': smiles,
                'property_type': property_type,
                'chembert_analysis': chembert_result,
                'ai_prediction': ai_prediction,
                'success': True
            }
            
        except Exception as e:
            return {
                'smiles': smiles,
                'property_type': property_type,
                'error': str(e),
                'success': False
            }


# Global singleton instance
_integration_instance = None

def get_chembert_groq_integration():
    """
    Get or create ChemBERT + Groq integration singleton
    
    Returns:
        ChemBERTGroqIntegration: Initialized integration
    """
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = ChemBERTGroqIntegration()
    return _integration_instance
