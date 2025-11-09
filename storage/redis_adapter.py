"""
Redis Cache Adapter
High-performance caching for peer snapshots, multiples, and frequently accessed data
"""

from typing import Dict, List, Optional, Any
import json
from datetime import timedelta
from loguru import logger

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available")

from config.settings import get_settings


class RedisAdapter:
    """Redis cache adapter for FMNA platform"""
    
    def __init__(self):
        """Initialize Redis connection"""
        if not REDIS_AVAILABLE:
            logger.error("Redis not installed. Install: pip install redis")
            self.enabled = False
            return
        
        settings = get_settings()
        
        try:
            self.client = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=True
            )
            
            # Test connection
            self.client.ping()
            self.enabled = True
            logger.info(f"Redis connected: {settings.redis_host}:{settings.redis_port}")
            
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            self.enabled = False
    
    def cache_peer_snapshot(
        self,
        symbol: str,
        peer_data: Dict[str, Any],
        ttl_hours: int = 24
    ) -> bool:
        """
        Cache peer company snapshot
        
        Args:
            symbol: Company symbol
            peer_data: Peer metrics and multiples
            ttl_hours: Time-to-live in hours
            
        Returns:
            Success status
        """
        if not self.enabled:
            return False
        
        try:
            key = f"peer_snapshot:{symbol}"
            value = json.dumps(peer_data)
            
            self.client.setex(
                key,
                timedelta(hours=ttl_hours),
                value
            )
            
            logger.debug(f"Cached peer snapshot for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Cache write failed: {str(e)}")
            return False
    
    def get_peer_snapshot(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached peer snapshot"""
        if not self.enabled:
            return None
        
        try:
            key = f"peer_snapshot:{symbol}"
            value = self.client.get(key)
            
            if value:
                logger.debug(f"Cache hit for peer snapshot: {symbol}")
                return json.loads(value)
            
            logger.debug(f"Cache miss for peer snapshot: {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Cache read failed: {str(e)}")
            return None
    
    def cache_valuation(
        self,
        symbol: str,
        valuation_data: Dict[str, Any],
        ttl_hours: int = 12
    ) -> bool:
        """Cache valuation results"""
        if not self.enabled:
            return False
        
        try:
            key = f"valuation:{symbol}"
            value = json.dumps(valuation_data, default=str)
            
            self.client.setex(
                key,
                timedelta(hours=ttl_hours),
                value
            )
            
            logger.debug(f"Cached valuation for {symbol}")
            return True
            
        except Exception as e:
            logger.error(f"Cache write failed: {str(e)}")
            return False
    
    def get_valuation(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached valuation"""
        if not self.enabled:
            return None
        
        try:
            key = f"valuation:{symbol}"
            value = self.client.get(key)
            
            if value:
                logger.debug(f"Cache hit for valuation: {symbol}")
                return json.loads(value)
            
            return None
            
        except Exception as e:
            logger.error(f"Cache read failed: {str(e)}")
            return None
    
    def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        if not self.enabled:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                count = self.client.delete(*keys)
                logger.info(f"Invalidated {count} cache entries")
                return count
            return 0
            
        except Exception as e:
            logger.error(f"Cache invalidation failed: {str(e)}")
            return 0
    
    def close(self):
        """Close Redis connection"""
        if self.enabled:
            self.client.close()
            logger.info("Redis connection closed")


# Example usage
if __name__ == "__main__":
    cache = RedisAdapter()
    
    if cache.enabled:
        # Cache peer data
        peer_data = {
            'symbol': 'MSFT',
            'ev_ebitda': 25.5,
            'ev_revenue': 8.2,
            'market_cap': 2_750_000_000_000
        }
        
        cache.cache_peer_snapshot('MSFT', peer_data)
        
        # Retrieve
        retrieved = cache.get_peer_snapshot('MSFT')
        print(f"Retrieved: {retrieved}")
        
        cache.close()
