# Use official Python image
FROM python:3.11-slim


# Set working directory
WORKDIR /app

# Copy all project files
COPY . .

# Install system packages
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


# Install python dependencies
RUN pip install --upgrade pip 
RUN pip install -r requirements.txt


# Default command (change if we are using entrypoint script)
CMD ["python", "-u", "main.py"]


