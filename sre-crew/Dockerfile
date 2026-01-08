FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ONLY source code (No config!)
COPY src/ ./src/

# Add /app to the Python path
ENV PYTHONPATH=/app

# Default command
CMD ["python", "src/main.py"]