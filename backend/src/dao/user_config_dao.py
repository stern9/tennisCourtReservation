# ABOUTME: UserConfig Data Access Object with specific user operations
# ABOUTME: Provides validated CRUD operations and user-specific queries for UserConfig

from typing import Optional, List
import logging

from .base import BaseDAO, NotFoundError
from ..models.user_config import UserConfig

logger = logging.getLogger(__name__)


class UserConfigDAO(BaseDAO[UserConfig]):
    """Data Access Object for UserConfig operations"""
    
    def __init__(self):
        super().__init__(UserConfig)
    
    def _get_table_name(self) -> str:
        """Get table name for UserConfig"""
        return "UserConfigs"
    
    def create_user(self, user_config: UserConfig) -> UserConfig:
        """Create a new user configuration"""
        return self.create(user_config)
    
    def get_user(self, user_id: str) -> Optional[UserConfig]:
        """Get user configuration by user ID"""
        return self.get(user_id=user_id)
    
    def get_user_by_username(self, username: str) -> Optional[UserConfig]:
        """Get user configuration by username"""
        # Since username is not the primary key, we need to scan
        # In a production system, you'd want a GSI on username
        try:
            response = self.table.scan(
                FilterExpression='username = :username',
                ExpressionAttributeValues={':username': username}
            )
            
            items = response.get('Items', [])
            if not items:
                return None
            
            if len(items) > 1:
                logger.warning(f"Multiple users found with username {username}")
            
            return self.model_class.from_dynamodb_item(items[0])
            
        except Exception as e:
            logger.error(f"Error getting user by username {username}: {e}")
            raise
    
    def get_user_by_email(self, email: str) -> Optional[UserConfig]:
        """Get user configuration by email"""
        try:
            response = self.table.scan(
                FilterExpression='email = :email',
                ExpressionAttributeValues={':email': email}
            )
            
            items = response.get('Items', [])
            if not items:
                return None
            
            if len(items) > 1:
                logger.warning(f"Multiple users found with email {email}")
            
            return self.model_class.from_dynamodb_item(items[0])
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise
    
    def update_user(self, user_config: UserConfig) -> UserConfig:
        """Update user configuration"""
        # Check if user exists first
        existing_user = self.get_user(user_config.user_id)
        if not existing_user:
            raise NotFoundError(f"User {user_config.user_id} not found")
        
        return self.update(user_config)
    
    def delete_user(self, user_id: str) -> bool:
        """Delete user configuration"""
        return self.delete(user_id=user_id)
    
    def user_exists(self, user_id: str) -> bool:
        """Check if user exists"""
        return self.exists(user_id=user_id)
    
    def username_exists(self, username: str) -> bool:
        """Check if username is already taken"""
        user = self.get_user_by_username(username)
        return user is not None
    
    def email_exists(self, email: str) -> bool:
        """Check if email is already registered"""
        user = self.get_user_by_email(email)
        return user is not None
    
    def get_active_users(self) -> List[UserConfig]:
        """Get all active users"""
        try:
            response = self.table.scan(
                FilterExpression='is_active = :is_active',
                ExpressionAttributeValues={':is_active': True}
            )
            
            users = []
            for item in response.get('Items', []):
                user = self.model_class.from_dynamodb_item(item)
                users.append(user)
            
            logger.debug(f"Retrieved {len(users)} active users")
            return users
            
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            raise
    
    def get_users_with_auto_book(self) -> List[UserConfig]:
        """Get users with auto-booking enabled"""
        try:
            response = self.table.scan(
                FilterExpression='auto_book = :auto_book AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':auto_book': True,
                    ':is_active': True
                }
            )
            
            users = []
            for item in response.get('Items', []):
                user = self.model_class.from_dynamodb_item(item)
                users.append(user)
            
            logger.debug(f"Retrieved {len(users)} users with auto-booking enabled")
            return users
            
        except Exception as e:
            logger.error(f"Error getting users with auto-booking: {e}")
            raise
    
    def get_users_by_court_preference(self, court_id: int) -> List[UserConfig]:
        """Get users who prefer a specific court"""
        try:
            response = self.table.scan(
                FilterExpression='contains(preferred_courts, :court_id) AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':court_id': court_id,
                    ':is_active': True
                }
            )
            
            users = []
            for item in response.get('Items', []):
                user = self.model_class.from_dynamodb_item(item)
                users.append(user)
            
            logger.debug(f"Retrieved {len(users)} users who prefer court {court_id}")
            return users
            
        except Exception as e:
            logger.error(f"Error getting users by court preference: {e}")
            raise
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserConfig]:
        """Authenticate user by username and password"""
        user = self.get_user_by_username(username)
        if not user:
            return None
        
        if not user.is_active:
            logger.warning(f"Authentication attempt for inactive user: {username}")
            return None
        
        # In a real system, you'd hash and compare passwords
        # This is simplified for demonstration
        if user.password == password:
            user.update_last_login()
            self.update_user(user)
            logger.info(f"User {username} authenticated successfully")
            return user
        
        logger.warning(f"Failed authentication attempt for user: {username}")
        return None
    
    def deactivate_user(self, user_id: str) -> bool:
        """Deactivate a user account"""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        user.deactivate()
        self.update_user(user)
        logger.info(f"Deactivated user: {user_id}")
        return True
    
    def activate_user(self, user_id: str) -> bool:
        """Activate a user account"""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        user.activate()
        self.update_user(user)
        logger.info(f"Activated user: {user_id}")
        return True
    
    def update_user_preferences(
        self, 
        user_id: str, 
        preferred_courts: Optional[List[int]] = None,
        preferred_times: Optional[List[str]] = None,
        auto_book: Optional[bool] = None,
        max_bookings_per_day: Optional[int] = None,
        booking_advance_days: Optional[int] = None
    ) -> UserConfig:
        """Update user booking preferences"""
        user = self.get_user(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found")
        
        if preferred_courts is not None:
            user.preferred_courts = preferred_courts
        
        if preferred_times is not None:
            user.preferred_times = preferred_times
        
        if auto_book is not None:
            user.auto_book = auto_book
        
        if max_bookings_per_day is not None:
            user.max_bookings_per_day = max_bookings_per_day
        
        if booking_advance_days is not None:
            user.booking_advance_days = booking_advance_days
        
        return self.update_user(user)
    
    def get_user_stats(self) -> dict:
        """Get user statistics"""
        try:
            # Get total count
            total_count = self.count()
            
            # Get active users count
            active_response = self.table.scan(
                FilterExpression='is_active = :is_active',
                ExpressionAttributeValues={':is_active': True},
                Select='COUNT'
            )
            active_count = active_response.get('Count', 0)
            
            # Get auto-booking users count
            auto_book_response = self.table.scan(
                FilterExpression='auto_book = :auto_book AND is_active = :is_active',
                ExpressionAttributeValues={
                    ':auto_book': True,
                    ':is_active': True
                },
                Select='COUNT'
            )
            auto_book_count = auto_book_response.get('Count', 0)
            
            stats = {
                'total_users': total_count,
                'active_users': active_count,
                'inactive_users': total_count - active_count,
                'auto_book_users': auto_book_count
            }
            
            logger.debug(f"User stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            raise