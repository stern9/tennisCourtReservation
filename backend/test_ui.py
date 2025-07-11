from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select

def print_element_info(element, name):
    """Print information about a found element"""
    print(f"\nFound {name}:")
    print(f"Tag name: {element.tag_name}")
    print(f"ID: {element.get_attribute('id')}")
    print(f"Class: {element.get_attribute('class')}")
    print(f"Text: {element.text}")
    print(f"HTML: {element.get_attribute('outerHTML')[:200]}...")

def inspect_page(driver, url):
    """Inspect the page and print information about important elements"""
    print(f"\nInspecting page: {url}")
    driver.get(url)
    time.sleep(5)  # Increased wait time for page load
    
    # Try to switch to frame if it exists
    try:
        frames = driver.find_elements(By.TAG_NAME, "frame")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        
        if frames:
            print(f"Found {len(frames)} frames")
            driver.switch_to.frame(frames[0])
        elif iframes:
            print(f"Found {len(iframes)} iframes")
            driver.switch_to.frame(iframes[0])
    except Exception as e:
        print(f"No frames found or error switching: {e}")
    
    # Updated selectors based on your HTML
    elements = {
        "username field": (By.ID, "number"),
        "password field": (By.ID, "pass"),
        "login button": (By.CLASS_NAME, "btn1"),
        "reservations link": (By.LINK_TEXT, "Reservations"),
        "reservation form": (By.ID, "reservation-form"),
        "venue field": (By.ID, "venue"),
        "date field": (By.ID, "date"),
        "time field": (By.ID, "time"),
        "confirm button": (By.ID, "confirm"),
        "success message": (By.CLASS_NAME, "success-message")
    }
    
    for name, (by, value) in elements.items():
        try:
            # Add a small delay between checks
            time.sleep(1)
            element = WebDriverWait(driver, 5).until(
                EC.presence_of_element_located((by, value))
            )
            print_element_info(element, name)
        except Exception as e:
            print(f"\nCould not find {name}: {str(e)}")
            # Try to print page source for debugging
            print("\nCurrent page source:")
            print(driver.page_source[:500] + "...")
    
    # Take screenshot
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    screenshot_path = f"screenshots/inspection_{timestamp}.png"
    driver.save_screenshot(screenshot_path)
    print(f"\nScreenshot saved as {screenshot_path}")

def test_login_and_reservations(driver, url, username, password, area_value, date, time_slot):
    """Test login and navigate to reservations"""
    print(f"\nTesting login at: {url}")
    driver.get(url)
    time.sleep(3)  # Wait for page load
    
    try:
        # Login steps...
        print("Looking for username field...")
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[name='number'][id='number']"))
        )
        username_field.clear()
        username_field.send_keys(username)
        print("✓ Username entered")
        time.sleep(1)
        
        print("Looking for password field...")
        password_field = driver.find_element(By.CSS_SELECTOR, "input[name='pass'][id='pass']")
        password_field.clear()
        password_field.send_keys(password)
        print("✓ Password entered")
        time.sleep(1)
        
        print("Looking for submit button...")
        submit_button = driver.find_element(By.CSS_SELECTOR, "input[type='submit'][class='btn1'][value='Ingresar']")
        submit_button.click()
        print("✓ Submit button clicked")
        time.sleep(3)  # Wait for login to complete
        
        # Take screenshot after login
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        driver.save_screenshot(f"screenshots/after_login_{timestamp}.png")
        print(f"Current URL after login: {driver.current_url}")
        
        # Now find and click the Reservaciones link
        print("\nLooking for Reservaciones link...")
        try:
            # Wait for the link to be present
            reservations_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href='pre_reservations.php']"))
            )
            
            # Scroll the element into view
            driver.execute_script("arguments[0].scrollIntoView(true);", reservations_link)
            time.sleep(1)
            
            # Click using JavaScript
            driver.execute_script("arguments[0].click();", reservations_link)
            print("✓ Clicked Reservaciones link using JavaScript")
            time.sleep(3)
            
            # Wait for Shadowbox iframe to appear
            print("\nWaiting for Shadowbox iframe...")
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "sb-player"))
            )
            print("Found iframe, switching to it...")
            driver.switch_to.frame(iframe)
            print("✓ Switched to iframe")
            
            # Wait for the select element to be present
            print("\nLooking for area select...")
            select_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "area"))
            )
            print("Found select element")
            
            # Print all options
            select = Select(select_element)
            print("\nAvailable options:")
            for option in select.options:
                print(f"- {option.text} (value: {option.get_attribute('value')})")
            
            # Select the tennis court by value
            select.select_by_value(area_value)  # Use the area_value parameter
            print(f"✓ Selected area with value: {area_value}")
            time.sleep(1)  # Wait for selection to register
            
            # Click the "Aceptar y Continuar" button
            print("\nLooking for Aceptar y Continuar button...")
            continue_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][class='btn2'][value='Aceptar y Continuar']"))
            )
            print("Found continue button, clicking...")
            driver.execute_script("arguments[0].click();", continue_button)
            print("✓ Clicked Aceptar y Continuar button")
            time.sleep(2)
            
            # After clicking continue button and waiting
            time.sleep(2)
            
            # Click on the date using the date parameter
            print(f"\nLooking for date: {date}")
            try:
                # Find the date cell by its onclick attribute that contains the exact date and area
                date_cell = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, f"td[onclick*=\"f_change_reservation_day('{date}','{area_value}')\"]"))
                )
                print("Found date cell, clicking...")
                driver.execute_script("arguments[0].click();", date_cell)
                print(f"✓ Clicked date {date}")
            except Exception as e:
                print(f"Error clicking date: {str(e)}")
                # Try alternative method using JavaScript directly
                try:
                    driver.execute_script(f"f_change_reservation_day('{date}','{area_value}')")
                    print("✓ Selected date using JavaScript function")
                except Exception as e2:
                    print(f"JavaScript selection failed: {str(e2)}")
                    raise
            
            time.sleep(3)  # Increased wait time
            
            # Click the "Solicitar Reserva" link using the exact selector from the recording
            print("\nLooking for Solicitar Reserva link...")
            try:
                # Use the exact selector from the recording
                reservation_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "table a"))
                )
                print("Found reservation link, clicking...")
                driver.execute_script("arguments[0].click();", reservation_link)
                print("✓ Clicked Solicitar Reserva link")
                time.sleep(2)  # Wait for the form to load
                
                # Take screenshot after clicking Solicitar Reserva
                driver.save_screenshot(f"screenshots/after_solicitar_reserva_{timestamp}.png")
                print(f"Current URL after clicking Solicitar Reserva: {driver.current_url}")
                
                # Now look for the time slot dropdown
                print("\nLooking for time slot dropdown...")
                time_select = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "schedule"))
                )
                print("Found time select element")
                
                # Print all available options
                time_select_obj = Select(time_select)
                print("\nAvailable time slots:")
                for option in time_select_obj.options:
                    print(f"- {option.text} (value: {option.get_attribute('value')})")
                
                # Select the time slot using the provided time_slot parameter
                time_select_obj.select_by_visible_text(time_slot)
                print(f"✓ Selected time slot: {time_slot}")
                time.sleep(2)  # Wait for selection to register
                
                # Take screenshot after selecting time
                driver.save_screenshot(f"screenshots/after_time_selection_{timestamp}.png")
                print(f"Current URL after selecting time: {driver.current_url}")
                
                # Finally, click the "Guardar" button
                print("\nLooking for Guardar button...")
                try:
                    # Wait for the save button to be clickable
                    save_button = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit'][class='btn2'][id='save_btn'][value='Guardar']"))
                    )
                    print("Found save button, clicking...")
                    driver.execute_script("arguments[0].click();", save_button)
                    print("✓ Clicked Guardar button")
                    time.sleep(2)
                    
                    # Take screenshot after clicking save
                    driver.save_screenshot(f"screenshots/after_save_{timestamp}.png")
                    print(f"Current URL after clicking save: {driver.current_url}")
                    
                except Exception as e:
                    print(f"Error clicking save button: {str(e)}")
                    # Try alternative method using JavaScript
                    try:
                        driver.execute_script("document.getElementById('save_btn').click();")
                        print("✓ Clicked save button using JavaScript")
                    except Exception as e2:
                        print(f"JavaScript click failed: {str(e2)}")
                        raise
                
            except Exception as e:
                print(f"Error finding Solicitar Reserva link: {str(e)}")
                # Take a screenshot to see what's on the page
                driver.save_screenshot(f"screenshots/error_finding_link_{time.strftime('%Y%m%d_%H%M%S')}.png")
                print("Took screenshot of error state")
                raise
            
        except Exception as e:
            print(f"Error during process: {str(e)}")
            driver.save_screenshot(f"screenshots/error_{time.strftime('%Y%m%d_%H%M%S')}.png")
            raise
            
    except Exception as e:
        print(f"Error during process: {str(e)}")
        driver.save_screenshot(f"screenshots/error_{time.strftime('%Y%m%d_%H%M%S')}.png")
        raise

def main():
    # Create screenshots directory if it doesn't exist
    os.makedirs("screenshots", exist_ok=True)
    
    # Set up driver with additional options
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-notifications")
    
    # Use Service class with ChromeDriverManager
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    try:
        # Load config
        env_vars = {}
        with open(".env", "r", encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    try:
                        if '=' in line:  # Only process lines that contain '='
                            key, value = line.split('=', 1)
                            env_vars[key.strip()] = value.strip()
                    except ValueError as e:
                        print(f"Warning: Skipping invalid line: {line}")
        
        # Get all required variables from environment
        website_url = env_vars.get("TENNIS_WEBSITE_URL")
        username = env_vars.get("TENNIS_USERNAME")
        password = env_vars.get("TENNIS_PASSWORD")
        area_value = env_vars.get("TENNIS_AREA_VALUE")
        date = env_vars.get("TENNIS_DATE")
        time_slot = env_vars.get("TENNIS_TIME_SLOT")
        
        # Check if all required variables are present
        required_vars = {
            "TENNIS_WEBSITE_URL": website_url,
            "TENNIS_USERNAME": username,
            "TENNIS_PASSWORD": password,
            "TENNIS_AREA_VALUE": area_value,
            "TENNIS_DATE": date,
            "TENNIS_TIME_SLOT": time_slot
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        # Test login and reservations with the configured values
        test_login_and_reservations(
            driver, 
            website_url, 
            username, 
            password,
            area_value=area_value,
            date=date,
            time_slot=time_slot
        )
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
    finally:
        time.sleep(3)  # Give time to see the final state
        driver.quit()

if __name__ == "__main__":
    main() 