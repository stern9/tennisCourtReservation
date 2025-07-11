# ABOUTME: JWT authentication service with tennis site credential validation
# ABOUTME: Provides user authentication, token generation, and credential verification

from datetime import datetime, timedelta
from typing import Optional
import logging
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import time

from .config import get_settings
from .models import TokenData, UserProfile
from ..dao import EncryptedUserConfigDAO
from ..models import EncryptedUserConfig

logger = logging.getLogger(__name__)

# Security setup
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    """Authentication service for JWT and tennis site validation"""
    
    def __init__(self):
        self.settings = get_settings()
        self.user_dao = EncryptedUserConfigDAO()
    
    def verify_tennis_site_credentials(self, username: str, password: str) -> bool:
        """Verify credentials against the tennis site"""
        try:
            # Set up Chrome options for headless operation
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            # Initialize WebDriver
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            
            try:
                # Navigate to tennis site
                driver.get(self.settings.tennis_site_url)
                
                # Wait for login form elements
                wait = WebDriverWait(driver, self.settings.tennis_site_timeout)
                
                # Find username and password fields (adjust selectors based on actual site)
                username_field = wait.until(
                    EC.presence_of_element_located((By.NAME, "username"))
                )
                password_field = driver.find_element(By.NAME, "password")
                login_button = driver.find_element(By.XPATH, "//input[@type='submit']")
                
                # Enter credentials
                username_field.clear()
                username_field.send_keys(username)
                password_field.clear()
                password_field.send_keys(password)
                
                # Submit login
                login_button.click()
                
                # Wait and check for successful login
                # This depends on the tennis site's behavior after successful login
                time.sleep(3)
                
                # Check if we're redirected to a dashboard or success page
                current_url = driver.current_url
                page_source = driver.page_source.lower()
                
                # Look for indicators of successful login
                success_indicators = [
                    "dashboard", "booking", "reservation", "courts", "welcome"
                ]
                
                # Check for error indicators
                error_indicators = [
                    "invalid", "error", "incorrect", "failed", "login"
                ]
                
                # Simple heuristic: if we see success indicators and not error indicators
                has_success = any(indicator in current_url.lower() or indicator in page_source for indicator in success_indicators)
                has_error = any(indicator in page_source for indicator in error_indicators)
                
                # If URL changed from login page and we see success indicators, assume success
                is_login_successful = has_success and not has_error
                
                logger.info(f"Tennis site login attempt for {username}: {'successful' if is_login_successful else 'failed'}")
                return is_login_successful
                
            finally:
                driver.quit()
                
        except TimeoutException:
            logger.error(f"Tennis site login timeout for user: {username}")
            return False
        except WebDriverException as e:
            logger.error(f"WebDriver error during tennis site login: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during tennis site login: {e}")
            return False
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=self.settings.jwt_expiration_hours)
        
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify JWT token and extract user data"""
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm]
            )
            
            username: str = payload.get("sub")
            user_id: str = payload.get("user_id")
            
            if username is None or user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            token_data = TokenData(username=username, user_id=user_id)
            return token_data
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def authenticate_user(self, username: str, password: str) -> Optional[EncryptedUserConfig]:
        """Authenticate user with tennis site and database"""
        try:
            # First, verify credentials against tennis site
            if not self.verify_tennis_site_credentials(username, password):
                logger.warning(f"Tennis site authentication failed for user: {username}")
                return None
            
            # Check if user exists in our database
            user = self.user_dao.get_user_by_username(username)
            
            if user is None:
                # User doesn't exist in our database, create new user
                logger.info(f"Creating new user in database: {username}")
                
                # Create new user with tennis site credentials
                new_user = EncryptedUserConfig(
                    user_id=f"user_{username}_{int(datetime.now().timestamp())}",
                    username=username,
                    password=password,  # This will be encrypted by EncryptedUserConfig
                    email=f"{username}@tennis.local",  # Placeholder email
                    first_name=username.title(),
                    last_name="User",
                    is_active=True,
                    preferred_courts=[1, 2],
                    preferred_times=["De 08:00 AM a 09:00 AM"],
                    max_bookings_per_day=1,
                    auto_booking_enabled=False
                )
                
                user = self.user_dao.create_user(new_user)
                
            else:
                # User exists, update password if needed (password might have changed on tennis site)
                if user.password != password:
                    logger.info(f"Updating password for existing user: {username}")
                    user.password = password
                    user = self.user_dao.update_user(user)
                
                # Check if user is active
                if not user.is_active:
                    logger.warning(f"Inactive user attempted login: {username}")
                    return None
            
            return user
            
        except Exception as e:
            logger.error(f"Authentication error for user {username}: {e}")
            return None
    
    def get_current_user_profile(self, user_id: str) -> UserProfile:
        """Get current user profile"""
        user = self.user_dao.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserProfile(
            user_id=user.user_id,
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            is_active=user.is_active,
            preferred_courts=user.preferred_courts,
            preferred_times=user.preferred_times,
            max_bookings_per_day=user.max_bookings_per_day,
            auto_booking_enabled=user.auto_booking_enabled,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

# Global auth service instance
auth_service = AuthService()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Dependency to get current user from JWT token"""
    token = credentials.credentials
    return auth_service.verify_token(token)

def get_current_user_profile(current_user: TokenData = Depends(get_current_user)) -> UserProfile:
    """Dependency to get current user profile"""
    return auth_service.get_current_user_profile(current_user.user_id)