#!/usr/bin/env python3
"""
API Rate Limiting System
========================
Implements token bucket algorithm for API rate limiting
"""

import time
from collections import defaultdict
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
import threading


class RateLimiter:
    """
    Token bucket rate limiter with multiple tiers
    """
    
    def __init__(self):
        # Storage for rate limit buckets
        self.buckets = defaultdict(lambda: {
            'tokens': 0,
            'last_update': time.time()
        })
        
        # Rate limit tiers (requests per minute)
        self.tiers = {
            'default': {'rate': 60, 'burst': 10},      # 60 req/min, burst of 10
            'prediction': {'rate': 30, 'burst': 5},    # 30 req/min for predictions
            'batch': {'rate': 10, 'burst': 2},         # 10 req/min for batch
            'ai': {'rate': 20, 'burst': 5},            # 20 req/min for AI endpoints
            'premium': {'rate': 300, 'burst': 50},     # Premium tier (future)
        }
        
        # Cleanup old entries periodically
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
        self.lock = threading.Lock()
    
    def _get_client_id(self):
        """Get unique client identifier (IP address or API key)"""
        # Try to get API key from headers
        api_key = request.headers.get('X-API-Key')
        if api_key:
            return f"key:{api_key}"
        
        # Fall back to IP address
        if request.headers.get('X-Forwarded-For'):
            ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
        else:
            ip = request.remote_addr
        
        return f"ip:{ip}"
    
    def _cleanup_old_entries(self):
        """Remove old entries to prevent memory bloat"""
        current_time = time.time()
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        with self.lock:
            cutoff_time = current_time - 3600  # Remove entries older than 1 hour
            keys_to_remove = [
                key for key, bucket in self.buckets.items()
                if bucket['last_update'] < cutoff_time
            ]
            for key in keys_to_remove:
                del self.buckets[key]
            
            self.last_cleanup = current_time
            if keys_to_remove:
                print(f"🧹 Cleaned up {len(keys_to_remove)} old rate limit entries")
    
    def _refill_tokens(self, bucket, tier_config):
        """Refill tokens based on elapsed time"""
        current_time = time.time()
        elapsed = current_time - bucket['last_update']
        
        # Calculate tokens to add (rate per second)
        tokens_to_add = elapsed * (tier_config['rate'] / 60.0)
        
        # Update bucket
        bucket['tokens'] = min(
            tier_config['burst'],
            bucket['tokens'] + tokens_to_add
        )
        bucket['last_update'] = current_time
    
    def check_rate_limit(self, tier='default', cost=1):
        """
        Check if request is within rate limit
        
        Args:
            tier: Rate limit tier to use
            cost: Number of tokens to consume (default 1)
        
        Returns:
            (allowed, retry_after, remaining)
        """
        client_id = self._get_client_id()
        tier_config = self.tiers.get(tier, self.tiers['default'])
        
        # Cleanup periodically
        self._cleanup_old_entries()
        
        with self.lock:
            bucket_key = f"{client_id}:{tier}"
            bucket = self.buckets[bucket_key]
            
            # Initialize bucket if new
            if bucket['tokens'] == 0 and bucket['last_update'] == time.time():
                bucket['tokens'] = tier_config['burst']
            
            # Refill tokens
            self._refill_tokens(bucket, tier_config)
            
            # Check if enough tokens
            if bucket['tokens'] >= cost:
                bucket['tokens'] -= cost
                remaining = int(bucket['tokens'])
                return True, 0, remaining
            else:
                # Calculate retry after (seconds until 1 token available)
                retry_after = int((cost - bucket['tokens']) / (tier_config['rate'] / 60.0))
                return False, retry_after, 0
    
    def get_rate_limit_headers(self, tier='default'):
        """Get rate limit headers for response"""
        tier_config = self.tiers.get(tier, self.tiers['default'])
        client_id = self._get_client_id()
        bucket_key = f"{client_id}:{tier}"
        
        with self.lock:
            bucket = self.buckets[bucket_key]
            remaining = int(bucket.get('tokens', tier_config['burst']))
        
        return {
            'X-RateLimit-Limit': str(tier_config['rate']),
            'X-RateLimit-Remaining': str(max(0, remaining)),
            'X-RateLimit-Reset': str(int(time.time() + 60))
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(tier='default', cost=1):
    """
    Decorator for rate limiting Flask routes
    
    Usage:
        @app.route('/api/predict')
        @rate_limit(tier='prediction', cost=1)
        def predict():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check rate limit
            allowed, retry_after, remaining = rate_limiter.check_rate_limit(tier, cost)
            
            if not allowed:
                # Rate limit exceeded
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Please try again in {retry_after} seconds.',
                    'retry_after': retry_after,
                    'tier': tier
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(retry_after)
                response.headers.update(rate_limiter.get_rate_limit_headers(tier))
                return response
            
            # Execute the function
            result = f(*args, **kwargs)
            
            # Add rate limit headers to response
            if hasattr(result, 'headers'):
                result.headers.update(rate_limiter.get_rate_limit_headers(tier))
            
            return result
        
        return decorated_function
    return decorator


def get_rate_limit_info():
    """Get current rate limit status for client"""
    client_id = rate_limiter._get_client_id()
    
    info = {
        'client_id': client_id.split(':')[1],  # Hide prefix
        'tiers': {}
    }
    
    for tier_name, tier_config in rate_limiter.tiers.items():
        bucket_key = f"{client_id}:{tier_name}"
        bucket = rate_limiter.buckets[bucket_key]
        
        info['tiers'][tier_name] = {
            'rate_limit': tier_config['rate'],
            'burst_limit': tier_config['burst'],
            'remaining': int(bucket.get('tokens', tier_config['burst'])),
            'reset_in': 60  # seconds
        }
    
    return info


if __name__ == "__main__":
    # Test rate limiter
    print("🧪 Testing Rate Limiter")
    print("=" * 60)
    
    limiter = RateLimiter()
    
    # Simulate requests
    print("\nSimulating 15 requests to 'prediction' tier (limit: 30/min, burst: 5):")
    for i in range(15):
        allowed, retry_after, remaining = limiter.check_rate_limit('prediction', cost=1)
        status = "✅ Allowed" if allowed else f"❌ Blocked (retry in {retry_after}s)"
        print(f"Request {i+1}: {status} (Remaining: {remaining})")
        time.sleep(0.1)  # Small delay
    
    print("\n" + "=" * 60)
    print("Rate limiter test complete!")
