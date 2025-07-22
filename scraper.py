from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ARMSClient:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")

        try:
            self.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )
            logger.info("✅ WebDriver initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize WebDriver: {e}")
            raise

    def fetch_profile(self, username, password):
        try:
            wait = WebDriverWait(self.driver, 15)

            # LOGIN
            self.driver.get("https://arms.sse.saveetha.com/Login.aspx")
            self.driver.find_element(By.ID, "txtusername").send_keys(username)
            self.driver.find_element(By.ID, "txtpassword").send_keys(password)
            self.driver.find_element(By.ID, "btnlogin").click()
            time.sleep(2)

            if "Login" in self.driver.title:
                return {"error": "Invalid credentials"}

            # PROFILE
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

            # NOTIFICATIONS (Home Page)
            logger.info("🔔 Fetching notifications...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/Home.aspx")
            time.sleep(2)
            notifications = []

            try:
                wait.until(EC.presence_of_element_located((By.ID, "ullpushnotification")))
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                ul = soup.find("ul", id="ullpushnotification")
                if ul:
                    items = ul.find_all("li")
                    for li in items:
                        name = li.find("a", class_="name")
                        date = li.find("span", class_="datetime")
                        body = li.find("span", class_="body")

                        notifications.append({
                            "by": name.get_text(strip=True) if name else "Unknown",
                            "datetime": date.get_text(strip=True) if date else "Unknown",
                            "message": body.get_text(strip=True) if body else "No message"
                        })
                else:
                    notifications.append({"message": "No notifications found"})
            except Exception as e:
                notifications = [{"error": f"Notification fetch failed: {str(e)}"}]

            profile_data["notifications"] = notifications

            # COURSES + CGPA
            logger.info("🎓 Fetching course results...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/MyCourse.aspx")
            time.sleep(2)

            courses = []
            total_points = 0
            total_credits = 0
            grade_points = {'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5}

            try:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                table = soup.find("table", {"id": "tblGridViewComplete"})
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
            except Exception as e:
                courses.append({"error": f"Course scrape failed: {str(e)}"})

            profile_data["courses"] = courses
            profile_data["cgpa"] = round(total_points / total_credits, 2) if total_credits > 0 else "N/A"

            # ATTENDANCE
            logger.info("📊 Fetching attendance...")
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/AttendanceReport.aspx")
            attendance = []

            try:
                wait.until(EC.presence_of_element_located((By.ID, "gvAttendanceReport")))
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
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
            logger.error(f"❌ Error during fetch: {e}")
            return {"error": str(e)}

        finally:
            try:
                self.driver.quit()
                logger.info("🛑 WebDriver closed.")
            except Exception as e:
                logger.warning(f"⚠️ Driver close failed: {e}")
