FROM python:3.10-slim

# Install Chromium and dependencies
RUN apt-get update && apt-get install -y \
    wget curl unzip gnupg2 \
    chromium chromium-driver \
    libnss3 libxss1 libappindicator1 \
    libasound2 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 fonts-liberation \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy app files
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Start the Flask app
CMD ["python", "app.py"]
