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
            # Check if sections already exist
            existing_sections = supabase.table("cv_sections")\
                .select("id")\
                .eq("cv_id", cv_id)\
                .execute()
            
            sections_data = {
                "cv_id": cv_id,
                "summary": parsed_data.get("summary", ""),
                "skills": json.dumps(parsed_data.get("skills", [])),
                "experience": json.dumps(parsed_data.get("experience", [])),
                "education": json.dumps(parsed_data.get("education", [])),
                "certifications": json.dumps(parsed_data.get("certifications", []))
            }
            
            if existing_sections.data:
                # Update existing sections
                supabase.table("cv_sections")\
                    .update(sections_data)\
                    .eq("cv_id", cv_id)\
                    .execute()
                print(f"📝 Updated existing CV sections")
            else:
                # Insert new sections
                supabase.table("cv_sections").insert(sections_data).execute()
                print(f"📝 Created new CV sections")
            
            # Update CV status to 'parsed'
            supabase.table("cvs").update({
                "status": "parsed",
                "parsed_at": datetime.utcnow().isoformat()
            }).eq("id", cv_id).execute()
            
            # Create notification for successful parse
            try:
                supabase.table("cv_notifications").insert({
                    "user_id": user_id,
                    "cv_id": cv_id,
                    "type": "cv_parsed",
                    "message": f"Your CV '{filename}' has been successfully parsed and is ready to use!"
                }).execute()
                print(f"📬 Notification created for CV: {cv_id}")
            except Exception as notif_error:
                print(f"⚠️  Failed to create notification: {str(notif_error)}")
            
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
        print(f"📡 Listening on queue: {queue_service.CV_PARSE_QUEUE}")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.running:
            try:
                # Try to get a job from the queue
                print("🔍 Checking for jobs...")
                job = await queue_service.dequeue(queue_service.CV_PARSE_QUEUE)
                
                if job:
                    consecutive_errors = 0  # Reset error counter on successful dequeue
                    print(f"📬 Job received: {job}")
                    await self.process_cv_parse_job(job)
                else:
                    # No jobs available, wait a bit
                    print("💤 No jobs, sleeping for 5s...")
                    await asyncio.sleep(5)
                    
            except Exception as e:
                consecutive_errors += 1
                print(f"❌ Worker error ({consecutive_errors}/{max_consecutive_errors}): {str(e)}")
                
                if consecutive_errors >= max_consecutive_errors:
                    print(f"⚠️  Too many consecutive errors ({consecutive_errors}), increasing backoff to 30s")
                    await asyncio.sleep(30)
                    consecutive_errors = 0  # Reset after long sleep
                else:
                    import traceback
                    traceback.print_exc()
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