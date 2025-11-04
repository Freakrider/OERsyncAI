FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy shared utilities first (from project root context)
COPY shared /app/shared

# Copy requirements
COPY services/ilias-analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service files
COPY services/ilias-analyzer /app

# Expose port
EXPOSE 8002

# Start service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002", "--reload"]

