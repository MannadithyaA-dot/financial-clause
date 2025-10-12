# 1. Start with a compatible Python version
FROM python:3.9-slim

# 2. Set environment variables for best practices in containers
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install ALL system dependencies required for a full source build
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
RUN pip install --upgrade pip

# 6. KEY FIX 1: Install PyTorch and torchvision FIRST from the correct index.
#    This must use a pre-compiled binary for a CPU-only environment.
RUN pip install --no-cache-dir torch torchvision --extra-index-url https://download.pytorch.org/whl/cpu

# 7. Copy requirements file
COPY requirements.txt .

# 8. KEY FIX 2: Install the REST of the packages.
#    This uses the targeted fix for the spaCy/NumPy incompatibility.
RUN pip install \
    --no-cache-dir \
    --no-binary "thinc,murmurhash,preshed,cymem,blis" \
    -r requirements.txt

# 9. Download the spaCy language model
RUN python -m spacy download en_core_web_sm

# 10. Copy your application code and set ownership for the non-root user
COPY --chown=appuser:appuser . .

# 11. Switch to the non-root user for security
USER appuser

# 12. Expose the port Streamlit runs on
EXPOSE 8501

# 13. The command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]