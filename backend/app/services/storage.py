from app.utils.supabase_client import supabase
import uuid

class StorageService:
    """Service for managing file storage in Supabase Storage"""
    
    BUCKET = "cv-uploads"
    
    async def upload_cv(self, content: bytes, filename: str, user_id: str) -> str:
        """
        Upload CV file to Supabase Storage
        
        Args:
            content: File content as bytes
            filename: Original filename
            user_id: User ID (for folder organization)
            
        Returns:
            File path in storage
        """
        # Generate unique filename
        ext = filename.split('.')[-1]
        unique_name = f"{uuid.uuid4()}.{ext}"
        path = f"{user_id}/{unique_name}"
        
        # Upload to Supabase Storage
        supabase.storage.from_(self.BUCKET).upload(
            path,
            content,
            {"content-type": f"application/{ext}"}
        )
        
        return path
    
    async def download_cv(self, path: str) -> bytes:
        """Download CV file from storage"""
        response = supabase.storage.from_(self.BUCKET).download(path)
        return response
    
    async def delete_cv(self, path: str):
        """Delete CV file from storage"""
        supabase.storage.from_(self.BUCKET).remove([path])
    
    async def get_signed_url(self, path: str, expires_in: int = 3600) -> str:
        """Get a temporary signed URL for file access"""
        response = supabase.storage.from_(self.BUCKET).create_signed_url(
            path,
            expires_in
        )
        return response['signedURL']

# Create singleton instance
storage_service = StorageService()