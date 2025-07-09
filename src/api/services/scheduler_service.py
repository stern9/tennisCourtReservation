# ABOUTME: Background job scheduler for midnight booking attempts and periodic tasks
# ABOUTME: Handles scheduled booking execution, retry logic, and background maintenance

import asyncio
import logging
from datetime import datetime, timedelta, time
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import threading
import uuid
from dataclasses import dataclass
import json

from ..config import get_settings
from ...dao import BookingRequestDAO, EncryptedUserConfigDAO
from ...models import BookingRequest as BookingRequestModel

logger = logging.getLogger(__name__)

class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class JobType(str, Enum):
    """Job type enumeration"""
    MIDNIGHT_BOOKING = "midnight_booking"
    RETRY_BOOKING = "retry_booking"
    CLEANUP_SESSIONS = "cleanup_sessions"
    CLEANUP_EXPIRED_BOOKINGS = "cleanup_expired_bookings"

@dataclass
class ScheduledJob:
    """Scheduled job definition"""
    job_id: str
    job_type: JobType
    scheduled_time: datetime
    payload: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class BackgroundScheduler:
    """Background job scheduler for tennis booking system"""
    
    def __init__(self):
        self.settings = get_settings()
        self.booking_dao = BookingRequestDAO()
        self.user_dao = EncryptedUserConfigDAO()
        self.jobs: Dict[str, ScheduledJob] = {}
        self.running = False
        self.scheduler_thread = None
        self._job_handlers = {
            JobType.MIDNIGHT_BOOKING: self._handle_midnight_booking,
            JobType.RETRY_BOOKING: self._handle_retry_booking,
            JobType.CLEANUP_SESSIONS: self._handle_cleanup_sessions,
            JobType.CLEANUP_EXPIRED_BOOKINGS: self._handle_cleanup_expired_bookings
        }
        
    def start(self):
        """Start the background scheduler"""
        if self.running:
            logger.warning("Scheduler is already running")
            return
            
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("Background scheduler started")
        
    def stop(self):
        """Stop the background scheduler"""
        if not self.running:
            return
            
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Background scheduler stopped")
        
    def schedule_job(self, job_type: JobType, scheduled_time: datetime, payload: Dict[str, Any]) -> str:
        """Schedule a new job"""
        job_id = str(uuid.uuid4())
        job = ScheduledJob(
            job_id=job_id,
            job_type=job_type,
            scheduled_time=scheduled_time,
            payload=payload
        )
        
        self.jobs[job_id] = job
        logger.info(f"Scheduled job {job_type.value} with ID {job_id} for {scheduled_time}")
        return job_id
        
    def schedule_midnight_booking(self, booking_request_id: str, user_id: str, target_date: datetime) -> str:
        """Schedule a midnight booking attempt"""
        # Calculate midnight time for the target date
        midnight_time = datetime.combine(target_date.date(), time.min)
        
        payload = {
            "booking_request_id": booking_request_id,
            "user_id": user_id,
            "target_date": target_date.isoformat()
        }
        
        return self.schedule_job(JobType.MIDNIGHT_BOOKING, midnight_time, payload)
        
    def schedule_retry_booking(self, booking_request_id: str, retry_delay_minutes: int = 30) -> str:
        """Schedule a booking retry"""
        retry_time = datetime.now() + timedelta(minutes=retry_delay_minutes)
        
        payload = {
            "booking_request_id": booking_request_id,
            "retry_delay_minutes": retry_delay_minutes
        }
        
        return self.schedule_job(JobType.RETRY_BOOKING, retry_time, payload)
        
    def schedule_cleanup_tasks(self):
        """Schedule periodic cleanup tasks"""
        # Schedule session cleanup every hour
        session_cleanup_time = datetime.now() + timedelta(hours=1)
        self.schedule_job(JobType.CLEANUP_SESSIONS, session_cleanup_time, {})
        
        # Schedule expired booking cleanup every 6 hours
        booking_cleanup_time = datetime.now() + timedelta(hours=6)
        self.schedule_job(JobType.CLEANUP_EXPIRED_BOOKINGS, booking_cleanup_time, {})
        
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                logger.info(f"Cancelled job {job_id}")
                return True
            else:
                logger.warning(f"Cannot cancel job {job_id} - status: {job.status}")
                return False
        return False
        
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status"""
        if job_id in self.jobs:
            job = self.jobs[job_id]
            return {
                "job_id": job.job_id,
                "job_type": job.job_type,
                "status": job.status,
                "scheduled_time": job.scheduled_time.isoformat(),
                "created_at": job.created_at.isoformat(),
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "error_message": job.error_message,
                "retry_count": job.retry_count,
                "max_retries": job.max_retries
            }
        return None
        
    def get_pending_jobs(self) -> List[Dict[str, Any]]:
        """Get all pending jobs"""
        pending_jobs = []
        for job in self.jobs.values():
            if job.status == JobStatus.PENDING:
                pending_jobs.append({
                    "job_id": job.job_id,
                    "job_type": job.job_type,
                    "scheduled_time": job.scheduled_time.isoformat(),
                    "payload": job.payload
                })
        return pending_jobs
        
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Find jobs that are ready to execute
                ready_jobs = []
                for job in self.jobs.values():
                    if job.status == JobStatus.PENDING and job.scheduled_time <= current_time:
                        ready_jobs.append(job)
                
                # Execute ready jobs
                for job in ready_jobs:
                    self._execute_job(job)
                
                # Clean up old completed jobs (older than 24 hours)
                self._cleanup_old_jobs()
                
                # Sleep for 30 seconds before next check
                threading.Event().wait(30)
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                threading.Event().wait(60)  # Wait longer on error
                
    def _execute_job(self, job: ScheduledJob):
        """Execute a scheduled job"""
        try:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now()
            
            logger.info(f"Executing job {job.job_id} of type {job.job_type}")
            
            # Get the appropriate handler
            handler = self._job_handlers.get(job.job_type)
            if not handler:
                raise ValueError(f"No handler for job type: {job.job_type}")
                
            # Execute the job
            success = handler(job.payload)
            
            if success:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.now()
                logger.info(f"Job {job.job_id} completed successfully")
            else:
                # Handle job failure
                self._handle_job_failure(job)
                
        except Exception as e:
            logger.error(f"Error executing job {job.job_id}: {e}")
            job.error_message = str(e)
            self._handle_job_failure(job)
            
    def _handle_job_failure(self, job: ScheduledJob):
        """Handle job failure with retry logic"""
        job.retry_count += 1
        
        if job.retry_count < job.max_retries:
            # Schedule retry
            retry_delay = min(300 * (2 ** job.retry_count), 3600)  # Exponential backoff, max 1 hour
            job.scheduled_time = datetime.now() + timedelta(seconds=retry_delay)
            job.status = JobStatus.PENDING
            logger.info(f"Job {job.job_id} scheduled for retry {job.retry_count}/{job.max_retries} in {retry_delay} seconds")
        else:
            # Max retries reached
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now()
            logger.error(f"Job {job.job_id} failed after {job.max_retries} retries")
            
    def _handle_midnight_booking(self, payload: Dict[str, Any]) -> bool:
        """Handle midnight booking attempt"""
        try:
            booking_request_id = payload["booking_request_id"]
            user_id = payload["user_id"]
            
            # Get booking request
            booking_request = self.booking_dao.get_booking_request(booking_request_id)
            if not booking_request:
                logger.error(f"Booking request {booking_request_id} not found")
                return False
                
            # Get user information
            user = self.user_dao.get_user(user_id)
            if not user:
                logger.error(f"User {user_id} not found")
                return False
                
            # Import here to avoid circular imports
            from .tennis_booking_service import TennisBookingService
            tennis_service = TennisBookingService()
            
            # Attempt the booking
            success = tennis_service.execute_booking(booking_request, user)
            
            if success:
                # Update booking status
                booking_request.status = "confirmed"
                booking_request.updated_at = datetime.now().isoformat()
                self.booking_dao.update_booking_status(booking_request_id, "confirmed")
                logger.info(f"Midnight booking successful for request {booking_request_id}")
                return True
            else:
                # Update booking status to failed
                booking_request.status = "failed"
                booking_request.updated_at = datetime.now().isoformat()
                self.booking_dao.update_booking_status(booking_request_id, "failed")
                logger.warning(f"Midnight booking failed for request {booking_request_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error in midnight booking: {e}")
            return False
            
    def _handle_retry_booking(self, payload: Dict[str, Any]) -> bool:
        """Handle booking retry attempt"""
        try:
            booking_request_id = payload["booking_request_id"]
            
            # Get booking request
            booking_request = self.booking_dao.get_booking_request(booking_request_id)
            if not booking_request:
                logger.error(f"Booking request {booking_request_id} not found for retry")
                return False
                
            # Check if booking is still in failed state
            if booking_request.status != "failed":
                logger.info(f"Booking request {booking_request_id} status changed, skipping retry")
                return True
                
            # Get user information
            user = self.user_dao.get_user(booking_request.user_id)
            if not user:
                logger.error(f"User {booking_request.user_id} not found for retry")
                return False
                
            # Import here to avoid circular imports
            from .tennis_booking_service import TennisBookingService
            tennis_service = TennisBookingService()
            
            # Attempt the booking again
            success = tennis_service.execute_booking(booking_request, user)
            
            if success:
                # Update booking status
                booking_request.status = "confirmed"
                booking_request.updated_at = datetime.now().isoformat()
                self.booking_dao.update_booking_status(booking_request_id, "confirmed")
                logger.info(f"Retry booking successful for request {booking_request_id}")
                return True
            else:
                # Increment retry count
                booking_request.retry_count += 1
                self.booking_dao.update_booking_request(booking_request)
                logger.warning(f"Retry booking failed for request {booking_request_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error in retry booking: {e}")
            return False
            
    def _handle_cleanup_sessions(self, payload: Dict[str, Any]) -> bool:
        """Handle session cleanup"""
        try:
            from .user_service import user_service
            cleaned_count = user_service.cleanup_expired_sessions()
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
            
            # Schedule next cleanup
            self.schedule_cleanup_tasks()
            return True
            
        except Exception as e:
            logger.error(f"Error in session cleanup: {e}")
            return False
            
    def _handle_cleanup_expired_bookings(self, payload: Dict[str, Any]) -> bool:
        """Handle expired booking cleanup"""
        try:
            # Import here to avoid circular imports
            from .booking_service import booking_service
            
            # Clean up old completed bookings (older than 30 days)
            cleanup_count = booking_service.cleanup_old_bookings(days_old=30)
            logger.info(f"Cleaned up {cleanup_count} old bookings")
            
            # Expire old pending/scheduled requests (older than 24 hours)
            expired_count = booking_service.expire_old_requests(hours_old=24)
            logger.info(f"Expired {expired_count} old requests")
            
            # Schedule next cleanup
            self.schedule_cleanup_tasks()
            return True
            
        except Exception as e:
            logger.error(f"Error in expired booking cleanup: {e}")
            return False
            
    def _cleanup_old_jobs(self):
        """Clean up old completed jobs"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        jobs_to_remove = []
        
        for job_id, job in self.jobs.items():
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                if job.completed_at and job.completed_at < cutoff_time:
                    jobs_to_remove.append(job_id)
                    
        for job_id in jobs_to_remove:
            del self.jobs[job_id]
            
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")

# Global scheduler instance
background_scheduler = BackgroundScheduler()