# ABOUTME: Factory classes for generating test data with valid attributes
# ABOUTME: Creates realistic test instances of UserConfig, BookingRequest, SystemConfig

import uuid
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from ..models.user_config import UserConfig
from ..models.booking_request import BookingRequest, BookingStatus, BookingPriority
from ..models.system_config import SystemConfig, ConfigCategory, ConfigValueType


class UserConfigFactory:
    """Factory for creating UserConfig test instances"""
    
    FIRST_NAMES = [
        "John", "Jane", "Michael", "Sarah", "David", "Lisa", "Robert", "Maria",
        "James", "Jennifer", "William", "Linda", "Richard", "Patricia", "Joseph", "Barbara"
    ]
    
    LAST_NAMES = [
        "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
        "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", "Thomas"
    ]
    
    EMAIL_DOMAINS = [
        "gmail.com", "yahoo.com", "outlook.com", "hotmail.com", "test.com", "example.com"
    ]
    
    PHONE_PREFIXES = ["555", "123", "456", "789", "321", "654"]
    
    @classmethod
    def create(cls, **overrides) -> UserConfig:
        """Create a UserConfig with random valid data"""
        first_name = random.choice(cls.FIRST_NAMES)
        last_name = random.choice(cls.LAST_NAMES)
        username = f"{first_name.lower()}_{last_name.lower()}_{random.randint(1, 999)}"
        
        defaults = {
            "user_id": f"user_{uuid.uuid4().hex[:8]}",
            "username": username,
            "password": f"SecurePass{random.randint(100, 999)}!",
            "email": f"{username}@{random.choice(cls.EMAIL_DOMAINS)}",
            "first_name": first_name,
            "last_name": last_name,
            "preferred_courts": random.sample([5, 7, 17, 19, 23], k=random.randint(1, 3)),
            "preferred_times": random.sample([
                "De 08:00 AM a 09:00 AM",
                "De 09:00 AM a 10:00 AM",
                "De 10:00 AM a 11:00 AM",
                "De 05:00 PM a 06:00 PM",
                "De 06:00 PM a 07:00 PM"
            ], k=random.randint(1, 3)),
            "auto_book": random.choice([True, False]),
            "max_bookings_per_day": random.randint(1, 5),
            "booking_advance_days": random.randint(1, 14),
            "phone_number": f"{random.choice(cls.PHONE_PREFIXES)}-{random.randint(100, 999)}-{random.randint(1000, 9999)}",
            "notifications_enabled": random.choice([True, False]),
            "is_active": True
        }
        
        # Apply overrides
        defaults.update(overrides)
        
        return UserConfig(**defaults)
    
    @classmethod
    def create_minimal(cls, **overrides) -> UserConfig:
        """Create a UserConfig with minimal required fields"""
        defaults = {
            "user_id": f"user_{uuid.uuid4().hex[:8]}",
            "username": f"testuser_{random.randint(1, 999)}",
            "password": "TestPass123!",
            "email": f"test{random.randint(1, 999)}@test.com",
            "first_name": "Test",
            "last_name": "User"
        }
        
        defaults.update(overrides)
        return UserConfig(**defaults)
    
    @classmethod
    def create_admin(cls, **overrides) -> UserConfig:
        """Create an admin UserConfig"""
        defaults = {
            "user_id": f"admin_{uuid.uuid4().hex[:8]}",
            "username": f"admin_{random.randint(1, 999)}",
            "password": "AdminPass123!",
            "email": f"admin{random.randint(1, 999)}@tennis-system.com",
            "first_name": "Admin",
            "last_name": "User",
            "preferred_courts": [5, 7, 17, 19, 23],  # All courts
            "max_bookings_per_day": 10,
            "booking_advance_days": 30,
            "auto_book": False,
            "is_active": True
        }
        
        defaults.update(overrides)
        return UserConfig(**defaults)
    
    @classmethod
    def create_inactive(cls, **overrides) -> UserConfig:
        """Create an inactive UserConfig"""
        user = cls.create(**overrides)
        user.is_active = False
        return user
    
    @classmethod
    def create_batch(cls, count: int, **common_overrides) -> List[UserConfig]:
        """Create multiple UserConfig instances"""
        users = []
        for i in range(count):
            overrides = common_overrides.copy()
            if 'user_id' not in overrides:
                overrides['user_id'] = f"user_{i}_{uuid.uuid4().hex[:6]}"
            users.append(cls.create(**overrides))
        return users


class BookingRequestFactory:
    """Factory for creating BookingRequest test instances"""
    
    TIME_SLOTS = [
        "De 08:00 AM a 09:00 AM",
        "De 09:00 AM a 10:00 AM",
        "De 10:00 AM a 11:00 AM",
        "De 11:00 AM a 12:00 PM",
        "De 12:00 PM a 01:00 PM",
        "De 01:00 PM a 02:00 PM",
        "De 02:00 PM a 03:00 PM",
        "De 03:00 PM a 04:00 PM",
        "De 04:00 PM a 05:00 PM",
        "De 05:00 PM a 06:00 PM",
        "De 06:00 PM a 07:00 PM",
        "De 07:00 PM a 08:00 PM"
    ]
    
    COURTS = [5, 7, 17, 19, 23]
    
    @classmethod
    def create(cls, **overrides) -> BookingRequest:
        """Create a BookingRequest with random valid data"""
        # Generate future date (1-7 days from now)
        future_date = datetime.now() + timedelta(days=random.randint(1, 7))
        booking_date = future_date.strftime('%Y-%m-%d')
        
        defaults = {
            "request_id": f"req_{uuid.uuid4().hex[:12]}",
            "user_id": f"user_{uuid.uuid4().hex[:8]}",
            "booking_date": booking_date,
            "time_slot": random.choice(cls.TIME_SLOTS),
            "court_id": random.choice(cls.COURTS),
            "status": random.choice(list(BookingStatus)),
            "priority": random.choice(list(BookingPriority)),
            "auto_retry": random.choice([True, False]),
            "max_retries": random.randint(1, 5),
            "retry_count": 0,
            "notes": f"Test booking request {random.randint(1, 999)}" if random.choice([True, False]) else None
        }
        
        # Apply overrides
        defaults.update(overrides)
        
        return BookingRequest(**defaults)
    
    @classmethod
    def create_pending(cls, **overrides) -> BookingRequest:
        """Create a pending BookingRequest"""
        overrides['status'] = BookingStatus.PENDING
        return cls.create(**overrides)
    
    @classmethod
    def create_confirmed(cls, **overrides) -> BookingRequest:
        """Create a confirmed BookingRequest"""
        overrides['status'] = BookingStatus.CONFIRMED
        overrides['confirmation_code'] = f"CONF_{random.randint(100000, 999999)}"
        return cls.create(**overrides)
    
    @classmethod
    def create_failed(cls, **overrides) -> BookingRequest:
        """Create a failed BookingRequest"""
        overrides['status'] = BookingStatus.FAILED
        overrides['error_message'] = "Court not available"
        overrides['retry_count'] = random.randint(1, 3)
        return cls.create(**overrides)
    
    @classmethod
    def create_cancelled(cls, **overrides) -> BookingRequest:
        """Create a cancelled BookingRequest"""
        overrides['status'] = BookingStatus.CANCELLED
        return cls.create(**overrides)
    
    @classmethod
    def create_for_user(cls, user_id: str, **overrides) -> BookingRequest:
        """Create a BookingRequest for a specific user"""
        overrides['user_id'] = user_id
        return cls.create(**overrides)
    
    @classmethod
    def create_for_date(cls, booking_date: str, **overrides) -> BookingRequest:
        """Create a BookingRequest for a specific date"""
        overrides['booking_date'] = booking_date
        return cls.create(**overrides)
    
    @classmethod
    def create_for_court(cls, court_id: int, **overrides) -> BookingRequest:
        """Create a BookingRequest for a specific court"""
        overrides['court_id'] = court_id
        return cls.create(**overrides)
    
    @classmethod
    def create_high_priority(cls, **overrides) -> BookingRequest:
        """Create a high priority BookingRequest"""
        overrides['priority'] = BookingPriority.HIGH
        return cls.create(**overrides)
    
    @classmethod
    def create_with_retries(cls, retry_count: int = None, **overrides) -> BookingRequest:
        """Create a BookingRequest with specific retry count"""
        if retry_count is None:
            retry_count = random.randint(1, 3)
        
        overrides['retry_count'] = retry_count
        overrides['max_retries'] = retry_count + random.randint(1, 3)
        overrides['status'] = BookingStatus.FAILED
        return cls.create(**overrides)
    
    @classmethod
    def create_batch(cls, count: int, **common_overrides) -> List[BookingRequest]:
        """Create multiple BookingRequest instances"""
        requests = []
        for i in range(count):
            overrides = common_overrides.copy()
            if 'request_id' not in overrides:
                overrides['request_id'] = f"req_{i}_{uuid.uuid4().hex[:8]}"
            requests.append(cls.create(**overrides))
        return requests


class SystemConfigFactory:
    """Factory for creating SystemConfig test instances"""
    
    @classmethod
    def create(cls, **overrides) -> SystemConfig:
        """Create a SystemConfig with random valid data"""
        config_key = f"test_config_{uuid.uuid4().hex[:8]}"
        
        defaults = {
            "config_key": config_key,
            "config_value": f"test_value_{random.randint(1, 999)}",
            "value_type": ConfigValueType.STRING,
            "category": random.choice(list(ConfigCategory)),
            "description": f"Test configuration for {config_key}",
            "is_active": True,
            "is_required": random.choice([True, False]),
            "is_sensitive": random.choice([True, False]),
            "version": "1.0"
        }
        
        # Apply overrides
        defaults.update(overrides)
        
        return SystemConfig(**defaults)
    
    @classmethod
    def create_string_config(cls, value: str = None, **overrides) -> SystemConfig:
        """Create a string configuration"""
        if value is None:
            value = f"string_value_{random.randint(1, 999)}"
        
        overrides.update({
            "config_value": value,
            "value_type": ConfigValueType.STRING,
            "default_value": value
        })
        return cls.create(**overrides)
    
    @classmethod
    def create_integer_config(cls, value: int = None, **overrides) -> SystemConfig:
        """Create an integer configuration"""
        if value is None:
            value = random.randint(1, 100)
        
        overrides.update({
            "config_value": value,
            "value_type": ConfigValueType.INTEGER,
            "default_value": value,
            "min_value": 1,
            "max_value": 100
        })
        return cls.create(**overrides)
    
    @classmethod
    def create_boolean_config(cls, value: bool = None, **overrides) -> SystemConfig:
        """Create a boolean configuration"""
        if value is None:
            value = random.choice([True, False])
        
        overrides.update({
            "config_value": value,
            "value_type": ConfigValueType.BOOLEAN,
            "default_value": value
        })
        return cls.create(**overrides)
    
    @classmethod
    def create_list_config(cls, value: List[Any] = None, **overrides) -> SystemConfig:
        """Create a list configuration"""
        if value is None:
            value = [f"item_{i}" for i in range(random.randint(1, 5))]
        
        overrides.update({
            "config_value": value,
            "value_type": ConfigValueType.LIST,
            "default_value": value
        })
        return cls.create(**overrides)
    
    @classmethod
    def create_dict_config(cls, value: Dict[str, Any] = None, **overrides) -> SystemConfig:
        """Create a dictionary configuration"""
        if value is None:
            value = {
                f"key_{i}": f"value_{i}" for i in range(random.randint(1, 3))
            }
        
        overrides.update({
            "config_value": value,
            "value_type": ConfigValueType.DICT,
            "default_value": value
        })
        return cls.create(**overrides)
    
    @classmethod
    def create_courts_config(cls, **overrides) -> SystemConfig:
        """Create the courts configuration"""
        overrides.update({
            "config_key": "available_courts",
            "config_value": [5, 7, 17, 19, 23],
            "value_type": ConfigValueType.LIST,
            "category": ConfigCategory.COURTS,
            "description": "List of available court IDs",
            "is_required": True
        })
        return cls.create(**overrides)
    
    @classmethod
    def create_time_slots_config(cls, **overrides) -> SystemConfig:
        """Create the time slots configuration"""
        time_slots = [
            "De 08:00 AM a 09:00 AM",
            "De 09:00 AM a 10:00 AM",
            "De 10:00 AM a 11:00 AM",
            "De 05:00 PM a 06:00 PM",
            "De 06:00 PM a 07:00 PM"
        ]
        
        overrides.update({
            "config_key": "available_time_slots",
            "config_value": time_slots,
            "value_type": ConfigValueType.LIST,
            "category": ConfigCategory.SCHEDULING,
            "description": "Available time slots for booking",
            "is_required": True
        })
        return cls.create(**overrides)
    
    @classmethod
    def create_sensitive_config(cls, **overrides) -> SystemConfig:
        """Create a sensitive configuration"""
        overrides.update({
            "is_sensitive": True,
            "config_value": "sensitive_value_123",
            "description": "Sensitive configuration value"
        })
        return cls.create(**overrides)
    
    @classmethod
    def create_required_config(cls, **overrides) -> SystemConfig:
        """Create a required configuration"""
        overrides.update({
            "is_required": True,
            "description": "Required configuration value"
        })
        return cls.create(**overrides)
    
    @classmethod
    def create_inactive_config(cls, **overrides) -> SystemConfig:
        """Create an inactive configuration"""
        overrides['is_active'] = False
        return cls.create(**overrides)
    
    @classmethod
    def create_by_category(cls, category: ConfigCategory, **overrides) -> SystemConfig:
        """Create a configuration for a specific category"""
        overrides['category'] = category
        return cls.create(**overrides)
    
    @classmethod
    def create_batch(cls, count: int, **common_overrides) -> List[SystemConfig]:
        """Create multiple SystemConfig instances"""
        configs = []
        for i in range(count):
            overrides = common_overrides.copy()
            if 'config_key' not in overrides:
                overrides['config_key'] = f"test_config_{i}_{uuid.uuid4().hex[:6]}"
            configs.append(cls.create(**overrides))
        return configs


class TestDataFactory:
    """Main factory class that combines all factories"""
    
    users = UserConfigFactory
    bookings = BookingRequestFactory
    configs = SystemConfigFactory
    
    @classmethod
    def create_complete_test_scenario(cls) -> Dict[str, Any]:
        """Create a complete test scenario with related data"""
        # Create users
        admin_user = cls.users.create_admin()
        regular_users = cls.users.create_batch(3)
        
        # Create system configs
        courts_config = cls.configs.create_courts_config()
        time_slots_config = cls.configs.create_time_slots_config()
        other_configs = cls.configs.create_batch(5)
        
        # Create booking requests for users
        booking_requests = []
        for user in regular_users:
            # Create 2-3 bookings per user
            user_bookings = cls.bookings.create_batch(
                random.randint(2, 3),
                user_id=user.user_id
            )
            booking_requests.extend(user_bookings)
        
        return {
            'admin_user': admin_user,
            'regular_users': regular_users,
            'all_users': [admin_user] + regular_users,
            'system_configs': [courts_config, time_slots_config] + other_configs,
            'booking_requests': booking_requests,
            'total_entities': 1 + len(regular_users) + len(other_configs) + 2 + len(booking_requests)
        }
    
    @classmethod
    def create_user_with_bookings(cls, booking_count: int = 3) -> Dict[str, Any]:
        """Create a user with associated booking requests"""
        user = cls.users.create()
        bookings = cls.bookings.create_batch(booking_count, user_id=user.user_id)
        
        return {
            'user': user,
            'bookings': bookings
        }
    
    @classmethod
    def create_court_booking_scenario(cls, court_id: int) -> Dict[str, Any]:
        """Create a scenario for a specific court with multiple bookings"""
        users = cls.users.create_batch(3)
        
        # Create bookings for the same court on different days
        bookings = []
        for i, user in enumerate(users):
            future_date = (datetime.now() + timedelta(days=i+1)).strftime('%Y-%m-%d')
            booking = cls.bookings.create_for_court(
                court_id,
                user_id=user.user_id,
                booking_date=future_date
            )
            bookings.append(booking)
        
        return {
            'users': users,
            'bookings': bookings,
            'court_id': court_id
        }