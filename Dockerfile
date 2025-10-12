# 1. Start with a compatible Python version
FROM python:3.9-slim

# 2. Set environment variables for best practices in containers
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install ALL system dependencies required for a full source build
#    FINAL FIX: Adds autoconf/automake/libtool for the GNU Build System.
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    libgl1 \
    autoconf \
    automake \
    libtool

# 4. Create a non-root user AND its home directory correctly
RUN useradd -m appuser
WORKDIR /home/appuser/app

# 5. Upgrade Python's build tools first
RUN pip install --upgrade pip setuptools wheel

# 6. Copy requirements file
COPY requirements.txt .

# 7. DEFINITIVE FIX: Install a stable numpy, then rebuild ALL other packages from source
#    The --no-binary :all: flag forbids pre-compiled wheels, guaranteeing compatibility.
RUN pip install --no-cache-dir numpy==1.23.5 && \
    pip install --no-cache-dir --no-binary :all: -r requirements.txt

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