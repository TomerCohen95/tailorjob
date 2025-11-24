import redis.asyncio as redis
import json
import uuid
import asyncio
from typing import Dict, Any, Optional
from app.config import settings

class QueueService:
    """Service for managing background job queues using Redis"""
    
    def __init__(self):
        # Redis is optional - if not configured, queue operations will be no-ops
        self.redis = None
        self.max_retries = 3
        self.retry_delay = 1  # seconds
        
        if settings.UPSTASH_REDIS_URL:
            try:
                self.redis = redis.from_url(
                    settings.UPSTASH_REDIS_URL,
                    decode_responses=True,
                    ssl_cert_reqs=None,  # Disable SSL verification for development
                    socket_keepalive=True,
                    socket_keepalive_options={},
                    health_check_interval=30
                )
                print("✅ Redis connection initialized")
            except Exception as e:
                print(f"⚠️  Warning: Could not connect to Redis: {e}")
        
        # Queue names
        self.CV_PARSE_QUEUE = "queue:cv-parse"
        self.AI_TAILOR_QUEUE = "queue:ai-tailor"
    
    async def _retry_operation(self, operation, *args, **kwargs):
        """Retry a Redis operation with exponential backoff"""
        last_error = None
        for attempt in range(self.max_retries):
            try:
                return await operation(*args, **kwargs)
            except (redis.ConnectionError, redis.TimeoutError, ConnectionResetError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"🔄 Redis operation failed (attempt {attempt + 1}/{self.max_retries}), retrying in {delay}s: {str(e)}")
                    await asyncio.sleep(delay)
                else:
                    print(f"❌ Redis operation failed after {self.max_retries} attempts: {str(e)}")
        raise last_error
    
    async def enqueue(self, queue_name: str, data: Dict[str, Any]) -> str:
        """Add a job to the queue with retry logic"""
        job_id = data.get("id", str(uuid.uuid4()))
        
        if self.redis:
            try:
                # Add job to queue (Redis list) with retry
                await self._retry_operation(self.redis.lpush, queue_name, json.dumps(data))
                
                # Set initial job status with 1 hour TTL with retry
                await self._retry_operation(self.redis.setex, f"job:{job_id}:status", 3600, "queued")
                
                print(f"✅ Job {job_id} successfully enqueued to {queue_name}")
            except Exception as e:
                print(f"❌ Failed to enqueue job {job_id}: {str(e)}")
                raise
        else:
            # Redis not configured - log warning
            print(f"⚠️  Warning: Redis not configured. Job {job_id} not queued.")
        
        return job_id
    
    async def dequeue(self, queue_name: str, timeout: int = 5) -> Optional[Dict[str, Any]]:
        """Get a job from the queue (blocking operation) with retry logic"""
        if not self.redis:
            return None
        
        try:
            result = await self._retry_operation(self.redis.brpop, queue_name, timeout=timeout)
            
            if result:
                _, job_data = result
                return json.loads(job_data)
        except Exception as e:
            print(f"❌ Failed to dequeue from {queue_name}: {str(e)}")
            # Return None to allow worker to continue
            return None
        
        return None
    
    async def set_job_status(self, job_id: str, status: str, result: Any = None):
        """Update job status and optionally store result with retry logic"""
        if not self.redis:
            return
        
        try:
            await self._retry_operation(self.redis.setex, f"job:{job_id}:status", 3600, status)
            
            if result:
                await self._retry_operation(
                    self.redis.setex,
                    f"job:{job_id}:result",
                    3600,
                    json.dumps(result)
                )
        except Exception as e:
            print(f"⚠️  Failed to set job status for {job_id}: {str(e)}")
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the current status of a job with retry logic"""
        if not self.redis:
            return {
                "status": "unavailable",
                "result": None
            }
        
        try:
            status = await self._retry_operation(self.redis.get, f"job:{job_id}:status")
            result = await self._retry_operation(self.redis.get, f"job:{job_id}:result")
            
            return {
                "status": status or "not_found",
                "result": json.loads(result) if result else None
            }
        except Exception as e:
            print(f"⚠️  Failed to get job status for {job_id}: {str(e)}")
            return {
                "status": "error",
                "result": None
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