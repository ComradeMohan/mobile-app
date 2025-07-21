FROM python:3.10-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg2 \
    chromium-driver \
    chromium

# Set environment variables
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_BIN=/usr/bin/chromedriver

# Set working directory
WORKDIR /app

COPY . .

# Install Python packages
RUN pip install --upgrade pip && pip install -r requirements.txt

# Run the app
CMD ["python", "app.py"]
