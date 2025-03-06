import redis
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, redis_host: str, redis_port: int, rate_limit: int, window_minutes: int):
        self.rate_limit = rate_limit
        self.window_seconds = window_minutes * 60
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("Successfully connected to Redis for rate limiting")
        except redis.ConnectionError:
            logger.warning("Could not connect to Redis - rate limiting will be disabled")
            self.redis_client = None
    
    async def check_rate_limit(self, user_id: str) -> bool:
        if not self.redis_client:
            return True
            
        try:
            current_time = int(time.time())
            key = f"ratelimit:{user_id}"
            
            self.redis_client.zremrangebyscore(key, 0, current_time - self.window_seconds)
            
            recent_requests = self.redis_client.zcard(key)
            
            if recent_requests < self.rate_limit:
                pipeline = self.redis_client.pipeline()
                pipeline.zadd(key, {str(current_time): current_time})
                pipeline.expire(key, self.window_seconds)
                pipeline.execute()
                return True
                
            return False
        except Exception as e:
            logger.error(f"Error in rate limiting: {e}")
            return True
