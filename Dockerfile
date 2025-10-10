# 1. Start with an official Python base image.
# Using a specific version is recommended for consistency.
FROM python:3.10-slim

# 2. Install system-level dependencies.
# 'build-essential' includes the C compiler (gcc) and other tools
# needed to build packages like 'blis'.
RUN apt-get update && apt-get install -y build-essential

# 3. Set the working directory inside the container.
WORKDIR /app

# 4. Copy your requirements file and install Python packages.
# This is done in a separate step to leverage Docker's caching.
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --upgrade setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your application code into the container.
COPY . .

# 6. Specify the command to run your application.
# Replace 'your_app_file.py' with the entry point of your app.
CMD ["python", "app.py"]