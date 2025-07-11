# ABOUTME: Comprehensive test suite for FastAPI endpoints using test client
# ABOUTME: Tests authentication, user management, and booking operations with court-specific logic

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
import json
import os

# Set test environment before importing the app
os.environ['TENNIS_ENVIRONMENT'] = 'development'
os.environ['DYNAMODB_ENDPOINT'] = 'http://localhost:8000'

from src.api.main import app
from src.models import EncryptedUserConfig
from src.models.booking_request import BookingRequest

# Test client
client = TestClient(app)

@pytest.fixture
def mock_user():
    """Mock user for testing"""
    return EncryptedUserConfig(
        user_id="test_user_123",
        username="testuser",
        password="TestPass123!",
        email="test@example.com",
        first_name="Test",
        last_name="User",
        is_active=True,
        preferred_courts=[1, 2],
        preferred_times=["De 08:00 AM a 09:00 AM"],
        max_bookings_per_day=1,
        auto_booking_enabled=False
    )

@pytest.fixture
def mock_booking_request():
    """Mock booking request for testing"""
    return BookingRequest(
        request_id="booking_123",
        user_id="test_user_123",
        court_id=1,
        booking_date=(date.today() + timedelta(days=1)).isoformat(),
        time_slot="De 08:00 AM a 09:00 AM",
        status="pending",
        retry_count=0,
        max_retries=3
    )

@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer test_token"}

class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["message"] == "Tennis Court Booking API"
    
    @patch('src.api.main.get_dynamodb_resource')
    @patch('src.api.main.get_encryption_service')
    def test_health_check_healthy(self, mock_encryption, mock_db):
        """Test health check when all services are healthy"""
        # Mock healthy database
        mock_db.return_value.tables.limit.return_value = []
        
        # Mock healthy encryption
        mock_encryption.return_value.health_check.return_value = {"status": "healthy"}
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "healthy"
        assert data["encryption"] == "healthy"
    
    @patch('src.api.main.get_dynamodb_resource')
    @patch('src.api.main.get_encryption_service')
    def test_health_check_unhealthy(self, mock_encryption, mock_db):
        """Test health check when services are unhealthy"""
        # Mock unhealthy database
        mock_db.side_effect = Exception("Database error")
        
        # Mock unhealthy encryption
        mock_encryption.return_value.health_check.return_value = {"status": "unhealthy"}
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "unhealthy"

class TestAuthenticationEndpoints:
    """Test authentication endpoints"""
    
    @patch('src.api.auth.auth_service.authenticate_user')
    def test_login_success(self, mock_auth, mock_user):
        """Test successful login"""
        mock_auth.return_value = mock_user
        
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "TestPass123!"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user_id"] == "test_user_123"
    
    @patch('src.api.auth.auth_service.authenticate_user')
    def test_login_failure(self, mock_auth):
        """Test failed login"""
        mock_auth.return_value = None
        
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_login_invalid_data(self):
        """Test login with invalid data"""
        response = client.post("/auth/login", json={
            "username": "ab",  # Too short
            "password": "123"  # Too short
        })
        
        assert response.status_code == 422
    
    def test_logout(self):
        """Test logout endpoint"""
        response = client.post("/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Logout successful"
    
    @patch('src.api.auth.auth_service.get_current_user_profile')
    def test_get_current_user_info(self, mock_profile, mock_user):
        """Test get current user info"""
        mock_profile.return_value = mock_user
        
        response = client.get("/auth/me", headers={"Authorization": "Bearer test_token"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"
        assert data["username"] == "testuser"

class TestUserEndpoints:
    """Test user management endpoints"""
    
    @patch('src.api.routers.users.get_current_user_profile')
    def test_get_current_user(self, mock_profile, mock_user):
        """Test get current user profile"""
        mock_profile.return_value = mock_user
        
        response = client.get("/users/me", headers={"Authorization": "Bearer test_token"})
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"
        assert data["username"] == "testuser"
    
    @patch('src.api.routers.users.get_current_user_profile')
    @patch('src.api.routers.users.user_dao.get_user')
    @patch('src.api.routers.users.user_dao.update_user')
    def test_update_user_config(self, mock_update, mock_get, mock_profile, mock_user):
        """Test update user configuration"""
        mock_profile.return_value = mock_user
        mock_get.return_value = mock_user
        mock_update.return_value = mock_user
        
        response = client.put("/users/me/config", 
                            headers={"Authorization": "Bearer test_token"},
                            json={
                                "first_name": "Updated",
                                "preferred_courts": [1]
                            })
        
        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "test_user_123"
    
    @patch('src.api.routers.users.get_current_user_profile')
    @patch('src.api.routers.users.user_dao.get_user_security_summary')
    def test_get_security_summary(self, mock_security, mock_profile, mock_user):
        """Test get user security summary"""
        mock_profile.return_value = mock_user
        mock_security.return_value = {
            "has_weak_credentials": False,
            "recommendations": []
        }
        
        response = client.get("/users/me/security", 
                            headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert "has_weak_credentials" in data
    
    @patch('src.api.routers.users.get_current_user_profile')
    @patch('src.api.routers.users.user_dao.deactivate_user')
    def test_deactivate_user(self, mock_deactivate, mock_profile, mock_user):
        """Test deactivate user account"""
        mock_profile.return_value = mock_user
        mock_deactivate.return_value = None
        
        response = client.delete("/users/me", 
                               headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        assert "deactivated successfully" in response.json()["message"]

class TestBookingEndpoints:
    """Test booking management endpoints"""
    
    @patch('src.api.routers.bookings.get_current_user_profile')
    @patch('src.api.routers.bookings.booking_service.create_booking_request')
    def test_create_booking_success(self, mock_create, mock_profile, mock_user):
        """Test successful booking creation"""
        mock_profile.return_value = mock_user
        
        # Mock successful booking response
        from src.api.models import BookingResponse, BookingStatus
        mock_response = BookingResponse(
            booking_id="booking_123",
            user_id="test_user_123",
            court_id=1,
            booking_date=date.today() + timedelta(days=1),
            time_slot="De 08:00 AM a 09:00 AM",
            status=BookingStatus.PENDING,
            message="Booking request created",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_create.return_value = mock_response
        
        response = client.post("/bookings/",
                             headers={"Authorization": "Bearer test_token"},
                             json={
                                 "court_id": 1,
                                 "booking_date": (date.today() + timedelta(days=1)).isoformat(),
                                 "time_slot": "De 08:00 AM a 09:00 AM"
                             })
        
        assert response.status_code == 200
        data = response.json()
        assert data["booking_id"] == "booking_123"
        assert data["status"] == "pending"
    
    @patch('src.api.routers.bookings.get_current_user_profile')
    @patch('src.api.routers.bookings.booking_service.create_booking_request')
    def test_create_booking_scheduled(self, mock_create, mock_profile, mock_user):
        """Test booking creation that gets scheduled"""
        mock_profile.return_value = mock_user
        
        # Mock scheduled booking response
        from src.api.models import BookingResponse, BookingStatus
        mock_response = BookingResponse(
            booking_id="booking_123",
            user_id="test_user_123",
            court_id=1,
            booking_date=date.today() + timedelta(days=10),
            time_slot="De 08:00 AM a 09:00 AM",
            status=BookingStatus.SCHEDULED,
            message="Booking scheduled for midnight",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            scheduled_for=datetime.now() + timedelta(hours=12)
        )
        mock_create.return_value = mock_response
        
        response = client.post("/bookings/",
                             headers={"Authorization": "Bearer test_token"},
                             json={
                                 "court_id": 1,
                                 "booking_date": (date.today() + timedelta(days=10)).isoformat(),
                                 "time_slot": "De 08:00 AM a 09:00 AM"
                             })
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "scheduled"
        assert data["scheduled_for"] is not None
    
    @patch('src.api.routers.bookings.get_current_user_profile')
    @patch('src.api.routers.bookings.booking_service.create_booking_request')
    def test_create_booking_failed(self, mock_create, mock_profile, mock_user):
        """Test booking creation that fails validation"""
        mock_profile.return_value = mock_user
        
        # Mock failed booking response
        from src.api.models import BookingResponse, BookingStatus
        mock_response = BookingResponse(
            booking_id="",
            user_id="test_user_123",
            court_id=1,
            booking_date=date.today() + timedelta(days=15),
            time_slot="De 08:00 AM a 09:00 AM",
            status=BookingStatus.FAILED,
            message="Court 1 only allows bookings 10 days in advance",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_create.return_value = mock_response
        
        response = client.post("/bookings/",
                             headers={"Authorization": "Bearer test_token"},
                             json={
                                 "court_id": 1,
                                 "booking_date": (date.today() + timedelta(days=15)).isoformat(),
                                 "time_slot": "De 08:00 AM a 09:00 AM"
                             })
        
        assert response.status_code == 400
        assert "10 days in advance" in response.json()["detail"]
    
    @patch('src.api.routers.bookings.get_current_user_profile')
    @patch('src.api.routers.bookings.booking_service.get_user_bookings')
    def test_get_user_bookings(self, mock_get_bookings, mock_profile, mock_user):
        """Test get user bookings"""
        mock_profile.return_value = mock_user
        mock_get_bookings.return_value = []
        
        response = client.get("/bookings/", 
                            headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert "bookings" in data
        assert "total" in data
        assert data["page"] == 1
        assert data["per_page"] == 10
    
    @patch('src.api.routers.bookings.get_current_user_profile')
    @patch('src.api.routers.bookings.booking_service.get_booking_by_id')
    def test_get_booking_by_id(self, mock_get_booking, mock_profile, mock_user):
        """Test get specific booking by ID"""
        mock_profile.return_value = mock_user
        
        from src.api.models import BookingResponse, BookingStatus
        mock_response = BookingResponse(
            booking_id="booking_123",
            user_id="test_user_123",
            court_id=1,
            booking_date=date.today() + timedelta(days=1),
            time_slot="De 08:00 AM a 09:00 AM",
            status=BookingStatus.CONFIRMED,
            message="Booking confirmed",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_get_booking.return_value = mock_response
        
        response = client.get("/bookings/booking_123", 
                            headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["booking_id"] == "booking_123"
        assert data["status"] == "confirmed"
    
    @patch('src.api.routers.bookings.get_current_user_profile')
    @patch('src.api.routers.bookings.booking_service.get_booking_by_id')
    def test_get_booking_not_found(self, mock_get_booking, mock_profile, mock_user):
        """Test get booking that doesn't exist"""
        mock_profile.return_value = mock_user
        mock_get_booking.return_value = None
        
        response = client.get("/bookings/nonexistent", 
                            headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    @patch('src.api.routers.bookings.get_current_user_profile')
    @patch('src.api.routers.bookings.booking_service.get_court_availability')
    def test_get_court_availability(self, mock_availability, mock_profile, mock_user):
        """Test get court availability"""
        mock_profile.return_value = mock_user
        
        from src.api.models import AvailabilityResponse, CourtAvailability
        mock_response = AvailabilityResponse(
            courts=[
                CourtAvailability(
                    court_id=1,
                    available_dates=[date.today() + timedelta(days=i) for i in range(10)],
                    booking_window_days=10
                ),
                CourtAvailability(
                    court_id=2,
                    available_dates=[date.today() + timedelta(days=i) for i in range(9)],
                    booking_window_days=9
                )
            ],
            current_date=date.today()
        )
        mock_availability.return_value = mock_response
        
        response = client.get("/bookings/availability/courts", 
                            headers={"Authorization": "Bearer test_token"})
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["courts"]) == 2
        assert data["courts"][0]["court_id"] == 1
        assert data["courts"][0]["booking_window_days"] == 10
        assert data["courts"][1]["court_id"] == 2
        assert data["courts"][1]["booking_window_days"] == 9
    
    @patch('src.api.routers.bookings.get_current_user_profile')
    @patch('src.api.routers.bookings.booking_service.validate_booking_request')
    def test_validate_booking(self, mock_validate, mock_profile, mock_user):
        """Test booking validation"""
        mock_profile.return_value = mock_user
        
        from src.api.models import BookingValidation
        mock_validation = BookingValidation(
            is_valid=True,
            is_available_now=True,
            is_schedulable=False,
            message="Court 1 is available for booking",
            court_booking_window=10
        )
        mock_validate.return_value = mock_validation
        
        response = client.post("/bookings/validate",
                             headers={"Authorization": "Bearer test_token"},
                             json={
                                 "court_id": 1,
                                 "booking_date": (date.today() + timedelta(days=1)).isoformat(),
                                 "time_slot": "De 08:00 AM a 09:00 AM"
                             })
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_valid"] is True
        assert data["is_available_now"] is True
        assert data["court_booking_window"] == 10

class TestBookingValidationLogic:
    """Test booking validation logic"""
    
    def test_invalid_court_id(self):
        """Test booking with invalid court ID"""
        response = client.post("/bookings/",
                             headers={"Authorization": "Bearer test_token"},
                             json={
                                 "court_id": 99,  # Invalid court
                                 "booking_date": (date.today() + timedelta(days=1)).isoformat(),
                                 "time_slot": "De 08:00 AM a 09:00 AM"
                             })
        
        assert response.status_code == 422
    
    def test_invalid_date_format(self):
        """Test booking with invalid date format"""
        response = client.post("/bookings/",
                             headers={"Authorization": "Bearer test_token"},
                             json={
                                 "court_id": 1,
                                 "booking_date": "invalid-date",
                                 "time_slot": "De 08:00 AM a 09:00 AM"
                             })
        
        assert response.status_code == 422
    
    def test_past_date_booking(self):
        """Test booking with past date"""
        response = client.post("/bookings/",
                             headers={"Authorization": "Bearer test_token"},
                             json={
                                 "court_id": 1,
                                 "booking_date": (date.today() - timedelta(days=1)).isoformat(),
                                 "time_slot": "De 08:00 AM a 09:00 AM"
                             })
        
        assert response.status_code == 422
    
    def test_invalid_time_slot(self):
        """Test booking with invalid time slot format"""
        response = client.post("/bookings/",
                             headers={"Authorization": "Bearer test_token"},
                             json={
                                 "court_id": 1,
                                 "booking_date": (date.today() + timedelta(days=1)).isoformat(),
                                 "time_slot": "8:00 AM to 9:00 AM"  # Wrong format
                             })
        
        assert response.status_code == 422

class TestAuthenticationMiddleware:
    """Test authentication middleware"""
    
    def test_missing_token(self):
        """Test request without authentication token"""
        response = client.get("/users/me")
        assert response.status_code == 403
    
    def test_invalid_token(self):
        """Test request with invalid token"""
        response = client.get("/users/me", headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401