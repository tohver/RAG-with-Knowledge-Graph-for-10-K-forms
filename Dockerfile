FROM python:3.11-slim

# Install system dependencies for common python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Keep the container running for Cursor to attach to
CMD ["tail", "-f", "/dev/null"]