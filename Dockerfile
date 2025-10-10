# 1. Start with an official Python base image
FROM python:3.9-slim

# 2. Set environment variables to prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install system-level dependencies (the "toolbox") as root
RUN apt-get update && apt-get install -y build-essential

# 4. Create a non-root user and a directory for the app
RUN useradd appuser
WORKDIR /home/appuser/app

# 5. Upgrade Python's build tools as root
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools wheel

# 6. Copy the requirements file and install packages (still as root for system-wide access if needed)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy the rest of your application code and give ownership to the new user
COPY --chown=appuser:appuser . .

# 8. Switch to the non-root user
USER appuser

# 9. IMPORTANT: Change 'main.py' to the name of your app's starting file
CMD ["python", "main.py"]