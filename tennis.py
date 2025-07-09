from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import os
import logging
from datetime import datetime
import json
import time
from typing import Optional, Dict, Any
import sys

# Add src directory to path for importing our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from dao import EncryptedUserConfigDAO, BookingRequestDAO
    from models import BookingRequest as BookingRequestModel
    from api.models import BookingStatus
    DYNAMODB_AVAILABLE = True
except ImportError:
    DYNAMODB_AVAILABLE = False
    # Define a stub for BookingRequestModel when DynamoDB is not available
    class BookingRequestModel:
        pass
    logging.warning("DynamoDB modules not available, falling back to environment variables")

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logging
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tennis_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_config(user_id: Optional[str] = None, booking_request: Optional[BookingRequestModel] = None) -> Dict[str, Any]:
    """
    Load configuration from DynamoDB or environment variables (fallback)
    
    Args:
        user_id: User ID to load configuration for
        booking_request: Specific booking request to process
        
    Returns:
        Configuration dictionary
    """
    config = {}
    
    # Try to load from DynamoDB first
    if DYNAMODB_AVAILABLE and user_id:
        try:
            config = load_config_from_dynamodb(user_id, booking_request)
            logger.info(f"Configuration loaded from DynamoDB for user {user_id}")
        except Exception as e:
            logger.warning(f"Failed to load config from DynamoDB: {e}")
            config = {}
    
    # Fallback to environment variables if DynamoDB failed or not available
    if not config:
        config = load_config_from_env()
        logger.info("Configuration loaded from environment variables")
    
    # Validate required fields
    validate_config(config)
    
    # Log config (hide sensitive fields)
    safe_config = {k: v if k not in ['password', 'tennis_password'] else '***' for k, v in config.items()}
    logger.debug(f"Final config: {json.dumps(safe_config, indent=2)}")
    
    return config

def load_config_from_dynamodb(user_id: str, booking_request: Optional[BookingRequestModel] = None) -> Dict[str, Any]:
    """Load configuration from DynamoDB for a specific user"""
    user_dao = EncryptedUserConfigDAO()
    
    # Get user configuration
    user_config = user_dao.get_user(user_id)
    if not user_config:
        raise ValueError(f"User configuration not found for user_id: {user_id}")
    
    # Map court ID to tennis site area value
    court_id_mapping = {
        1: 5,  # Court 1 -> Area value 5 (Cancha de Tenis 1)
        2: 7   # Court 2 -> Area value 7 (Cancha de Tenis 2)
    }
    
    # Base configuration from user
    config = {
        'username': user_config.username,
        'password': user_config.password,  # Already decrypted by EncryptedUserConfigDAO
        'website_url': getattr(user_config, 'website_url', 'https://parquesdelsol.sasweb.net/'),
        'venue': getattr(user_config, 'venue', 'Parques del Sol'),
        'headless': getattr(user_config, 'headless', True),
        'area_value': None,  # Will be set based on court selection
        'date': None,        # Will be set based on booking request
        'time_slot': None    # Will be set based on booking request
    }
    
    # If we have a specific booking request, use its details
    if booking_request:
        # Map our court ID to tennis site area value
        if booking_request.court_id in court_id_mapping:
            config['area_value'] = court_id_mapping[booking_request.court_id]
        else:
            raise ValueError(f"Invalid court_id: {booking_request.court_id}")
        
        config['date'] = booking_request.booking_date
        config['time_slot'] = booking_request.time_slot
    else:
        # Use user preferences or defaults
        preferred_courts = getattr(user_config, 'preferred_courts', [1])
        config['area_value'] = court_id_mapping.get(preferred_courts[0], 5)
        config['date'] = getattr(user_config, 'default_date', '2025-04-01')
        config['time_slot'] = getattr(user_config, 'default_time', 'De 08:00 AM a 09:00 AM')
    
    return config

def load_config_from_env() -> Dict[str, Any]:
    """Load configuration from environment variables (fallback method)"""
    config = {
        'username': os.getenv('TENNIS_USERNAME'),
        'password': os.getenv('TENNIS_PASSWORD'),
        'website_url': os.getenv('TENNIS_WEBSITE_URL', 'https://parquesdelsol.sasweb.net/'),
        'venue': os.getenv('TENNIS_VENUE', 'Parques del Sol'),
        'area_value': int(os.getenv('TENNIS_AREA_VALUE', '5')),
        'date': os.getenv('TENNIS_DATE', '2025-04-01'),
        'time_slot': os.getenv('TENNIS_TIME_SLOT', 'De 08:00 AM a 09:00 AM'),
        'headless': os.getenv('TENNIS_HEADLESS', 'false').lower() == 'true'
    }
    
    return config

def validate_config(config: Dict[str, Any]) -> None:
    """Validate configuration has all required fields"""
    required_fields = ['username', 'password', 'website_url', 'area_value', 'date', 'time_slot']
    
    missing_fields = [field for field in required_fields if not config.get(field)]
    if missing_fields:
        raise ValueError(f"Missing required configuration fields: {', '.join(missing_fields)}")
    
    # Validate area_value is valid for tennis courts
    valid_area_values = [5, 7]  # Tennis courts only
    if config['area_value'] not in valid_area_values:
        raise ValueError(f"Invalid area_value: {config['area_value']}. Valid values: {valid_area_values}")
    
    logger.debug("Configuration validation successful")

def setup_driver(config: Dict[str, Any]) -> webdriver.Chrome:
    """Set up and configure the Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    if config.get('headless', False):
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        logger.debug("WebDriver initialized successfully")
        return driver
    except WebDriverException as e:
        logger.error(f"Failed to initialize WebDriver: {e}")
        raise

def make_reservation(user_id: Optional[str] = None, booking_request: Optional[BookingRequestModel] = None) -> bool:
    """
    Main function to handle the reservation process
    
    Args:
        user_id: User ID to load configuration for
        booking_request: Specific booking request to process
        
    Returns:
        True if reservation was successful, False otherwise
    """
    config = load_config(user_id, booking_request)
    driver = None
    
    try:
        logger.info(f"Starting reservation process for user_id: {user_id}")
        if booking_request:
            logger.info(f"Processing booking request: {booking_request.request_id}")
        
        driver = setup_driver(config)
        driver.get(config['website_url'])
        logger.debug(f"Navigated to {config['website_url']}")
        time.sleep(2)
        
        # Log in
        logger.info("Attempting to log in")
        username = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "number"))
        )
        logger.debug("Found username field")
        password = driver.find_element(By.ID, "pass")
        logger.debug("Found password field")
        
        username.send_keys(config['username'])
        time.sleep(1)
        password.send_keys(config['password'])
        time.sleep(1)
        
        login_button = driver.find_element(By.CLASS_NAME, "btn1")
        logger.debug("Found login button")
        login_button.click()
        time.sleep(2)
        logger.info("Login successful")
        
        # Navigate to Reservations
        logger.info("Navigating to Reservations page")
        reservations_link = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.LINK_TEXT, "Reservations"))
        )
        logger.debug("Found Reservations link")
        reservations_link.click()
        time.sleep(2)
        
        # Fill reservation form
        logger.info("Filling reservation form")
        form = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "reservation-form"))
        )
        logger.debug("Found reservation form")
        
        # Find and fill form fields
        venue_field = driver.find_element(By.ID, "venue")
        date_field = driver.find_element(By.ID, "date")
        time_field = driver.find_element(By.ID, "time")
        
        # Select area (court) - this is the key mapping
        area_dropdown = driver.find_element(By.ID, "area")
        area_dropdown.send_keys(str(config['area_value']))  # Use mapped area value
        time.sleep(1)
        
        logger.debug("Found and filled form fields")
        
        venue_field.send_keys(config['venue'])
        time.sleep(1)
        date_field.send_keys(config['date'])
        time.sleep(1)
        time_field.send_keys(config['time_slot'])
        time.sleep(1)
        
        # Take screenshot before confirmation
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        screenshot_path = f"screenshots/reservation_{timestamp}.png"
        os.makedirs("screenshots", exist_ok=True)
        driver.save_screenshot(screenshot_path)
        logger.info(f"Screenshot saved as {screenshot_path}")
        
        # Confirm reservation
        confirm_button = driver.find_element(By.ID, "confirm")
        logger.debug("Found confirm button")
        confirm_button.click()
        time.sleep(2)
        
        # Wait for confirmation message
        success_message = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "success-message"))
        )
        logger.debug("Found success message")
        
        logger.info("Reservation made successfully!")
        return True
        
    except TimeoutException as e:
        logger.error(f"Timeout while waiting for element: {e}")
        return False
    except WebDriverException as e:
        logger.error(f"WebDriver error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")

if __name__ == "__main__":
    success = make_reservation()
    if not success:
        logger.error("Reservation process failed")
        exit(1)
