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
            logger.info("✅ Chrome WebDriver initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize WebDriver: {e}")
            raise

    def fetch_profile(self, username, password):
        try:
            logger.info("🔐 Logging in...")

            self.driver.get("https://arms.sse.saveetha.com/Login.aspx")
            wait = WebDriverWait(self.driver, 10)

            wait.until(EC.presence_of_element_located((By.ID, "txtusername"))).send_keys(username)
            self.driver.find_element(By.ID, "txtpassword").send_keys(password)
            self.driver.find_element(By.ID, "btnlogin").click()
            time.sleep(3)

            if "Login" in self.driver.title:
                return {"error": "Invalid credentials"}

            profile_data = {}
            wait = WebDriverWait(self.driver, 10)

            # Profile Info
            logger.info("📄 Fetching profile info...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/DataProfile.aspx")
            time.sleep(2)

            def safe(id_):
                try:
                    return self.driver.find_element(By.ID, id_).text.strip()
                except:
                    return "Not Found"

            profile_data = {
                "name": safe("dvname"),
                "regno": safe("dvregno"),
                "dob": safe("dvdob"),
                "program": safe("dvprogram"),
                "email": safe("dvemail"),
                "mobile": safe("dvmobile"),
            }

            # Notifications
            logger.info("🔔 Fetching notifications...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/Home.aspx")
            try:
                wait.until(EC.presence_of_element_located((By.ID, "ullpushnotification")))
            except:
                pass

            notifications = []
            try:
                ul = self.driver.find_element(By.ID, "ullpushnotification")
                items = ul.find_elements(By.TAG_NAME, "li")
                for item in items:
                    try:
                        notifications.append({
                            "by": item.find_element(By.CLASS_NAME, "name").text.strip(),
                            "datetime": item.find_element(By.CLASS_NAME, "datetime").text.strip(),
                            "message": item.find_element(By.CLASS_NAME, "body").text.strip()
                        })
                    except Exception as e:
                        notifications.append({"message": f"Failed to parse: {str(e)}"})
            except:
                notifications.append({"message": "No notifications found"})

            profile_data["notifications"] = notifications

            # My Courses + CGPA
            logger.info("🎓 Fetching course results and calculating CGPA...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/MyCourse.aspx")
            time.sleep(2)

            html = self.driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            table = soup.find("table", {"id": "tblGridViewComplete"})

            courses = []
            total_points = 0
            total_credits = 0
            grade_points = {'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5}

            if table:
                rows = table.find("tbody").find_all("tr")
                for row in rows:
                    cols = row.find_all("td")
                    if len(cols) >= 6:
                        grade = cols[3].text.strip().upper()
                        status = cols[4].text.strip().upper()

                        if status == "FAIL":
                            continue

                        course = {
                            "sno": cols[0].text.strip(),
                            "code": cols[1].text.strip(),
                            "name": cols[2].text.strip(),
                            "grade": grade,
                            "status": status,
                            "month_year": cols[5].text.strip()
                        }

                        if grade in grade_points:
                            total_points += grade_points[grade]
                            total_credits += 1

                        courses.append(course)

            profile_data["courses"] = courses
            profile_data["cgpa"] = round(total_points / total_credits, 2) if total_credits else "N/A"

            # Attendance
            logger.info("📊 Fetching attendance...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/AttendanceReport.aspx")
            time.sleep(3)
            attendance = []

            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: len(d.find_elements(By.XPATH, "//table[@id='gvAttendanceReport']//tr")) > 1
                )
                page = self.driver.page_source
                soup = BeautifulSoup(page, 'html.parser')
                table = soup.find("table", {"id": "gvAttendanceReport"})
                if table:
                    rows = table.find_all("tr")[1:]
                    for row in rows:
                        cols = row.find_all("td")
                        if len(cols) >= 7:
                            attendance.append({
                                "code": cols[0].text.strip(),
                                "name": cols[1].text.strip(),
                                "type": cols[2].text.strip(),
                                "total_classes": cols[3].text.strip(),
                                "attended": cols[4].text.strip(),
                                "percentage": cols[5].text.strip(),
                                "status": cols[6].text.strip(),
                            })
            except Exception as e:
                attendance.append({"error": f"Attendance fetch failed: {str(e)}"})

            profile_data["attendance"] = attendance

            logger.info("✅ Profile fetch complete.")
            return profile_data

        except Exception as e:
            logger.error(f"❌ Error during profile fetch: {e}")
            return {"error": str(e)}

        finally:
            try:
                self.driver.quit()
                logger.info("🛑 WebDriver closed.")
            except Exception as e:
                logger.warning(f"⚠️ Error closing WebDriver: {e}")
