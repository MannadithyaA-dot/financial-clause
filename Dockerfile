# 1. Start with a compatible Python version
FROM python:3.9-slim

# 2. Set environment variables for best practices in containers
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install required system dependencies
RUN apt-get update && apt-get install -y build-essential libgl1

# 4. Create a non-root user AND its home directory correctly
RUN useradd -m appuser
WORKDIR /home/appuser/app

# 5. Upgrade Python's build tools first
RUN pip install --upgrade pip

# 6. Install PyTorch and torchvision FIRST from the correct index.
RUN pip install --no-cache-dir torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# 7. Copy the final requirements file
COPY requirements.txt .

# 8. Install everything from the pinned requirements file.
RUN pip install --no-cache-dir -r requirements.txt

# 9. FINAL STEP: Pre-download and cache the EasyOCR models during the build.
#    This makes the container self-contained and prevents runtime errors.
RUN python -c "import easyocr; reader = easyocr.Reader(['en'])"

# 10. Copy your application code and set ownership for the non-root user
COPY --chown=appuser:appuser . .

# 11. Switch to the non-root user for security
USER appuser

# 12. Expose the port Streamlit runs on
EXPOSE 8501

# 13. The command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]