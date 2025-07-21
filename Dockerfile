FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg2 \
    chromium chromium-driver \
    build-essential libnss3 libxss1 libappindicator1 libindicator7 \
    libasound2 libatk-bridge2.0-0 libgtk-3-0 libx11-xcb1 fonts-liberation \
    --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Set environment variables for Chromium
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Set working directory
WORKDIR /app

# Copy source code
COPY . .

# Install Python dependencies
RUN pip install --upgrade pip && pip install -r requirements.txt

# Run the app
CMD ["python", "app.py"]
