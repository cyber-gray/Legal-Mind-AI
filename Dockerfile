# Legal Mind Agent - Production Container for Azure App Service
FROM python:3.11-slim

# Set environment variables for Azure App Service
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=80

# Install system dependencies for ML/AI packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY src/requirements.txt requirements.txt

# Install Python dependencies with specific versions
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code and security framework
COPY src/ ./src/
COPY legal_mind/ ./legal_mind/

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Health check with startup grace period for ML libraries
HEALTHCHECK --interval=30s --timeout=15s --start-period=120s --retries=5 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Expose port (Azure App Service uses PORT environment variable)
EXPOSE ${PORT}

# Use the updated app.py for production server with security framework
CMD ["python", "src/app.py"]
