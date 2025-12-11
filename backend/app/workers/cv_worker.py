import asyncio
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any
from app.services.queue import queue_service
from app.services.cv_parser import cv_parser_service
from app.services.storage import storage_service
from app.utils.supabase_client import supabase

logger = logging.getLogger(__name__)

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
            logger.error(f"❌ Invalid job data received: {job_data}")
            return
        
        start_time = time.time()
        logger.info(f"⚙️  Worker processing CV parse job: cv_id={cv_id}, user={user_id}")
        
        try:
            
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
            
            # Count sections
            section_counts = {
                'skills': len(parsed_data.get("skills", [])),
                'experience': len(parsed_data.get("experience", [])),
                'education': len(parsed_data.get("education", [])),
                'certifications': len(parsed_data.get("certifications", []))
            }
            
            if existing_sections.data:
                # Update existing sections
                supabase.table("cv_sections")\
                    .update(sections_data)\
                    .eq("cv_id", cv_id)\
                    .execute()
                logger.info(f"📝 Updated CV sections: cv_id={cv_id}, sections={section_counts}")
            else:
                # Insert new sections
                supabase.table("cv_sections").insert(sections_data).execute()
                logger.info(f"📝 Created CV sections: cv_id={cv_id}, sections={section_counts}")
            
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
                logger.info(f"📬 Notification created: cv_id={cv_id}, user={user_id}")
            except Exception as notif_error:
                logger.warning(f"⚠️  Failed to create notification (non-fatal): cv_id={cv_id}, error={str(notif_error)}")
            
            duration = time.time() - start_time
            logger.info(f"✅ Worker completed CV parsing: cv_id={cv_id}, user={user_id}, duration={duration:.2f}s, sections={section_counts}")
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ Worker failed to parse CV: cv_id={cv_id}, user={user_id}, duration={duration:.2f}s, error={str(e)}", exc_info=True)
            
            # Update CV status to 'error'
            supabase.table("cvs").update({
                "status": "error",
                "error_message": str(e)
            }).eq("id", cv_id).execute()
    
    async def run(self):
        """Main worker loop - processes jobs from the queue"""
        self.running = True
        logger.info(f"🚀 CV Worker started, listening on queue: {queue_service.CV_PARSE_QUEUE}")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        jobs_processed = 0
        
        while self.running:
            try:
                # Try to get a job from the queue
                job = await queue_service.dequeue(queue_service.CV_PARSE_QUEUE)
                
                if job:
                    consecutive_errors = 0  # Reset error counter on successful dequeue
                    jobs_processed += 1
                    logger.info(f"📬 Worker received job #{jobs_processed}: cv_id={job.get('cv_id')}")
                    await self.process_cv_parse_job(job)
                else:
                    # No jobs available, wait a bit
                    await asyncio.sleep(5)
                    
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"❌ Worker loop error ({consecutive_errors}/{max_consecutive_errors}): {str(e)}", exc_info=True)
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.warning(f"⚠️  Too many consecutive errors, increasing backoff to 30s")
                    await asyncio.sleep(30)
                    consecutive_errors = 0  # Reset after long sleep
                else:
                    await asyncio.sleep(5)
    
    async def start(self):
        """Start the worker in the background"""
        if not self.task or self.task.done():
            self.task = asyncio.create_task(self.run())
            logger.info("✅ CV Worker task created and started")
    
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