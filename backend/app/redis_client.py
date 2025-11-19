import redis
import json
from typing import Any, Optional
from .config import settings

class RedisClient:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            decode_responses=True
        )
    
    async def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set a key-value pair in Redis"""
        try:
            serialized_value = json.dumps(value) if not isinstance(value, str) else value
            return self.redis_client.set(key, serialized_value, ex=expire)
        except Exception as e:
            print(f"Redis SET error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[Any]:
        """Get a value from Redis"""
        try:
            value = self.redis_client.get(key)
            if value is None:
                return None
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        except Exception as e:
            print(f"Redis GET error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete a key from Redis"""
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            print(f"Redis DELETE error: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if a key exists in Redis"""
        try:
            return bool(self.redis_client.exists(key))
        except Exception as e:
            print(f"Redis EXISTS error: {e}")
            return False
    
    async def set_hash(self, key: str, mapping: dict, expire: Optional[int] = None) -> bool:
        """Set a hash in Redis"""
        try:
            result = self.redis_client.hset(key, mapping=mapping)
            if expire:
                self.redis_client.expire(key, expire)
            return bool(result)
        except Exception as e:
            print(f"Redis HSET error: {e}")
            return False
    
    async def get_hash(self, key: str) -> Optional[dict]:
        """Get a hash from Redis"""
        try:
            return self.redis_client.hgetall(key)
        except Exception as e:
            print(f"Redis HGETALL error: {e}")
            return None

# Create global Redis client instance
redis_client = RedisClient()
