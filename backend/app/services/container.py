import redis

from app.services.cv_extractor import CVExtractor
from app.services.cv_tailor import CVTailor
from app.config import settings

class Container:
    """
    A container for managing application-wide service instances (dependencies).
    This centralizes the creation and access of services.
    """
    def __init__(self):
        # Services are instantiated here. In a real app, this is where you
        # would pass configuration (e.g., from environment variables).
        self._cv_extractor = CVExtractor()
        self._cv_tailor = CVTailor()
        self._redis_client = redis.from_url(settings.UPSTASH_REDIS_URL)

    def cv_extractor(self) -> CVExtractor:
        return self._cv_extractor

    def cv_tailor(self) -> CVTailor:
        return self._cv_tailor
    
    def redis_client(self) -> redis.Redis:
        """Provides the Redis client instance."""
        return self._redis_client

# A single, global instance of the container that the app will use.
container = Container()