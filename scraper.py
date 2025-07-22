# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, session
from scraper import ARMSClient
import secrets

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(16))

@app.route('/', methods=['GET', 'POST'])
def login():
    if 'profile' in session:
        return redirect(url_for('profile'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            return render_template('index.html', error='Username and password are required')
        
        client = ARMSClient()
        profile = client.fetch_profile(username, password)
        
        if "error" in profile:
            return render_template('index.html', error=profile['error'])
        
        session['profile'] = profile
        return redirect(url_for('profile'))
    
    return render_template('index.html')

@app.route('/profile')
def profile():
    if 'profile' not in session:
        return redirect(url_for('login'))
    return render_template('profile.html', profile=session['profile'])

@app.route('/logout')
def logout():
    session.pop('profile', None)
    return redirect(url_for('login'))

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

---

# scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ARMSClient:
    def __init__(self):
        chrome_options = Options()
        
        # Essential Chrome options for Docker/Render
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-logging")
        chrome_options.add_argument("--disable-login-animations")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-client-side-phishing-detection")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-hang-monitor")
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_argument("--disable-prompt-on-repost")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--disable-web-resources")
        chrome_options.add_argument("--metrics-recording-only")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--safebrowsing-disable-auto-update")
        chrome_options.add_argument("--enable-automation")
        chrome_options.add_argument("--password-store=basic")
        chrome_options.add_argument("--use-mock-keychain")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Memory optimization
        chrome_options.add_argument("--memory-pressure-off")
        chrome_options.add_argument("--max_old_space_size=4096")
        
        # Use system Chrome in Docker
        chrome_options.binary_location = "/usr/bin/google-chrome"
        
        try:
            # Use ChromeDriver from system PATH in Docker
            service = Service("/usr/bin/chromedriver")
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def fetch_profile(self, username, password):
        try:
            logger.info("Starting profile fetch process")
            
            # Navigate to login page
            self.driver.get("https://arms.sse.saveetha.com/Login.aspx")
            logger.info("Navigated to login page")
            
            # Wait for login elements to be present
            wait = WebDriverWait(self.driver, 10)
            
            username_field = wait.until(EC.presence_of_element_located((By.ID, "txtusername")))
            password_field = self.driver.find_element(By.ID, "txtpassword")
            login_button = self.driver.find_element(By.ID, "btnlogin")
            
            # Enter credentials
            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            
            # Click login
            login_button.click()
            logger.info("Login attempt made")
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if login was successful
            if "Login" in self.driver.title:
                logger.warning("Login failed - still on login page")
                return {"error": "Invalid credentials"}
            
            # Navigate to profile page
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/DataProfile.aspx")
            logger.info("Navigated to profile page")
            
            # Wait for profile data to load
            time.sleep(3)
            
            def safe_get_text(element_id):
                try:
                    element = wait.until(EC.presence_of_element_located((By.ID, element_id)))
                    return element.text.strip() or "Not Available"
                except (TimeoutException, NoSuchElementException):
                    logger.warning(f"Element {element_id} not found")
                    return "Not Found"
            
            # Extract profile data
            profile_data = {
                "name": safe_get_text("dvname"),
                "regno": safe_get_text("dvregno"),
                "dob": safe_get_text("dvdob"),
                "program": safe_get_text("dvprogram"),
                "email": safe_get_text("dvemail"),
                "mobile": safe_get_text("dvmobile"),
            }
            
            logger.info("Profile data extracted successfully")
            return profile_data
            
        except TimeoutException:
            logger.error("Timeout occurred while fetching profile")
            return {"error": "Request timeout - please try again"}
        except Exception as e:
            logger.error(f"Error during profile fetch: {e}")
            return {"error": f"An error occurred: {str(e)}"}
        finally:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
