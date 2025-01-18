# Use the official Python image with version 3.9 or any compatible version
FROM python:3.9-slim

# Set environment variables to prevent Python from writing .pyc files and to enable unbuffered output
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script and related files into the working directory
COPY . .

# Expose a volume for backups (optional: allows mounting volumes to access backups easily)
# VOLUME /backups

# Set the entrypoint command to run the Python script
CMD ["python", "backup-script.py"]