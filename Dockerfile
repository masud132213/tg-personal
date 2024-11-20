FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p assets temp

# Copy the rest of the application
COPY . .

# Make sure the directories exist and are writable
RUN chmod -R 777 assets temp

# Expose port for health checks
EXPOSE 8080

# Run the bot
CMD ["python", "bot.py"] 