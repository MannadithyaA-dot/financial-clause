# 1. Start with a compatible Python version
FROM python:3.9-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install system dependencies
RUN apt-get update && apt-get install -y build-essential libgl1

# 4. Create a non-root user and fix home directory permissions
RUN useradd appuser && chown -R appuser:appuser /home/appuser
WORKDIR /home/appuser/app

# 5. Upgrade Python's build tools
RUN pip install --upgrade pip setuptools wheel

# 6. Install a specific, stable version of NumPy FIRST
# This is the key step to ensure binary compatibility
RUN pip install --no-cache-dir numpy==1.23.5

# 7. Now copy requirements and install the rest of the packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 8. Copy your application code and set ownership
COPY --chown=appuser:appuser . .

# 9. Switch to the non-root user
USER appuser

# 10. Expose the port Streamlit runs on
EXPOSE 8501

# 11. The command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]