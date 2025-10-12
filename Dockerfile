# 1. Start with a compatible Python version
FROM python:3.9-slim

# 2. Set environment variables for best practices in containers
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install system dependencies (build tools are essential)
RUN apt-get update && apt-get install -y build-essential libgl1

# 4. Create a non-root user AND its home directory correctly
RUN useradd -m appuser
WORKDIR /home/appuser/app

# 5. Upgrade Python's build tools first
RUN pip install --upgrade pip setuptools wheel

# 6. Copy requirements file
COPY requirements.txt .

# 7. Install dependencies, forcing a rebuild of problematic packages
#    THIS IS THE DEFINITIVE FIX for the numpy incompatibility.
#    It installs a stable numpy, then installs the rest of the requirements
#    while FORCING thinc and murmurhash to build from source.
RUN pip install --no-cache-dir numpy==1.23.5 && \
    pip install --no-cache-dir --no-binary thinc,murmurhash -r requirements.txt

# 8. Download the spaCy language model
RUN python -m spacy download en_core_web_sm

# 9. Copy your application code and set ownership for the non-root user
COPY --chown=appuser:appuser . .

# 10. Switch to the non-root user for security
USER appuser

# 11. Expose the port Streamlit runs on
EXPOSE 8501

# 12. The command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]