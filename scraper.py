from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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
            wait = WebDriverWait(self.driver, 20)

            # LOGIN
            self.driver.get("https://arms.sse.saveetha.com/Login.aspx")
            self.driver.find_element(By.ID, "txtusername").send_keys(username)
            self.driver.find_element(By.ID, "txtpassword").send_keys(password)
            self.driver.find_element(By.ID, "btnlogin").click()

            # Wait for login success (redirect)
            wait.until(lambda d: "Login" not in d.title)
            profile_data = {}

            # PROFILE
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/DataProfile.aspx")
            wait.until(EC.presence_of_element_located((By.ID, "dvname")))

            def safe(id_):
                try:
                    return self.driver.find_element(By.ID, id_).text.strip()
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

            # NOTIFICATIONS
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/Landing.aspx")
            notifications = []
            try:
                wait.until(EC.presence_of_element_located((By.ID, "ullpushnotification")))
                ul = self.driver.find_element(By.ID, "ullpushnotification")
                li_items = ul.find_elements(By.TAG_NAME, "li")

                for li in li_items:
                    try:
                        name = li.find_element(By.CLASS_NAME, "name").text.strip()
                        datetime = li.find_element(By.CLASS_NAME, "datetime").text.strip()
                        body = li.find_element(By.CLASS_NAME, "body").text.strip()
                        notifications.append({
                            "by": name,
                            "datetime": datetime,
                            "message": body
                        })
                    except:
                        continue

                if not notifications:
                    notifications.append({"message": "No notifications found"})

            except Exception as e:
                notifications = [{"error": f"Failed to fetch notifications: {str(e)}"}]

            profile_data["notifications"] = notifications

            # RESULTS + CGPA
            self.driver.get("https://arms.sse.saveetha.com/StudentPortal/MyCourse.aspx")
            wait.until(EC.presence_of_element_located((By.ID, "tblGridViewComplete")))

            courses = []
            total_points = 0
            total_credits = 0
            grade_points = {'S': 10, 'A': 9, 'B': 8, 'C': 7, 'D': 6, 'E': 5}

            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "#tblGridViewComplete tbody tr")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
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
            attendance = []
            try:
                wait.until(EC.presence_of_element_located((By.ID, "tblStudent")))
                rows = self.driver.find_elements(By.CSS_SELECTOR, "#tblStudent tbody tr")
                for row in rows:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) >= 9:
                        attendance.append({
                            "sno": cols[0].text.strip(),
                            "code": cols[1].text.strip(),
                            "name": cols[2].text.strip(),
                            "class_attended": cols[3].text.strip(),
                            "hours_attended": cols[4].text.strip(),
                            "total_class": cols[5].text.strip(),
                            "total_hours": cols[6].text.strip(),
                            "percentage": cols[7].text.strip(),
                            "view": cols[8].text.strip(),
                        })
            except Exception as e:
                attendance = [{"error": f"Failed to fetch attendance: {str(e)}"}]

            profile_data["attendance"] = attendance

            return profile_data

        except Exception as e:
            return {"error": str(e)}

        finally:
            self.driver.quit()
