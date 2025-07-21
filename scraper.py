# scraper.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time

class ARMSClient:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def fetch_profile(self, username, password):
        try:
            self.driver.get("https://arms.sse.saveetha.com/Login.aspx")
            self.driver.find_element(By.ID, "txtusername").send_keys(username)
            self.driver.find_element(By.ID, "txtpassword").send_keys(password)
            self.driver.find_element(By.ID, "btnlogin").click()
            time.sleep(3)

            if "Login" in self.driver.title:
                return {"error": "Invalid credentials"}

            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/DataProfile.aspx")
            time.sleep(2)

            def safe(id_):
                try:
                    return self.driver.find_element(By.ID, id_).text.strip()
                except:
                    return "Not Found"

            return {
                "name": safe("dvname"),
                "regno": safe("dvregno"),
                "dob": safe("dvdob"),
                "program": safe("dvprogram"),
                "email": safe("dvemail"),
                "mobile": safe("dvmobile"),
            }

        except Exception as e:
            return {"error": str(e)}
        finally:
            self.driver.quit()
