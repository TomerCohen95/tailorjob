import redis.asyncio as redis
import json
import uuid
from typing import Dict, Any, Optional
from app.config import settings

class QueueService:
    """Service for managing background job queues using Redis"""
    
    def __init__(self):
        # Redis is optional - if not configured, queue operations will be no-ops
        self.redis = None
        if settings.UPSTASH_REDIS_URL:
            try:
                self.redis = redis.from_url(
                    settings.UPSTASH_REDIS_URL,
                    decode_responses=True,
                    ssl_cert_reqs=None  # Disable SSL verification for development
                )
            except Exception as e:
                print(f"Warning: Could not connect to Redis: {e}")
        
        # Queue names
        self.CV_PARSE_QUEUE = "queue:cv-parse"
        self.AI_TAILOR_QUEUE = "queue:ai-tailor"
    
    async def enqueue(self, queue_name: str, data: Dict[str, Any]) -> str:
        """Add a job to the queue"""
        job_id = data.get("id", str(uuid.uuid4()))
        
        if self.redis:
            # Add job to queue (Redis list)
            await self.redis.lpush(queue_name, json.dumps(data))
            
            # Set initial job status with 1 hour TTL
            await self.redis.setex(f"job:{job_id}:status", 3600, "queued")
        else:
            # Redis not configured - log warning
            print(f"Warning: Redis not configured. Job {job_id} not queued.")
        
        return job_id
    
    async def dequeue(self, queue_name: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """Get a job from the queue (blocking operation)"""
        if not self.redis:
            return None
            
        result = await self.redis.brpop(queue_name, timeout=timeout)
        
        if result:
            _, job_data = result
            return json.loads(job_data)
        
        return None
    
    async def set_job_status(self, job_id: str, status: str, result: Any = None):
        """Update job status and optionally store result"""
        if not self.redis:
            return
            
        await self.redis.setex(f"job:{job_id}:status", 3600, status)
        
        if result:
            await self.redis.setex(
                f"job:{job_id}:result",
                3600,
                json.dumps(result)
            )
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the current status of a job"""
        if not self.redis:
            return {
                "status": "unavailable",
                "result": None
            }
            
        status = await self.redis.get(f"job:{job_id}:status")
        result = await self.redis.get(f"job:{job_id}:result")
        
        return {
            "status": status or "not_found",
            "result": json.loads(result) if result else None
        }
    
    # Convenience methods for specific queues
    
    async def enqueue_cv_parse(self, cv_id: str, user_id: str) -> str:
        """Enqueue a CV parsing job"""
        return await self.enqueue(self.CV_PARSE_QUEUE, {
            "id": cv_id,
            "cv_id": cv_id,
            "user_id": user_id,
            "type": "cv_parse"
        })
    
    async def enqueue_ai_tailor(self, cv_id: str, job_id: str, user_id: str) -> str:
        """Enqueue an AI tailoring job"""
        job_key = f"{cv_id}:{job_id}"
        return await self.enqueue(self.AI_TAILOR_QUEUE, {
            "id": job_key,
            "cv_id": cv_id,
            "job_id": job_id,
            "user_id": user_id,
            "type": "ai_tailor"
        })

# Create singleton instance
queue_service = QueueService()