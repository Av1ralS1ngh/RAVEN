FROM mcr.microsoft.com/playwright/python:v1.50.0-jammy

# OLD VERSION (KEEPING FOR REFERENCE):
# FROM python:3.11-slim
# RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*
# RUN playwright install --with-deps chromium

WORKDIR /app

# Ensure curl is installed for Render healthchecks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

EXPOSE 8000

# Start the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
