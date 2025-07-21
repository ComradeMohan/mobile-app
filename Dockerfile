FROM python:3.10

# Install Chromium and ChromeDriver dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg2 \
    chromium chromium-driver \
    build-essential libnss3 libxss1 libappindicator1 libindicator7 \
    libasound2 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 fonts-liberation \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Environment variables for Chrome + Chromedriver
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Start the app
CMD ["python", "app.py"]
