"""
Database Models for Supabase Integration
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import uuid

@dataclass
class PredictionRecord:
    """Data model for toxicity predictions"""
    id: str
    smiles: str
    molecule_name: Optional[str]
    endpoints: Dict[str, Any]
    ai_analysis: Optional[str]
    user_id: Optional[str]
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase storage"""
        data = asdict(self)
        data['endpoints'] = json.dumps(self.endpoints) if isinstance(self.endpoints, dict) else self.endpoints
        data['metadata'] = json.dumps(self.metadata) if self.metadata else None
        data['created_at'] = self.created_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PredictionRecord':
        """Create from Supabase data"""
        # Parse JSON fields
        if isinstance(data.get('endpoints'), str):
            data['endpoints'] = json.loads(data['endpoints'])
        if isinstance(data.get('metadata'), str) and data.get('metadata'):
            data['metadata'] = json.loads(data['metadata'])
        
        # Parse datetime
        if isinstance(data.get('created_at'), str):
            data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        return cls(**data)

@dataclass
class UserFeedback:
    """Data model for user feedback on predictions"""
    id: str
    prediction_id: str
    user_id: Optional[str]
    rating: int  # 1-5 stars
    comment: Optional[str]
    is_accurate: Optional[bool]
    created_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase storage"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        return data

@dataclass
class MoleculeLibrary:
    """Data model for molecule library"""
    id: str
    name: str
    smiles: str
    category: str
    description: Optional[str]
    known_toxicity: Optional[Dict[str, Any]]
    drug_bank_id: Optional[str]
    cas_number: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Supabase storage"""
        data = asdict(self)
        data['known_toxicity'] = json.dumps(self.known_toxicity) if self.known_toxicity else None
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data

class DatabaseService:
    """Service class for database operations"""
    
    def __init__(self, supabase_client):
        self.client = supabase_client
    
    async def save_prediction(self, prediction: PredictionRecord) -> bool:
        """Save prediction to database"""
        try:
            result = self.client.table('predictions').insert(prediction.to_dict()).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error saving prediction: {e}")
            return False
    
    async def get_prediction(self, prediction_id: str) -> Optional[PredictionRecord]:
        """Get prediction by ID"""
        try:
            result = self.client.table('predictions').select("*").eq('id', prediction_id).execute()
            if result.data:
                return PredictionRecord.from_dict(result.data[0])
            return None
        except Exception as e:
            print(f"Error getting prediction: {e}")
            return None
    
    async def get_user_predictions(self, user_id: str, limit: int = 50) -> List[PredictionRecord]:
        """Get user's prediction history"""
        try:
            result = (self.client.table('predictions')
                     .select("*")
                     .eq('user_id', user_id)
                     .order('created_at', desc=True)
                     .limit(limit)
                     .execute())
            
            return [PredictionRecord.from_dict(data) for data in result.data]
        except Exception as e:
            print(f"Error getting user predictions: {e}")
            return []
    
    async def save_feedback(self, feedback: UserFeedback) -> bool:
        """Save user feedback"""
        try:
            result = self.client.table('user_feedback').insert(feedback.to_dict()).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False
    
    async def get_molecule_library(self, category: Optional[str] = None, limit: int = 100) -> List[MoleculeLibrary]:
        """Get molecules from library"""
        try:
            query = self.client.table('molecule_library').select("*")
            
            if category:
                query = query.eq('category', category)
            
            result = query.order('name').limit(limit).execute()
            
            return [MoleculeLibrary(**data) for data in result.data]
        except Exception as e:
            print(f"Error getting molecule library: {e}")
            return []
    
    async def add_molecule_to_library(self, molecule: MoleculeLibrary) -> bool:
        """Add molecule to library"""
        try:
            result = self.client.table('molecule_library').insert(molecule.to_dict()).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"Error adding molecule to library: {e}")
            return False