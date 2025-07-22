from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os

class ARMSClient:
    def __init__(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920x1080")

        chrome_path = os.getenv("GOOGLE_CHROME_BIN", "/usr/bin/google-chrome")
        driver_path = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

        chrome_options.binary_location = chrome_path

        self.driver = webdriver.Chrome(
            service=Service(driver_path),
            options=chrome_options
        )

    def fetch_profile(self, username, password):
        try:
            wait = WebDriverWait(self.driver, 15)
            self.driver.get("https://arms.sse.saveetha.com/Login.aspx")

            self.driver.find_element(By.ID, "txtusername").send_keys(username)
            self.driver.find_element(By.ID, "txtpassword").send_keys(password)
            self.driver.find_element(By.ID, "btnlogin").click()
            time.sleep(2)

            if "Login" in self.driver.title:
                return {"error": "Invalid credentials"}

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
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                ul = soup.find("ul", id="ullpushnotification")
                notifications = []
                if ul:
                    for li in ul.find_all("li"):
                        name = li.find("a", class_="name")
                        datetime = li.find("span", class_="datetime")
                        body = li.find("span", class_="body")
                        notifications.append({
                            "by": name.get_text(strip=True) if name else "Unknown",
                            "datetime": datetime.get_text(strip=True) if datetime else "Unknown",
                            "message": body.get_text(" ", strip=True) if body else "No message"
                        })
                profile_data["notifications"] = notifications
            except Exception as e:
                profile_data["notifications"] = [{"error": str(e)}]

            # RESULTS + CGPA
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/MyCourse.aspx")
            time.sleep(2)
            courses = []
            total_points = 0
            total_credits = 0
            grade_points = {'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5}

            try:
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                table = soup.find("table", {"id": "tblGridViewComplete"})
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
                courses.append({"error": f"Failed to fetch course data: {str(e)}"})

            profile_data["courses"] = courses
            profile_data["cgpa"] = round(total_points / total_credits, 2) if total_credits else "N/A"

            # ATTENDANCE
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/AttendanceReport.aspx")
            try:
                wait.until(EC.presence_of_element_located((By.ID, "tblStudent")))
                time.sleep(2)
                soup = BeautifulSoup(self.driver.page_source, "html.parser")
                rows = soup.find("table", id="tblStudent").find("tbody").find_all("tr")

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
                profile_data["attendance"] = [{"error": str(e)}]

            return profile_data

        except Exception as e:
            return {"error": str(e)}

        finally:
            self.driver.quit()
