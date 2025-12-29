#!/usr/bin/env python3
"""
Prediction Caching System
Caches toxicity predictions to improve performance by 100-1000x
"""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class PredictionCache:
    """In-memory cache for toxicity predictions"""
    
    def __init__(self, ttl_seconds: int = 3600, max_size: int = 10000):
        """
        Initialize prediction cache
        
        Args:
            ttl_seconds: Time to live for cache entries (default 1 hour)
            max_size: Maximum number of cached predictions (default 10000)
        """
        self.cache: Dict[str, tuple] = {}
        self.ttl = ttl_seconds
        self.max_size = max_size
        self.hits = 0
        self.misses = 0
        
    def _hash_smiles(self, smiles: str) -> str:
        """Generate hash key for SMILES string"""
        try:
            normalized_smiles = smiles.strip().upper()
            return hashlib.md5(normalized_smiles.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing SMILES: {e}")
            return ""
    
    def get(self, smiles: str) -> Optional[Dict[str, Any]]:
        """
        Get cached prediction result
        
        Args:
            smiles: SMILES string to look up
            
        Returns:
            Cached prediction result or None if not found/expired
        """
        try:
            key = self._hash_smiles(smiles)
            if not key or key not in self.cache:
                self.misses += 1
                return None
            
            result, timestamp = self.cache[key]
            
            # Check if cache entry has expired
            if datetime.now() - timestamp > timedelta(seconds=self.ttl):
                logger.info(f"Cache entry expired for SMILES: {smiles}")
                del self.cache[key]
                self.misses += 1
                return None
            
            self.hits += 1
            logger.info(f"✅ Cache HIT - SMILES: {smiles[:30]}... | Hit ratio: {self.get_hit_ratio():.1%}")
            return result
            
        except Exception as e:
            logger.error(f"Error retrieving from cache: {e}")
            self.misses += 1
            return None
    
    def set(self, smiles: str, result: Dict[str, Any]) -> bool:
        """
        Store prediction result in cache
        
        Args:
            smiles: SMILES string (key)
            result: Prediction result to cache
            
        Returns:
            True if successfully cached, False otherwise
        """
        try:
            # Check cache size and evict oldest if needed
            if len(self.cache) >= self.max_size:
                self._evict_oldest()
            
            key = self._hash_smiles(smiles)
            if not key:
                return False
            
            self.cache[key] = (result, datetime.now())
            logger.info(f"📦 Cache SET - SMILES: {smiles[:30]}... | Cache size: {len(self.cache)}/{self.max_size}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing in cache: {e}")
            return False
    
    def _evict_oldest(self):
        """Remove oldest cache entry when max size reached"""
        try:
            if not self.cache:
                return
            
            oldest_key = min(self.cache.keys(), 
                           key=lambda k: self.cache[k][1])
            del self.cache[oldest_key]
            logger.info(f"🗑️  Evicted oldest cache entry. Cache size: {len(self.cache)}/{self.max_size}")
            
        except Exception as e:
            logger.error(f"Error evicting cache: {e}")
    
    def clear(self) -> None:
        """Clear entire cache"""
        try:
            old_size = len(self.cache)
            self.cache.clear()
            self.hits = 0
            self.misses = 0
            logger.info(f"🗑️  Cache cleared. Removed {old_size} entries")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_ratio = self.hits / total_requests if total_requests > 0 else 0
        
        return {
            'cache_size': len(self.cache),
            'max_size': self.max_size,
            'cache_hits': self.hits,
            'cache_misses': self.misses,
            'total_requests': total_requests,
            'hit_ratio': f"{hit_ratio:.1%}",
            'ttl_seconds': self.ttl,
            'usage_percentage': f"{(len(self.cache) / self.max_size * 100):.1f}%"
        }
    
    def get_cache_size_mb(self) -> float:
        """Estimate cache size in MB"""
        try:
            total_size = 0
            for key, (result, _) in self.cache.items():
                total_size += len(key)
                if isinstance(result, dict):
                    total_size += len(json.dumps(result).encode())
            return total_size / (1024 * 1024)
        except Exception:
            return 0.0


class CachedPredictionWrapper:
    """Wrapper to automatically cache predictions"""
    
    def __init__(self, predictor, cache: Optional[PredictionCache] = None):
        """
        Initialize wrapper
        
        Args:
            predictor: ML predictor instance
            cache: PredictionCache instance (creates new if not provided)
        """
        self.predictor = predictor
        self.cache = cache or PredictionCache()
    
    def predict_single(self, smiles: str) -> Dict[str, Any]:
        """
        Predict with caching
        
        Args:
            smiles: SMILES string to predict
            
        Returns:
            Prediction result (from cache or fresh)
        """
        # Try to get from cache first
        cached_result = self.cache.get(smiles)
        if cached_result is not None:
            return cached_result
        
        # Get fresh prediction
        result = self.predictor.predict(smiles)
        
        # Store in cache
        self.cache.set(smiles, result)
        
        return result
    
    def predict_batch(self, smiles_list: list) -> list:
        """
        Batch predict with caching
        
        Args:
            smiles_list: List of SMILES strings
            
        Returns:
            List of prediction results
        """
        results = []
        uncached_smiles = []
        uncached_indices = []
        
        # Check cache for each SMILES
        for i, smiles in enumerate(smiles_list):
            cached = self.cache.get(smiles)
            if cached is not None:
                results.append((i, cached))
            else:
                uncached_smiles.append(smiles)
                uncached_indices.append(i)
        
        # Predict uncached molecules
        if uncached_smiles:
            fresh_results = self.predictor.predict_batch(uncached_smiles)
            
            # Cache and store results
            for j, smiles in enumerate(uncached_smiles):
                result = fresh_results[j]
                self.cache.set(smiles, result)
                results.append((uncached_indices[j], result))
        
        # Sort results by original index
        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()
    
    def clear_cache(self) -> None:
        """Clear cache"""
        self.cache.clear()


# Global cache instance
prediction_cache = PredictionCache(
    ttl_seconds=3600,  # 1 hour TTL
    max_size=10000      # Max 10000 predictions
)
