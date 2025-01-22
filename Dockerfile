FROM python:3.12.1-slim

WORKDIR /app/

# Add requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN python3 -m pip install --no-cache-dir --upgrade pip && \
    python3 -m pip install --no-cache-dir gunicorn && \
    python3 -m pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create non-root user for security
RUN useradd -m django && \
    chown -R django:django /app
USER django
