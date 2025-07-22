from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time

class ARMSClient:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920x1080")

        self.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )

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

            # NOTIFICATIONS
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/Landing.aspx")
            try:
                wait.until(EC.presence_of_element_located((By.ID, "ullpushnotification")))
                time.sleep(2)

                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                ul = soup.find("ul", id="ullpushnotification")

                notifications = []
                if ul:
                    items = ul.find_all("li")
                    for li in items:
                        name_tag = li.find("a", class_="name")
                        datetime_tag = li.find("span", class_="datetime")
                        body_tag = li.find("span", class_="body")

                        name = name_tag.get_text(strip=True) if name_tag else "Unknown"
                        datetime = datetime_tag.get_text(strip=True) if datetime_tag else "Unknown date"
                        body = body_tag.get_text(" ", strip=True) if body_tag else "No message"

                        notifications.append({
                            "by": name,
                            "datetime": datetime,
                            "message": body
                        })
                else:
                    notifications.append({"message": "No notifications found"})
            except Exception as e:
                notifications = [{"error": f"Failed to fetch notifications: {str(e)}"}]

            profile_data["notifications"] = notifications

            # RESULTS + CGPA
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/MyCourse.aspx")
            time.sleep(2)

            courses = []
            total_points = 0
            total_credits = 0
            grade_points = {'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5}

            try:
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
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
                courses.append({"error": f"Failed to scrape course data: {str(e)}"})

            profile_data["courses"] = courses
            profile_data["cgpa"] = round(total_points / total_credits, 2) if total_credits > 0 else "N/A"

            # ATTENDANCE
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/AttendanceReport.aspx")
            try:
                wait.until(EC.presence_of_element_located((By.ID, "tblStudent")))
                time.sleep(2)
                html = self.driver.page_source
                soup = BeautifulSoup(html, "html.parser")
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
            return {"error": str(e)}

        finally:
            self.driver.quit()
