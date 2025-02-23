# Use Python image
FROM python:3.11-bullseye

# Install build dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    liblapack-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]