FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY courses/ ./courses/
COPY uploads/ ./uploads/

# Create necessary directories
RUN mkdir -p courses uploads

# Expose port
EXPOSE 8001

# Run Flask app
CMD ["python", "app.py"]

