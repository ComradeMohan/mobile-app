from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ARMSClient:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.binary_location = "/usr/bin/chromium"

        try:
            service = Service("/usr/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def fetch_profile(self, username, password):
        try:
            logger.info("Fetching profile...")

            self.driver.get("https://arms.sse.saveetha.com/Login.aspx")
            wait = WebDriverWait(self.driver, 10)

            username_field = wait.until(EC.presence_of_element_located((By.ID, "txtusername")))
            password_field = self.driver.find_element(By.ID, "txtpassword")
            login_button = self.driver.find_element(By.ID, "btnlogin")

            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            login_button.click()

            time.sleep(3)

            if "Login" in self.driver.title:
                return {"error": "Invalid credentials"}

            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/DataProfile.aspx")
            time.sleep(3)

            def safe_get_text(element_id):
                try:
                    element = wait.until(EC.presence_of_element_located((By.ID, element_id)))
                    return element.text.strip() or "Not Available"
                except (TimeoutException, NoSuchElementException):
                    return "Not Found"

            return {
                "name": safe_get_text("dvname"),
                "regno": safe_get_text("dvregno"),
                "dob": safe_get_text("dvdob"),
                "program": safe_get_text("dvprogram"),
                "email": safe_get_text("dvemail"),
                "mobile": safe_get_text("dvmobile"),
            }

        except Exception as e:
            logger.error(f"Error during profile fetch: {e}")
            return {"error": "Something went wrong while fetching profile."}
        finally:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
