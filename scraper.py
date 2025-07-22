from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
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
        profile_data = {}
        try:
            wait = WebDriverWait(self.driver, 15)
            logger.info("Logging in to ARMS portal...")

            self.driver.get("https://arms.sse.saveetha.com/Login.aspx")

            username_field = wait.until(EC.presence_of_element_located((By.ID, "txtusername")))
            password_field = self.driver.find_element(By.ID, "txtpassword")
            login_button = self.driver.find_element(By.ID, "btnlogin")

            username_field.clear()
            username_field.send_keys(username)
            password_field.clear()
            password_field.send_keys(password)
            login_button.click()
            time.sleep(2)

            if "Login" in self.driver.title:
                return {"error": "Invalid credentials"}

            logger.info("Fetching profile data...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/DataProfile.aspx")
            time.sleep(2)

            def safe(id_):
                try:
                    return wait.until(EC.presence_of_element_located((By.ID, id_))).text.strip() or "Not Available"
                except:
                    return "Not Found"

            profile_data.update({
                "name": safe("dvname"),
                "regno": safe("dvregno"),
                "dob": safe("dvdob"),
                "program": safe("dvprogram"),
                "email": safe("dvemail"),
                "mobile": safe("dvmobile"),
            })

            # Notifications
            logger.info("Fetching notifications...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/Landing.aspx")
            try:
                wait.until(EC.presence_of_element_located((By.ID, "ullpushnotification")))
                time.sleep(2)
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                ul = soup.find("ul", id="ullpushnotification")
                notifications = []
                if ul:
                    for li in ul.find_all("li"):
                        name = li.find("a", class_="name").get_text(strip=True) if li.find("a", class_="name") else "Unknown"
                        datetime = li.find("span", class_="datetime").get_text(strip=True) if li.find("span", class_="datetime") else "Unknown date"
                        body = li.find("span", class_="body").get_text(" ", strip=True) if li.find("span", class_="body") else "No message"
                        notifications.append({"by": name, "datetime": datetime, "message": body})
                else:
                    notifications.append({"message": "No notifications found"})
            except Exception as e:
                notifications = [{"error": f"Failed to fetch notifications: {str(e)}"}]

            profile_data["notifications"] = notifications

            # Results + CGPA
            logger.info("Fetching course results and CGPA...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/MyCourse.aspx")
            time.sleep(2)

            grade_points = {'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5}
            total_points = 0
            total_credits = 0
            courses = []

            try:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                table = soup.find("table", {"id": "tblGridViewComplete"})
                if table:
                    for row in table.find("tbody").find_all("tr"):
                        cols = row.find_all("td")
                        if len(cols) >= 6:
                            grade = cols[3].text.strip().upper()
                            status = cols[4].text.strip().upper()
                            if status == "FAIL":
                                continue
                            if grade in grade_points:
                                total_points += grade_points[grade]
                                total_credits += 1
                            courses.append({
                                "sno": cols[0].text.strip(),
                                "code": cols[1].text.strip(),
                                "name": cols[2].text.strip(),
                                "grade": grade,
                                "status": status,
                                "month_year": cols[5].text.strip()
                            })
            except Exception as e:
                courses.append({"error": f"Failed to scrape course data: {str(e)}"})

            profile_data["courses"] = courses
            profile_data["cgpa"] = round(total_points / total_credits, 2) if total_credits > 0 else "N/A"

            # Attendance
            logger.info("Fetching attendance data...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/AttendanceReport.aspx")
            try:
                wait.until(EC.presence_of_element_located((By.ID, "tblStudent")))
                time.sleep(2)
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                table = soup.find("table", id="tblStudent")
                rows = table.find("tbody").find_all("tr")

                attendance = []
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 9:
                        attendance.append({
                            "sno": cols[0].text.strip(),
                            "code": cols[1].text.strip(),
                            "name": cols[2].text.strip(),
                            "class_attended": cols[3].text.strip(),
                            "hours_attended": cols[4].text.strip(),
                            "total_class": cols[5].text.strip(),
                            "total_hours": cols[6].text.strip(),
                            "percentage": cols[7].text.strip().replace("label", "").strip(),
                            "view": cols[8].text.strip(),
                        })
                profile_data["attendance"] = attendance
            except Exception as e:
                profile_data["attendance"] = [{"error": f"Failed to fetch attendance: {str(e)}"}]

            return profile_data

        except Exception as e:
            logger.error(f"Error in fetch_profile: {e}")
            return {"error": "Something went wrong while fetching data."}

        finally:
            try:
                self.driver.quit()
                logger.info("WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
