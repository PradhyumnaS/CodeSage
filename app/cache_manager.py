import json
import redis
from typing import Optional, Dict, Any
import logging
from .config import settings
from .models import CodeReviewResponse, FeedbackRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True
        )
        self.ttl = settings.CACHE_TTL
        
        try:
            self.redis_client.ping()
            logger.info("Successfully connected to Redis")
        except redis.ConnectionError:
            logger.warning("Could not connect to Redis - caching will be disabled")
            self.redis_client = None
    
    async def cache_review(self, key: str, response: CodeReviewResponse) -> bool:
        if not self.redis_client:
            return False
            
        try:
            response_json = json.dumps(response.dict())
            result = self.redis_client.setex(f"review:{key}", self.ttl, response_json)
            return result
        except Exception as e:
            logger.error(f"Error caching review: {e}")
            return False
    
    async def get_cached_review(self, key: str) -> Optional[CodeReviewResponse]:
        if not self.redis_client:
            return None
            
        try:
            cached = self.redis_client.get(f"review:{key}")
            if cached:
                response_dict = json.loads(cached)
                return CodeReviewResponse(**response_dict)
            return None
        except Exception as e:
            logger.error(f"Error retrieving cached review: {e}")
            return None
    
    async def store_feedback(self, feedback: FeedbackRequest) -> bool:
        if not self.redis_client:
            return False
            
        try:
            feedback_key = f"feedback:{feedback.request_id}"
            feedback_json = json.dumps(feedback.dict())
            result = self.redis_client.set(feedback_key, feedback_json)
            
            self.redis_client.lpush("all_feedback", feedback_json)
            return result
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
            return False
    
    async def get_conversation_history(self, user_id: str) -> list:
        if not self.redis_client:
            return []
            
        try:
            history_key = f"history:{user_id}"
            history = self.redis_client.lrange(history_key, 0, 9)
            return [json.loads(item) for item in history]
        except Exception as e:
            logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    async def add_to_conversation_history(self, user_id: str, data: Dict[str, Any]) -> bool:
        if not self.redis_client:
            return False
            
        try:
            history_key = f"history:{user_id}"
            history_item = json.dumps(data)
            
            self.redis_client.lpush(history_key, history_item)
            self.redis_client.ltrim(history_key, 0, 19)
            
            self.redis_client.expire(history_key, 60 * 60 * 24 * 7)
            return True
        except Exception as e:
            logger.error(f"Error adding to conversation history: {e}")
            return False
