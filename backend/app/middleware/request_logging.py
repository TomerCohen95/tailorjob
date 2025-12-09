"""
Middleware to log all HTTP requests.
"""
import logging
import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("uvicorn.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all incoming HTTP requests.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Log the request and response.
        """
        start_time = time.time()
        
        # Log the incoming request
        logger.info(
            f"{request.method} {request.url.path} - Client: {request.client.host if request.client else 'unknown'}"
        )
        
        # Process the request
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Log the response
            logger.info(
                f"{request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.3f}s"
            )
            
            # Log errors separately
            if response.status_code >= 400:
                logger.warning(
                    f"HTTP {response.status_code} error: {request.method} {request.url.path}"
                )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"{request.method} {request.url.path} - Error: {str(e)} - Duration: {duration:.3f}s",
                exc_info=True
            )
            raise