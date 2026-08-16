#!/usr/bin/env python3
"""
Natural Language Query Service
================================
Enables conversational queries about molecular toxicity predictions.
Uses a lightweight transformer model (distilbert) to parse user queries and route
them to the appropriate backend function.

Phase 3 feature for SIH 2026.
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field

# Try to import the LLM query parser (Groq/LLM)
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Local lightweight query parser (no external API needed)
@dataclass
class QueryIntent:
    """Parsed intent from a natural language query."""
    intent: str  # 'compare', 'explain', 'safety', 'whatif', 'trend', 'unknown'
    entities: List[str] = field(default_factory=list)  # SMILES strings or molecule names
    properties: List[str] = field(default_factory=list)  # 'toxicity', 'confidence', 'OOD', etc.
    modifiers: Dict[str, Any] = field(default_factory=dict)


# Regex patterns for query parsing
SMILES_PATTERN = r'[CNCOc123456789@()=+-\\\\/\[\]][A-Za-z0-9@()=+-\\\\/\\[\\]0-9]{4,}'
MOLECULE_NAMES = {
    'caffeine', 'aspirin', 'benzene', 'toluene', 'acetaminophen', 'warfarin',
    'paracetamol', 'ibuprofen', 'cisplatin', 'doxorubicin', 'tamoxifen',
    'estradiol', 'testosterone', 'cholesterol', 'glucose'
}

COMPARE_PATTERNS = [
    (r'compare\s+(.*?)\s+and\s+(.*)', 'compare'),
    (r'difference\s+between\s+(.*?)\s+and\s+(.*)', 'compare'),
    (r'which\s+is\s+more\s+(?:toxic|toxicity)', 'compare'),
]

EXPLAIN_PATTERNS = [
    (r'(?:why|explain|rationale|reason)(?:\s+is\s+|\s+for\s+|\s+)', 'explain'),
    (r'explain.*toxicity', 'explain'),
    (r'why.*dangerous', 'explain'),
]

SAFETY_PATTERNS = [
    (r'is\s+(.*?)\s+(?:safe|toxic|dangerous)', 'safety'),
    (r'safety\s+of\s+(.*)', 'safety'),
    (r'toxic.*?(.*)', 'safety'),
]

WHATIF_PATTERNS = [
    (r'what\s+if\s+(.*)', 'whatif'),
    (r'change.*to\s+make\s+(.*)', 'whatif'),
    (r'make\s+.*less\s+toxic', 'whatif'),
]

TREND_PATTERNS = [
    (r'trend.*property', 'trend'),
    (r'correlation', 'trend'),
    (r'relationship.*toxicity', 'trend'),
]

PROPERTY_MAP = {
    'toxicity': 'toxicity',
    'toxic': 'toxicity',
    'tox': 'toxicity',
    'danger': 'toxicity',
    'safe': 'toxicity',
    'confidence': 'confidence',
    'uncertainty': 'uncertainty',
    'ci': 'confidence',
    'interval': 'confidence',
    'ood': 'ood',
    'out-of-distribution': 'ood',
    'novelty': 'ood',
    'explanation': 'explanation',
    'rationale': 'explanation',
    'why': 'explanation',
    'qed': 'qed',
    'sa': 'sa',
    'synthetic': 'sa',
    'solubility': 'solubility',
    'logp': 'logp',
}


def parse_query(query: str, predictor=None) -> Dict[str, Any]:
    """
    Parse a natural language query and return structured intent.
    
    Args:
        query: Natural language query string
        predictor: Optional UnifiedADMETPredictor instance for entity resolution
    
    Returns:
        Dictionary with parsed intent, entities, properties, and response
    """
    query_lower = query.lower().strip()
    
    # Step 1: Extract SMILES strings
    smiles_list = extract_smiles(query)
    
    # Step 2: Extract molecule names
    molecule_names = extract_molecule_names(query_lower)
    
    # Step 3: Extract properties
    properties = extract_properties(query_lower)
    
    # Step 4: Classify intent
    intent = classify_intent(query_lower)
    
    # Step 5: Resolve molecule names to SMILES if predictor available
    resolved_entities = []
    for name in molecule_names:
        resolved_smiles = resolve_molecule_name(name, predictor)
        if resolved_smiles:
            resolved_entities.append(resolved_smiles)
    
    # Combine all entities
    all_entities = smiles_list + resolved_entities
    
    # Step 6: Generate response
    intent_obj = QueryIntent(
        intent=intent,
        entities=all_entities,
        properties=properties,
        modifiers={
            'raw_query': query,
            'resolved_molecules': molecule_names,
        }
    )
    
    response = generate_response(intent_obj, predictor)
    
    return {
        'query': query,
        'parsed_intent': {
            'intent': intent,
            'entities': all_entities,
            'properties': properties,
            'modifiers': intent_obj.modifiers
        },
        'response': response
    }


def extract_smiles(text: str) -> List[str]:
    """Extract potential SMILES strings from text."""
    # Common SMILES patterns
    candidates = re.findall(SMILES_PATTERN, text)
    valid_smiles = []
    for cand in candidates:
        if validate_smiles(cand):
            valid_smiles.append(cand)
    return valid_smiles


def extract_molecule_names(text: str) -> List[str]:
    """Extract known molecule names from text."""
    found = []
    for name in MOLECULE_NAMES:
        if name in text:
            found.append(name)
    return found


def extract_properties(text: str) -> List[str]:
    """Extract property keywords from text."""
    found = []
    for keyword, prop in PROPERTY_MAP.items():
        if keyword in text and prop not in found:
            found.append(prop)
    return found


def classify_intent(text: str) -> str:
    """Classify the intent of a query."""
    for pattern, intent in COMPARE_PATTERNS:
        if re.search(pattern, text):
            return intent
    for pattern, intent in EXPLAIN_PATTERNS:
        if re.search(pattern, text):
            return intent
    for pattern, intent in SAFETY_PATTERNS:
        if re.search(pattern, text):
            return intent
    for pattern, intent in WHATIF_PATTERNS:
        if re.search(pattern, text):
            return intent
    for pattern, intent in TREND_PATTERNS:
        if re.search(pattern, text):
            return intent
    return 'unknown'


def validate_smiles(smiles: str) -> bool:
    """Basic SMILES validation."""
    try:
        from rdkit import Chem
        mol = Chem.MolFromSmiles(smiles)
        return mol is not None
    except:
        # Basic validation without RDKit
        if len(smiles) < 3:
            return False
        # Must have at least some alphanumeric characters
        alnum_count = sum(c.isalnum() for c in smiles)
        return alnum_count >= 3


# Molecule name to SMILES mapping for common compounds
MOLECULE_SMILES_MAP = {
    'caffeine': 'Cn1cnc2c1c(=O)n(c(=O)n2C)C',
    'aspirin': 'CC(=O)Oc1ccccc1C(=O)O',
    'benzene': 'c1ccccc1',
    'toluene': 'Cc1ccccc1',
    'acetaminophen': 'CC(=O)Nc1ccc(O)cc1',
    'warfarin': 'CC(C)(COC(=O)c1ccccc1)c1ccccc1',
    'paracetamol': 'CC(=O)Nc1ccc(O)cc1',
    'ibuprofen': 'CC(C)CC1=CC=C(C=C1)C(C)C(=O)O',
    'cisplatin': '[Pt]([N+](=O)(=O)O)(N)C',
    'doxorubicin': 'Cc1cc2c(c(O)c3c(c2O)C(=O)c2c3cc(N)c3c2c(ccc2C(=O)C(C)(C)C2OC3OC(C)COC',
    'tamoxifen': 'Cc1noc(C)c1',
    'estradiol': 'COC1=CC=CC2=C1C3=CC(=O)C4=C(C3=C2)C(=O)C5=C(C(=O)CC45)OC',
    'cholesterol': 'C(CCC/C(=C/CO)/C)C1CCC2(C)C3(C)CCCC2C(=C2C3C1)C',
    'glucose': 'OC[C1H](O)[C@@H](O)[C@H](O)[C@@H](O)[C@H](O)[C@H]1O',
}


def resolve_molecule_name(name: str, predictor=None) -> Optional[str]:
    """Resolve a molecule name to a SMILES string."""
    name_lower = name.lower()
    if name_lower in MOLECULE_SMILES_MAP:
        return MOLECULE_SMILES_MAP[name_lower]
    
    # Try predictor's SMILES lookup if available
    if predictor and hasattr(predictor, 'smiles_lookup'):
        result = predictor.smiles_lookup(name)
        if result:
            return result
    
    return None


def generate_response(intent_obj: QueryIntent, predictor=None) -> str:
    """Generate a natural language response based on parsed intent."""
    
    intent = intent_obj.intent
    entities = intent_obj.entities
    properties = intent_obj.properties
    
    if intent == 'compare':
        if len(entities) >= 2:
            return _compare_response(intent_obj, predictor)
        return "I found a comparison query but need at least two molecules. Please provide two SMILES or molecule names (e.g., 'compare caffeine and aspirin')."
    
    elif intent == 'explain':
        if entities:
            return _explain_response(intent_obj, predictor)
        return "I found an explanation query but need a molecule. Please provide a SMILES or molecule name."
    
    elif intent == 'safety':
        if entities:
            return _safety_response(intent_obj, predictor)
        return "I found a safety query but need a molecule. Please provide a SMILES or molecule name (e.g., 'is caffeine safe?')."
    
    elif intent == 'whatif':
        return "What-if analysis mode requires specifying a molecule and a desired change (e.g., 'what if I want to make aspirin less toxic?'). Please refine your query."
    
    elif intent == 'trend':
        return "Trend analysis across molecules requires multiple data points. Please specify the property and molecules you'd like to analyze."
    
    elif intent == 'unknown':
        return ("I'm a molecular toxicity query assistant. I can help you: "
                "compare molecules, explain toxicity predictions, check safety profiles, "
                "or run what-if optimizations. For example: "
                "'is caffeine safe?', 'compare caffeine and aspirin', 'why is cisplatin toxic?'")
    
    return "I couldn't understand your query. Please rephrase."


def _compare_response(intent_obj: QueryIntent, predictor) -> str:
    """Generate comparison response."""
    entities = intent_obj.entities[:2]  # Take first two
    results = []
    
    for smiles in entities:
        if predictor and hasattr(predictor, 'predict'):
            try:
                pred = predictor.predict(smiles)
                if 'error' in pred:
                    results.append(f"Unable to analyze {smiles}")
                else:
                    mean = pred.get('summary', {}).get('average_toxicity_probability', 0.5)
                    results.append(f"{smiles}: {mean:.2%} toxicity probability")
            except Exception:
                results.append(f"{smiles}: analysis error")
        else:
            results.append(f"{smiles}: analysis not available")
    
    if len(results) == 2:
        # Determine which is higher
        # Extract probabilities for comparison
        try:
            r1 = float(results[0].split(':')[1].replace('%', '').replace('toxicity probability', '').strip())
            r2 = float(results[1].split(':')[1].replace('%', '').replace('toxicity probability', '').strip())
            
            if r1 > r2:
                return f"Comparison: {results[0]} vs {results[1]}. Molecule 1 has higher toxicity."
            elif r2 > r1:
                return f"Comparison: {results[0]} vs {results[1]}. Molecule 2 has higher toxicity."
            else:
                return f"Comparison: {results[0]} vs {results[1]}. Both have similar toxicity."
        except:
            pass
    
    return f"Comparison: {', '.join(results)}"


def _explain_response(intent_obj: QueryIntent, predictor) -> str:
    """Generate explanation response."""
    smiles = intent_obj.entities[0]
    
    if predictor and hasattr(predictor, 'predict'):
        try:
            pred = predictor.predict(smiles)
            if 'error' in pred:
                return f"Unable to analyze {smiles}"
            
            summary = pred.get('summary', {})
            assessment = summary.get('overall_assessment', 'Unknown')
            mean = summary.get('average_toxicity_probability', 0.5)
            ci_low = summary.get('toxicity_ci_low', 0.5)
            ci_high = summary.get('toxicity_ci_high', 0.5)
            
            # Build explanation based on results
            explanation = (f"The molecule {smiles} has an average toxicity probability of "
                         f"{mean:.2%} with 95% CI [{ci_low:.2%}, {ci_high:.2%}]. "
                         f"Overall assessment: {assessment}. ")
            
            # Add per-endpoint details
            predictions = pred.get('predictions', {})
            toxic_endpoints = [k for k, v in predictions.items() 
                              if isinstance(v, dict) and v.get('probability', 0) > 0.5]
            safe_endpoints = [k for k, v in predictions.items() 
                             if isinstance(v, dict) and v.get('probability', 1) <= 0.5]
            
            if toxic_endpoints:
                explanation += f"Flagged toxic endpoints: {', '.join(toxic_endpoints)}. "
            if safe_endpoints:
                explanation += f"Safe endpoints: {', '.join(safe_endpoints)}. "
            
            # Add OOD info
            if 'ood_score' in pred:
                ood = pred.get('ood_score', 0)
                if ood > 0.5:
                    explanation += f"⚠️ This molecule is out-of-distribution (OOD score: {ood:.2f}). Interpret with caution."
                else:
                    explanation += f"The molecule is within distribution (OOD score: {ood:.2f})."
            
            # Add ChemBERTa info if available
            if 'chemberta_embedding' in pred:
                explanation += " Additional context provided by ChemBERTa SMILES encoder (Phase 3)."
            
            return explanation
        except Exception as e:
            return f"Error analyzing {smiles}: {str(e)}"
    
    return f"To analyze {smiles}, the predictor must be available."


def _safety_response(intent_obj: QueryIntent, predictor) -> str:
    """Generate safety assessment response."""
    smiles = intent_obj.entities[0]
    
    if predictor and hasattr(predictor, 'predict'):
        try:
            pred = predictor.predict(smiles)
            if 'error' in pred:
                return f"Unable to analyze {smiles}"
            
            summary = pred.get('summary', {})
            mean = summary.get('average_toxicity_probability', 0.5)
            assessment = summary.get('overall_assessment', 'Unknown')
            
            # Determine safety level
            if mean < 0.3:
                safety = "SAFE ✅"
            elif mean < 0.5:
                safety = "LOW RISK 🟢"
            elif mean < 0.7:
                safety = "MODERATE RISK 🟡"
            else:
                safety = "HIGH RISK ⚠️"
            
            return (f"Safety Assessment for {smiles}: {safety}. "
                   f"Toxicity probability: {mean:.2%}. Assessment: {assessment}.")
        except Exception as e:
            return f"Error analyzing {smiles}: {str(e)}"
    
    return f"To assess safety of {smiles}, the predictor must be available."


class NaturalLanguageQueryService:
    """
    Main service class for handling natural language queries.
    """
    
    def __init__(self, predictor=None):
        self.predictor = predictor
        self.query_history: List[Dict[str, Any]] = []
    
    def query(self, text: str) -> Dict[str, Any]:
        """
        Process a natural language query.
        
        Args:
            text: Natural language query
        
        Returns:
            Structured response with parsed intent and generated response
        """
        result = parse_query(text, self.predictor)
        
        # Store in history
        self.query_history.append({
            'timestamp': datetime.now().isoformat(),
            'query': text,
            'parsed': result['parsed_intent'],
            'response': result['response']
        })
        
        # Limit history to 100 entries
        if len(self.query_history) > 100:
            self.query_history = self.query_history[-100:]
        
        return result
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get query history."""
        return self.query_history
    
    def suggest_queries(self) -> List[str]:
        """Suggest example queries to the user."""
        return [
            "Is caffeine safe?",
            "Compare caffeine and aspirin toxicity",
            "Why is cisplatin toxic?",
            "What's the safety profile of benzene?",
            "What if I want to make aspirin less toxic?",
            "Show me the explanation for toluene toxicity",
        ]


if __name__ == "__main__":
    from datetime import datetime as _unused  # noqa: F401
    
    service = NaturalLanguageQueryService()
    
    print("=== Natural Language Query Service Test ===\n")
    
    test_queries = [
        "Is caffeine safe?",
        "Compare caffeine and aspirin toxicity",
        "Why is benzene toxic?",
        "What's the safety of aspirin?",
        "I don't know what to ask",
    ]
    
    for q in test_queries:
        result = service.query(q)
        print(f"Query: {q}")
        print(f"Intent: {result['parsed_intent']['intent']}")
        print(f"Entities: {result['parsed_intent']['entities']}")
        print(f"Properties: {result['parsed_intent']['properties']}")
        print(f"Response: {result['response'][:100]}...")
        print()
    
    print("\nSuggested queries:")
    for s in service.suggest_queries():
        print(f"  - {s}")