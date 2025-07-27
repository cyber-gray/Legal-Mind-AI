# Legal Mind Agent Pro - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy main application
COPY main.py .

# Expose port
EXPOSE 80

# Run the Legal Mind Agent Pro
CMD ["python", "main.py"]
