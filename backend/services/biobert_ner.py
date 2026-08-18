#!/usr/bin/env python3
"""
BioBERT Named Entity Recognition Service
=========================================
Extracts biomedical entities from natural language queries:
- Drug/chemical names (CHEMICAL)
- Gene/protein targets (GENE)
- Diseases/conditions (DISEASE)

Uses allenai/scibert_scivocab_uncased (110MB) - lighter than full BioBERT (440MB)
Same domain, optimized for scientific text.
"""

import os
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from functools import lru_cache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BiomedicalEntities:
    """Structured biomedical entities extracted from text."""
    drugs: List[str]
    targets: List[str]
    diseases: List[str]
    chemicals: List[str]  # Broader chemical entities

    def to_dict(self) -> Dict:
        return {
            'drugs': self.drugs,
            'targets': self.targets,
            'diseases': self.diseases,
            'chemicals': self.chemicals,
        }

    def all_entities(self) -> List[str]:
        """Get all unique entities across categories."""
        all_ents = []
        all_ents.extend(self.drugs)
        all_ents.extend(self.targets)
        all_ents.extend(self.diseases)
        all_ents.extend(self.chemicals)
        return list(dict.fromkeys(all_ents))  # Preserve order, remove duplicates


class BioBERTNER:
    """
    Biomedical Named Entity Recognition using SciBERT.
    
    Falls back gracefully if model not available or download fails.
    """

    def __init__(self, model_name: str = "allenai/scibert_scivocab_uncased", cache_dir: Optional[str] = None):
        """
        Initialize BioBERT NER pipeline.
        
        Args:
            model_name: HuggingFace model identifier
            cache_dir: Directory to cache model downloads
        """
        self.model_name = model_name
        self.cache_dir = cache_dir or os.path.join(os.path.dirname(__file__), '..', '..', 'models_cache')
        self.ner_pipeline = None
        self._initialized = False
        self._init_error = None

    def _initialize(self) -> bool:
        """Lazy initialization of the NER pipeline."""
        if self._initialized:
            return self.ner_pipeline is not None
        
        self._initialized = True
        
        try:
            from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
            import torch
            
            logger.info(f"Loading BioBERT NER model: {self.model_name}")
            
            # Load tokenizer and model
            tokenizer = AutoTokenizer.from_pretrained(
                self.model_name, 
                cache_dir=self.cache_dir
            )
            
            model = AutoModelForTokenClassification.from_pretrained(
                self.model_name,
                cache_dir=self.cache_dir
            )
            
            # Create NER pipeline with aggregation
            self.ner_pipeline = pipeline(
                "ner",
                model=model,
                tokenizer=tokenizer,
                aggregation_strategy="simple",
                device=0 if torch.cuda.is_available() else -1
            )
            
            logger.info("✅ BioBERT NER pipeline initialized successfully")
            return True
            
        except ImportError as e:
            self._init_error = f"transformers not installed: {e}"
            logger.warning(f"⚠️ {self._init_error}")
            return False
        except Exception as e:
            self._init_error = str(e)
            logger.warning(f"⚠️ BioBERT NER initialization failed: {e}")
            return False

    def extract_entities(self, text: str) -> BiomedicalEntities:
        """
        Extract biomedical entities from query text.
        
        Args:
            text: Natural language query string
            
        Returns:
            BiomedicalEntities with categorized entities
        """
        # Initialize if not already done
        if not self._initialized:
            self._initialize()
        
        # Fallback: return empty if not available
        if self.ner_pipeline is None:
            logger.debug("BioBERT NER not available, returning empty entities")
            return BiomedicalEntities(drugs=[], targets=[], diseases=[], chemicals=[])
        
        try:
            # Run NER
            entities = self.ner_pipeline(text)
            
            # Categorize entities based on entity_group
            # SciBERT uses: CHEMICAL, GENE, DISEASE, etc.
            drugs: List[str] = []
            targets: List[str] = []
            diseases: List[str] = []
            chemicals: List[str] = []
            
            for ent in entities:
                if not isinstance(ent, dict):
                    continue
                entity_text = ent.get('word', '').strip()
                entity_group = ent.get('entity_group', '').upper()
                score = float(ent.get('score', 0.0))
                
                # Filter low confidence
                if score < 0.5:
                    continue
                
                # Clean up subword tokens (##)
                entity_text = entity_text.replace('##', '')
                
                if entity_group in ('CHEMICAL', 'DRUG'):
                    chemicals.append(entity_text)
                    drugs.append(entity_text)  # Drugs are chemicals
                elif entity_group in ('GENE', 'PROTEIN', 'GENE_OR_GENE_PRODUCT'):
                    targets.append(entity_text)
                elif entity_group in ('DISEASE', 'DISORDER', 'PATHOLOGICAL_FORMATION'):
                    diseases.append(entity_text)
                else:
                    # Other biomedical entities - add to chemicals as catch-all
                    chemicals.append(entity_text)
            
            # Deduplicate while preserving order
            drugs = list(dict.fromkeys(drugs))
            targets = list(dict.fromkeys(targets))
            diseases = list(dict.fromkeys(diseases))
            chemicals = list(dict.fromkeys(chemicals))
            
            logger.debug(f"Extracted entities: drugs={drugs}, targets={targets}, diseases={diseases}")
            
            return BiomedicalEntities(
                drugs=drugs,
                targets=targets,
                diseases=diseases,
                chemicals=chemicals
            )
            
        except Exception as e:
            logger.error(f"BioBERT NER extraction failed: {e}")
            return BiomedicalEntities(drugs=[], targets=[], diseases=[], chemicals=[])

    def is_available(self) -> bool:
        """Check if NER service is available."""
        if not self._initialized:
            self._initialize()
        return self.ner_pipeline is not None

    def get_init_error(self) -> Optional[str]:
        """Get initialization error if any."""
        if not self._initialized:
            self._initialize()
        return self._init_error


# Singleton instance for reuse
_biobert_ner_instance = None


def get_biobert_ner() -> BioBERTNER:
    """Get or create the singleton BioBERT NER instance."""
    global _biobert_ner_instance
    if _biobert_ner_instance is None:
        _biobert_ner_instance = BioBERTNER()
    return _biobert_ner_instance


# Convenience function for quick extraction
def extract_biomedical_entities(text: str) -> Dict:
    """
    Quick extraction function for use in query processing.
    
    Args:
        text: Natural language query
        
    Returns:
        Dict with 'drugs', 'targets', 'diseases', 'chemicals' lists
    """
    ner = get_biobert_ner()
    entities = ner.extract_entities(text)
    return entities.to_dict()


if __name__ == "__main__":
    # Quick test
    ner = BioBERTNER()
    test_queries = [
        "Is methotrexate safe for hERG potassium channel cardiotoxicity?",
        "Do Aspirin and Warfarin interact with each other via CYP2C9?",
        "Does caffeine cause hepatotoxicity or DILI?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        entities = ner.extract_entities(query)
        print(f"  Drugs: {entities.drugs}")
        print(f"  Targets: {entities.targets}")
        print(f"  Diseases: {entities.diseases}")
        print(f"  Chemicals: {entities.chemicals}")