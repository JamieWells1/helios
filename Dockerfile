# Use Python 3.13 slim base image for minimal size
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY main.py .

# Copy the test scripts
COPY run_tests.sh .
COPY run_trading_tests.sh .

# Ensure the test scripts are executable
RUN chmod +x run_tests.sh run_trading_tests.sh

# Create directories for logs and data
RUN mkdir -p logs data

# Create non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Ensure the tests directory is copied into the container
COPY tests/ ./tests/

# Ensure the tests directory is writable by the container user
USER root
RUN chown -R botuser:botuser ./tests && touch ./tests/__init__.py

# Switch back to the non-root user
USER botuser

# Update the default CMD to gracefully exit after tests
CMD ["bash", "-c", "echo 'Running tests...' && python3 -m unittest discover -s ./tests -p '*.py' && echo 'Tests completed. Exiting gracefully.'"]
