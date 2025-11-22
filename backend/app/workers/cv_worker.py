import asyncio
import json
from datetime import datetime
from typing import Dict, Any
from app.services.queue import queue_service
from app.services.cv_parser import cv_parser_service
from app.services.storage import storage_service
from app.utils.supabase_client import supabase

class CVWorker:
    """Background worker for processing CV parsing jobs"""
    
    def __init__(self):
        self.running = False
        self.task = None
    
    async def process_cv_parse_job(self, job_data: Dict[str, Any]):
        """Process a single CV parsing job"""
        cv_id = job_data.get("cv_id")
        user_id = job_data.get("user_id")
        
        if not cv_id or not user_id:
            print(f"❌ Invalid job data: {job_data}")
            return
        
        try:
            print(f"📄 Processing CV parse job for CV: {cv_id}")
            
            # Update CV status to 'parsing'
            supabase.table("cvs").update({
                "status": "parsing"
            }).eq("id", cv_id).execute()
            
            # Get CV metadata to find file path
            cv_result = supabase.table("cvs").select("*").eq("id", cv_id).single().execute()
            
            if not cv_result.data:
                raise Exception(f"CV not found: {cv_id}")
            
            cv_data = cv_result.data
            file_path = cv_data["file_path"]
            filename = cv_data["original_filename"]
            
            # Download file from Supabase Storage
            file_content = await storage_service.download_cv(file_path)
            
            # Parse CV content
            parsed_data = await cv_parser_service.parse_cv_file(file_content, filename)
            
            # Save parsed sections to database
            supabase.table("cv_sections").upsert({
                "cv_id": cv_id,
                "summary": parsed_data.get("summary", ""),
                "skills": json.dumps(parsed_data.get("skills", [])),
                "experience": json.dumps(parsed_data.get("experience", [])),
                "education": json.dumps(parsed_data.get("education", [])),
                "certifications": json.dumps(parsed_data.get("certifications", []))
            }).execute()
            
            # Update CV status to 'parsed'
            supabase.table("cvs").update({
                "status": "parsed",
                "parsed_at": datetime.utcnow().isoformat()
            }).eq("id", cv_id).execute()
            
            print(f"✅ Successfully parsed CV: {cv_id}")
            
        except Exception as e:
            print(f"❌ Error parsing CV {cv_id}: {str(e)}")
            
            # Update CV status to 'error'
            supabase.table("cvs").update({
                "status": "error",
                "error_message": str(e)
            }).eq("id", cv_id).execute()
    
    async def run(self):
        """Main worker loop - processes jobs from the queue"""
        self.running = True
        print("🚀 CV Worker started")
        
        while self.running:
            try:
                # Try to get a job from the queue
                job = await queue_service.dequeue(queue_service.CV_PARSE_QUEUE)
                
                if job:
                    await self.process_cv_parse_job(job)
                else:
                    # No jobs available, wait a bit
                    await asyncio.sleep(5)
                    
            except Exception as e:
                print(f"❌ Worker error: {str(e)}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the worker in the background"""
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self.run())
            print("✓ CV Worker task created")
    
    async def stop(self):
        """Stop the worker gracefully"""
        self.running = False
        if self.task and not self.task.done():
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print("🛑 CV Worker stopped")

# Global worker instance
cv_worker = CVWorker()