# ABOUTME: Integration tests for booking service with comprehensive workflow testing
# ABOUTME: Tests booking creation, validation, status transitions, and cleanup operations

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, patch, MagicMock
import uuid

from src.api.services.booking_service import BookingService
from src.api.models import BookingRequest, BookingResponse, BookingStatus, BookingValidation
from src.models.booking_request import BookingRequest as BookingRequestModel
from src.factories.test_factories import BookingRequestFactory


class TestBookingServiceIntegration:
    """Integration tests for booking service"""
    
    @pytest.fixture
    def mock_booking_dao(self):
        """Mock booking DAO"""
        with patch('src.api.services.booking_service.BookingRequestDAO') as mock_dao:
            dao_instance = Mock()
            mock_dao.return_value = dao_instance
            yield dao_instance
    
    @pytest.fixture
    def mock_system_config_dao(self):
        """Mock system config DAO"""
        with patch('src.api.services.booking_service.SystemConfigDAO') as mock_dao:
            dao_instance = Mock()
            mock_dao.return_value = dao_instance
            yield dao_instance
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with court configurations"""
        with patch('src.api.services.booking_service.get_settings') as mock_get_settings:
            settings = Mock()
            settings.court_availability_windows = {
                "1": 10,  # Court 1: 10-day window
                "2": 9    # Court 2: 9-day window (different availability windows)
            }
            mock_get_settings.return_value = settings
            yield settings
    
    @pytest.fixture
    def booking_service(self, mock_booking_dao, mock_system_config_dao, mock_settings):
        """Create booking service with mocked dependencies"""
        service = BookingService()
        service.booking_dao = mock_booking_dao
        service.system_config_dao = mock_system_config_dao
        return service
    
    def test_create_booking_request_success(self, booking_service, mock_booking_dao):
        """Test successful booking request creation"""
        # Arrange
        user_id = str(uuid.uuid4())
        booking_request = BookingRequest(
            court_id=1,
            booking_date=date.today() + timedelta(days=5),
            time_slot="De 10:00 AM a 11:00 AM"
        )
        
        # Mock no conflicts
        mock_booking_dao.get_booking_conflicts.return_value = []
        mock_booking_dao.get_user_bookings_for_date.return_value = []
        
        # Mock successful creation
        created_booking = BookingRequestModel(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            court_id=booking_request.court_id,
            booking_date=booking_request.booking_date.isoformat(),
            time_slot=booking_request.time_slot,
            status=BookingStatus.PENDING.value,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        mock_booking_dao.create_booking_request.return_value = created_booking
        
        # Act
        result = booking_service.create_booking_request(booking_request, user_id)
        
        # Assert
        assert isinstance(result, BookingResponse)
        assert result.status == BookingStatus.PENDING
        assert result.court_id == booking_request.court_id
        assert result.booking_date == booking_request.booking_date
        assert result.time_slot == booking_request.time_slot
        assert result.user_id == user_id
        
        # Verify DAO calls
        mock_booking_dao.get_booking_conflicts.assert_called_once()
        mock_booking_dao.get_user_bookings_for_date.assert_called_once()
        mock_booking_dao.create_booking_request.assert_called_once()
    
    def test_create_booking_request_with_conflicts(self, booking_service, mock_booking_dao):
        """Test booking request creation with conflicts"""
        # Arrange
        user_id = str(uuid.uuid4())
        booking_request = BookingRequest(
            court_id=1,
            booking_date=date.today() + timedelta(days=5),
            time_slot="De 10:00 AM a 11:00 AM"
        )
        
        # Mock existing conflict
        conflicting_booking = BookingRequestFactory.create_booking_request(
            court_id=1,
            booking_date=booking_request.booking_date.isoformat(),
            time_slot=booking_request.time_slot,
            status=BookingStatus.CONFIRMED.value
        )
        mock_booking_dao.get_booking_conflicts.return_value = [conflicting_booking]
        mock_booking_dao.get_user_bookings_for_date.return_value = []
        
        # Act
        result = booking_service.create_booking_request(booking_request, user_id)
        
        # Assert
        assert isinstance(result, BookingResponse)
        assert result.status == BookingStatus.FAILED
        assert "already booked" in result.message.lower()
        
        # Verify no booking was created
        mock_booking_dao.create_booking_request.assert_not_called()
    
    def test_create_booking_request_user_limit_exceeded(self, booking_service, mock_booking_dao):
        """Test booking request creation when user exceeds daily limit"""
        # Arrange
        user_id = str(uuid.uuid4())
        booking_request = BookingRequest(
            court_id=1,
            booking_date=date.today() + timedelta(days=5),
            time_slot="De 10:00 AM a 11:00 AM"
        )
        
        # Mock no conflicts but user has max bookings
        mock_booking_dao.get_booking_conflicts.return_value = []
        existing_bookings = [
            BookingRequestFactory.create_booking_request(user_id=user_id, status=BookingStatus.CONFIRMED.value),
            BookingRequestFactory.create_booking_request(user_id=user_id, status=BookingStatus.PENDING.value)
        ]
        mock_booking_dao.get_user_bookings_for_date.return_value = existing_bookings
        
        # Act
        result = booking_service.create_booking_request(booking_request, user_id)
        
        # Assert
        assert isinstance(result, BookingResponse)
        assert result.status == BookingStatus.FAILED
        assert "maximum" in result.message.lower()
        
        # Verify no booking was created
        mock_booking_dao.create_booking_request.assert_not_called()
    
    def test_create_scheduled_booking_request(self, booking_service, mock_booking_dao):
        """Test creation of scheduled booking request"""
        # Arrange
        user_id = str(uuid.uuid4())
        # Request booking for 10 days in the future (exact window limit for court 1)
        booking_request = BookingRequest(
            court_id=1,
            booking_date=date.today() + timedelta(days=10),
            time_slot="De 10:00 AM a 11:00 AM"
        )
        
        # Mock no conflicts
        mock_booking_dao.get_booking_conflicts.return_value = []
        mock_booking_dao.get_user_bookings_for_date.return_value = []
        
        # Mock successful creation
        created_booking = BookingRequestModel(
            request_id=str(uuid.uuid4()),
            user_id=user_id,
            court_id=booking_request.court_id,
            booking_date=booking_request.booking_date.isoformat(),
            time_slot=booking_request.time_slot,
            status=BookingStatus.SCHEDULED.value,
            retry_count=0,
            max_retries=3,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
        mock_booking_dao.create_booking_request.return_value = created_booking
        
        # Act
        result = booking_service.create_booking_request(booking_request, user_id)
        
        # Assert
        assert isinstance(result, BookingResponse)
        assert result.status == BookingStatus.SCHEDULED
        assert result.scheduled_for is not None
        assert "scheduled" in result.message.lower()
    
    def test_booking_status_transitions(self, booking_service, mock_booking_dao):
        """Test booking status transitions"""
        # Arrange
        booking_id = str(uuid.uuid4())
        booking_model = BookingRequestFactory.create_booking_request(
            request_id=booking_id,
            status=BookingStatus.PENDING.value
        )
        
        # Test valid transitions
        valid_transitions = [
            (BookingStatus.PENDING, BookingStatus.PROCESSING),
            (BookingStatus.PROCESSING, BookingStatus.CONFIRMED),
        ]
        
        for current_status, new_status in valid_transitions:
            # Update booking model status
            booking_model.status = current_status.value
            mock_booking_dao.get_booking_request.return_value = booking_model
            
            # Mock successful update
            updated_booking = BookingRequestModel(**booking_model.__dict__)
            updated_booking.status = new_status.value
            updated_booking.updated_at = datetime.now().isoformat()
            mock_booking_dao.update_booking_request.return_value = updated_booking
            
            # Act
            result = booking_service.update_booking_status(booking_id, new_status, f"Updated to {new_status.value}")
            
            # Assert
            assert isinstance(result, BookingResponse)
            assert result.status == new_status
            assert result.booking_id == booking_id
    
    def test_invalid_status_transition(self, booking_service, mock_booking_dao):
        """Test invalid status transitions are rejected"""
        # Arrange
        booking_id = str(uuid.uuid4())
        booking_model = BookingRequestFactory.create_booking_request(
            request_id=booking_id,
            status=BookingStatus.CONFIRMED.value
        )
        mock_booking_dao.get_booking_request.return_value = booking_model
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid status transition"):
            booking_service.update_booking_status(booking_id, BookingStatus.PENDING)
    
    def test_get_bookings_by_status(self, booking_service, mock_booking_dao):
        """Test getting bookings by status"""
        # Arrange
        status = BookingStatus.PENDING
        bookings = [
            BookingRequestFactory.create_booking_request(status=status.value),
            BookingRequestFactory.create_booking_request(status=status.value)
        ]
        mock_booking_dao.get_requests_by_status.return_value = bookings
        
        # Act
        result = booking_service.get_bookings_by_status(status, limit=10)
        
        # Assert
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(booking, BookingResponse) for booking in result)
        assert all(booking.status == status for booking in result)
        
        # Verify DAO call
        mock_booking_dao.get_requests_by_status.assert_called_once_with(status, 10)
    
    def test_cleanup_old_bookings(self, booking_service, mock_booking_dao):
        """Test cleanup of old bookings"""
        # Arrange
        old_bookings = [
            BookingRequestFactory.create_booking_request(status=BookingStatus.CONFIRMED.value),
            BookingRequestFactory.create_booking_request(status=BookingStatus.CANCELLED.value),
            BookingRequestFactory.create_booking_request(status=BookingStatus.PENDING.value)  # Should not be cleaned
        ]
        mock_booking_dao.get_old_bookings.return_value = old_bookings
        mock_booking_dao.delete_booking_request.return_value = True
        
        # Act
        cleanup_count = booking_service.cleanup_old_bookings(days_old=30)
        
        # Assert
        assert cleanup_count == 2  # Only confirmed and cancelled should be cleaned
        
        # Verify DAO calls
        mock_booking_dao.get_old_bookings.assert_called_once()
        assert mock_booking_dao.delete_booking_request.call_count == 2
    
    def test_expire_old_requests(self, booking_service, mock_booking_dao):
        """Test expiration of old requests"""
        # Arrange
        old_requests = [
            BookingRequestFactory.create_booking_request(status=BookingStatus.PENDING.value),
            BookingRequestFactory.create_booking_request(status=BookingStatus.SCHEDULED.value)
        ]
        mock_booking_dao.get_old_requests_by_status.return_value = old_requests
        
        # Mock update_booking_status method
        with patch.object(booking_service, 'update_booking_status') as mock_update:
            mock_update.return_value = Mock()
            
            # Act
            expired_count = booking_service.expire_old_requests(hours_old=24)
            
            # Assert
            assert expired_count == 2
            assert mock_update.call_count == 2
            
            # Verify expire_booking was called for each request
            for request in old_requests:
                mock_update.assert_any_call(request.request_id, BookingStatus.EXPIRED, "Booking expired")
    
    def test_court_availability_calculation(self, booking_service):
        """Test court availability calculation"""
        # Act
        availability = booking_service.get_court_availability()
        
        # Assert
        assert hasattr(availability, 'courts')
        assert hasattr(availability, 'current_date')
        assert len(availability.courts) == 2  # Two courts configured
        
        # Check court 1 (10-day window)
        court1 = next(court for court in availability.courts if court.court_id == 1)
        assert court1.booking_window_days == 10
        assert len(court1.available_dates) == 10
        
        # Check court 2 (9-day window)
        court2 = next(court for court in availability.courts if court.court_id == 2)
        assert court2.booking_window_days == 9
        assert len(court2.available_dates) == 9
    
    def test_cancel_booking_success(self, booking_service, mock_booking_dao):
        """Test successful booking cancellation"""
        # Arrange
        booking_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        booking_model = BookingRequestFactory.create_booking_request(
            request_id=booking_id,
            user_id=user_id,
            status=BookingStatus.PENDING.value
        )
        mock_booking_dao.get_booking_request.return_value = booking_model
        mock_booking_dao.update_booking_request.return_value = booking_model
        
        # Act
        result = booking_service.cancel_booking(booking_id, user_id)
        
        # Assert
        assert result is True
        mock_booking_dao.update_booking_request.assert_called_once()
    
    def test_cancel_booking_wrong_user(self, booking_service, mock_booking_dao):
        """Test booking cancellation by wrong user"""
        # Arrange
        booking_id = str(uuid.uuid4())
        user_id = str(uuid.uuid4())
        wrong_user_id = str(uuid.uuid4())
        booking_model = BookingRequestFactory.create_booking_request(
            request_id=booking_id,
            user_id=user_id,
            status=BookingStatus.PENDING.value
        )
        mock_booking_dao.get_booking_request.return_value = booking_model
        
        # Act
        result = booking_service.cancel_booking(booking_id, wrong_user_id)
        
        # Assert
        assert result is False
        mock_booking_dao.update_booking_request.assert_not_called()
    
    def test_booking_validation_comprehensive(self, booking_service, mock_booking_dao):
        """Test comprehensive booking validation"""
        # Arrange
        user_id = str(uuid.uuid4())
        booking_request = BookingRequest(
            court_id=1,
            booking_date=date.today() + timedelta(days=5),
            time_slot="De 10:00 AM a 11:00 AM"
        )
        
        # Mock no conflicts and within user limits
        mock_booking_dao.get_booking_conflicts.return_value = []
        mock_booking_dao.get_user_bookings_for_date.return_value = []
        
        # Act
        validation = booking_service.validate_booking_request(booking_request, user_id)
        
        # Assert
        assert isinstance(validation, BookingValidation)
        assert validation.is_valid is True
        assert validation.is_available_now is True
        assert validation.is_schedulable is False
        assert validation.court_booking_window == 10  # Court 1 window
        assert "available" in validation.message.lower()
    
    def test_process_booking_workflow(self, booking_service, mock_booking_dao):
        """Test complete booking processing workflow"""
        # Arrange
        booking_id = str(uuid.uuid4())
        
        # Create booking progression through statuses
        booking_states = [
            BookingStatus.PENDING,
            BookingStatus.PROCESSING,
            BookingStatus.CONFIRMED
        ]
        
        for i, status in enumerate(booking_states):
            booking_model = BookingRequestFactory.create_booking_request(
                request_id=booking_id,
                status=status.value
            )
            mock_booking_dao.get_booking_request.return_value = booking_model
            
            if i < len(booking_states) - 1:
                # Mock transition to next status
                next_status = booking_states[i + 1]
                updated_booking = BookingRequestModel(**booking_model.__dict__)
                updated_booking.status = next_status.value
                updated_booking.updated_at = datetime.now().isoformat()
                mock_booking_dao.update_booking_request.return_value = updated_booking
                
                # Test processing methods
                if status == BookingStatus.PENDING:
                    result = booking_service.process_booking(booking_id)
                    assert result.status == BookingStatus.PROCESSING
                elif status == BookingStatus.PROCESSING:
                    result = booking_service.confirm_booking(booking_id, "CONF123")
                    assert result.status == BookingStatus.CONFIRMED
                    assert "CONF123" in result.message