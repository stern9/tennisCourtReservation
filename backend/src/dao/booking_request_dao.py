# ABOUTME: BookingRequest Data Access Object with booking-specific operations
# ABOUTME: Provides validated CRUD operations and booking queries for BookingRequest

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging

from .base import BaseDAO, NotFoundError
from ..models.booking_request import BookingRequest, BookingStatus, BookingPriority

logger = logging.getLogger(__name__)


class BookingRequestDAO(BaseDAO[BookingRequest]):
    """Data Access Object for BookingRequest operations"""
    
    def __init__(self):
        super().__init__(BookingRequest)
    
    def _get_table_name(self) -> str:
        """Get table name for BookingRequest"""
        return "BookingRequests"
    
    def create_booking_request(self, booking_request: BookingRequest) -> BookingRequest:
        """Create a new booking request"""
        # Set initial timestamps
        if not booking_request.requested_at:
            booking_request.requested_at = datetime.utcnow().isoformat()
        
        # Set expiration if not set
        if not booking_request.expires_at:
            booking_request.set_expiration(days=1)
        
        return self.create(booking_request)
    
    def get_booking_request(self, request_id: str) -> Optional[BookingRequest]:
        """Get booking request by request ID"""
        return self.get(request_id=request_id)
    
    def update_booking_request(self, booking_request: BookingRequest) -> BookingRequest:
        """Update booking request"""
        existing_request = self.get_booking_request(booking_request.request_id)
        if not existing_request:
            raise NotFoundError(f"Booking request {booking_request.request_id} not found")
        
        return self.update(booking_request)
    
    def delete_booking_request(self, request_id: str) -> bool:
        """Delete booking request"""
        return self.delete(request_id=request_id)
    
    def get_user_booking_requests(
        self, 
        user_id: str, 
        status: Optional[BookingStatus] = None,
        limit: Optional[int] = None
    ) -> List[BookingRequest]:
        """Get booking requests for a user"""
        try:
            # Build filter expression
            filter_expression = 'user_id = :user_id'
            expression_attribute_values = {':user_id': user_id}
            
            if status:
                filter_expression += ' AND #status = :status'
                expression_attribute_values[':status'] = status.value
            
            scan_kwargs = {
                'FilterExpression': filter_expression,
                'ExpressionAttributeValues': expression_attribute_values
            }
            
            if status:
                scan_kwargs['ExpressionAttributeNames'] = {'#status': 'status'}
            
            if limit:
                scan_kwargs['Limit'] = limit
            
            response = self.table.scan(**scan_kwargs)
            
            requests = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                requests.append(booking_request)
            
            # Sort by creation date (newest first)
            requests.sort(key=lambda x: x.created_at, reverse=True)
            
            logger.debug(f"Retrieved {len(requests)} booking requests for user {user_id}")
            return requests
            
        except Exception as e:
            logger.error(f"Error getting user booking requests: {e}")
            raise
    
    def get_requests_by_status(
        self, 
        status: BookingStatus, 
        limit: Optional[int] = None
    ) -> List[BookingRequest]:
        """Get booking requests by status"""
        try:
            scan_kwargs = {
                'FilterExpression': '#status = :status',
                'ExpressionAttributeNames': {'#status': 'status'},
                'ExpressionAttributeValues': {':status': status.value}
            }
            
            if limit:
                scan_kwargs['Limit'] = limit
            
            response = self.table.scan(**scan_kwargs)
            
            requests = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                requests.append(booking_request)
            
            logger.debug(f"Retrieved {len(requests)} booking requests with status {status}")
            return requests
            
        except Exception as e:
            logger.error(f"Error getting requests by status: {e}")
            raise
    
    def get_requests_by_date(
        self, 
        booking_date: str, 
        status: Optional[BookingStatus] = None
    ) -> List[BookingRequest]:
        """Get booking requests for a specific date"""
        try:
            filter_expression = 'booking_date = :booking_date'
            expression_attribute_values = {':booking_date': booking_date}
            expression_attribute_names = {}
            
            if status:
                filter_expression += ' AND #status = :status'
                expression_attribute_values[':status'] = status.value
                expression_attribute_names['#status'] = 'status'
            
            scan_kwargs = {
                'FilterExpression': filter_expression,
                'ExpressionAttributeValues': expression_attribute_values
            }
            
            if expression_attribute_names:
                scan_kwargs['ExpressionAttributeNames'] = expression_attribute_names
            
            response = self.table.scan(**scan_kwargs)
            
            requests = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                requests.append(booking_request)
            
            logger.debug(f"Retrieved {len(requests)} booking requests for date {booking_date}")
            return requests
            
        except Exception as e:
            logger.error(f"Error getting requests by date: {e}")
            raise
    
    def get_requests_by_court(
        self, 
        court_id: int, 
        booking_date: Optional[str] = None
    ) -> List[BookingRequest]:
        """Get booking requests for a specific court"""
        try:
            filter_expression = 'court_id = :court_id'
            expression_attribute_values = {':court_id': court_id}
            
            if booking_date:
                filter_expression += ' AND booking_date = :booking_date'
                expression_attribute_values[':booking_date'] = booking_date
            
            response = self.table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            requests = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                requests.append(booking_request)
            
            logger.debug(f"Retrieved {len(requests)} booking requests for court {court_id}")
            return requests
            
        except Exception as e:
            logger.error(f"Error getting requests by court: {e}")
            raise
    
    def get_pending_requests(self) -> List[BookingRequest]:
        """Get all pending booking requests"""
        return self.get_requests_by_status(BookingStatus.PENDING)
    
    def get_failed_requests_for_retry(self) -> List[BookingRequest]:
        """Get failed requests that can be retried"""
        try:
            response = self.table.scan(
                FilterExpression='#status = :status AND auto_retry = :auto_retry AND retry_count < max_retries',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': BookingStatus.FAILED.value,
                    ':auto_retry': True
                }
            )
            
            requests = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                if booking_request.can_retry():
                    requests.append(booking_request)
            
            logger.debug(f"Retrieved {len(requests)} failed requests for retry")
            return requests
            
        except Exception as e:
            logger.error(f"Error getting failed requests for retry: {e}")
            raise
    
    def get_expired_requests(self) -> List[BookingRequest]:
        """Get requests that have expired"""
        try:
            current_time = datetime.utcnow().isoformat()
            
            response = self.table.scan(
                FilterExpression='expires_at < :current_time AND #status IN (:pending, :failed)',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':current_time': current_time,
                    ':pending': BookingStatus.PENDING.value,
                    ':failed': BookingStatus.FAILED.value
                }
            )
            
            requests = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                requests.append(booking_request)
            
            logger.debug(f"Retrieved {len(requests)} expired requests")
            return requests
            
        except Exception as e:
            logger.error(f"Error getting expired requests: {e}")
            raise
    
    def mark_request_as_confirmed(
        self, 
        request_id: str, 
        confirmation_code: str = None,
        external_booking_id: str = None
    ) -> BookingRequest:
        """Mark a request as confirmed"""
        request = self.get_booking_request(request_id)
        if not request:
            raise NotFoundError(f"Booking request {request_id} not found")
        
        request.mark_as_confirmed(confirmation_code)
        if external_booking_id:
            request.external_booking_id = external_booking_id
        
        return self.update_booking_request(request)
    
    def mark_request_as_failed(
        self, 
        request_id: str, 
        error_message: str = None
    ) -> BookingRequest:
        """Mark a request as failed"""
        request = self.get_booking_request(request_id)
        if not request:
            raise NotFoundError(f"Booking request {request_id} not found")
        
        request.mark_as_failed(error_message)
        return self.update_booking_request(request)
    
    def mark_request_as_cancelled(self, request_id: str) -> BookingRequest:
        """Mark a request as cancelled"""
        request = self.get_booking_request(request_id)
        if not request:
            raise NotFoundError(f"Booking request {request_id} not found")
        
        request.mark_as_cancelled()
        return self.update_booking_request(request)
    
    def increment_retry_count(self, request_id: str) -> BookingRequest:
        """Increment retry count for a request"""
        request = self.get_booking_request(request_id)
        if not request:
            raise NotFoundError(f"Booking request {request_id} not found")
        
        request.increment_retry_count()
        return self.update_booking_request(request)
    
    def expire_old_requests(self) -> int:
        """Mark expired requests as expired"""
        expired_requests = self.get_expired_requests()
        count = 0
        
        for request in expired_requests:
            try:
                request.mark_as_expired()
                self.update_booking_request(request)
                count += 1
            except Exception as e:
                logger.error(f"Error expiring request {request.request_id}: {e}")
        
        logger.info(f"Expired {count} old requests")
        return count
    
    def get_booking_conflicts(
        self, 
        court_id: int, 
        booking_date: str, 
        time_slot: str
    ) -> List[BookingRequest]:
        """Get confirmed bookings that conflict with the given parameters"""
        try:
            response = self.table.scan(
                FilterExpression='court_id = :court_id AND booking_date = :booking_date AND time_slot = :time_slot AND #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':court_id': court_id,
                    ':booking_date': booking_date,
                    ':time_slot': time_slot,
                    ':status': BookingStatus.CONFIRMED.value
                }
            )
            
            requests = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                requests.append(booking_request)
            
            return requests
            
        except Exception as e:
            logger.error(f"Error checking booking conflicts: {e}")
            raise
    
    def get_user_bookings_for_date(
        self, 
        user_id: str, 
        booking_date: str
    ) -> List[BookingRequest]:
        """Get user's bookings for a specific date"""
        try:
            response = self.table.scan(
                FilterExpression='user_id = :user_id AND booking_date = :booking_date AND #status IN (:confirmed, :pending)',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':user_id': user_id,
                    ':booking_date': booking_date,
                    ':confirmed': BookingStatus.CONFIRMED.value,
                    ':pending': BookingStatus.PENDING.value
                }
            )
            
            requests = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                requests.append(booking_request)
            
            return requests
            
        except Exception as e:
            logger.error(f"Error getting user bookings for date: {e}")
            raise
    
    def get_booking_stats(self) -> Dict[str, Any]:
        """Get booking request statistics"""
        try:
            total_count = self.count()
            
            # Get counts by status
            status_counts = {}
            for status in BookingStatus:
                response = self.table.scan(
                    FilterExpression='#status = :status',
                    ExpressionAttributeNames={'#status': 'status'},
                    ExpressionAttributeValues={':status': status.value},
                    Select='COUNT'
                )
                status_counts[status.value] = response.get('Count', 0)
            
            # Get requests from last 7 days
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            recent_response = self.table.scan(
                FilterExpression='created_at >= :week_ago',
                ExpressionAttributeValues={':week_ago': week_ago},
                Select='COUNT'
            )
            recent_count = recent_response.get('Count', 0)
            
            stats = {
                'total_requests': total_count,
                'status_counts': status_counts,
                'recent_requests_7_days': recent_count
            }
            
            logger.debug(f"Booking stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting booking stats: {e}")
            raise
    
    def get_old_bookings(self, cutoff_date_str: str) -> List[BookingRequest]:
        """Get all bookings older than cutoff date"""
        try:
            response = self.table.scan(
                FilterExpression='created_at < :cutoff_date',
                ExpressionAttributeValues={':cutoff_date': cutoff_date_str}
            )
            
            bookings = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                bookings.append(booking_request)
            
            logger.debug(f"Retrieved {len(bookings)} old bookings")
            return bookings
            
        except Exception as e:
            logger.error(f"Error getting old bookings: {e}")
            raise
    
    def get_old_requests_by_status(self, statuses: List[BookingStatus], cutoff_time_str: str) -> List[BookingRequest]:
        """Get old requests by status list"""
        try:
            # Build filter expression for multiple statuses
            status_placeholders = []
            expression_values = {':cutoff_time': cutoff_time_str}
            
            for i, status in enumerate(statuses):
                placeholder = f':status{i}'
                status_placeholders.append(placeholder)
                expression_values[placeholder] = status.value
            
            status_filter = ' OR '.join([f'#status = {placeholder}' for placeholder in status_placeholders])
            filter_expression = f'created_at < :cutoff_time AND ({status_filter})'
            
            response = self.table.scan(
                FilterExpression=filter_expression,
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues=expression_values
            )
            
            requests = []
            for item in response.get('Items', []):
                booking_request = self.model_class.from_dynamodb_item(item)
                requests.append(booking_request)
            
            logger.debug(f"Retrieved {len(requests)} old requests with statuses {[s.value for s in statuses]}")
            return requests
            
        except Exception as e:
            logger.error(f"Error getting old requests by status: {e}")
            raise