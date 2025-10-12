# 1. Start with a compatible Python version
FROM python:3.9-slim

# 2. Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# 3. Install system dependencies for OpenCV and other libraries
RUN apt-get update && apt-get install -y build-essential libgl1

# 4. Create a non-root user for security and GIVE IT OWNERSHIP of its home
RUN useradd appuser && chown -R appuser:appuser /home/appuser
WORKDIR /home/appuser/app

# 5. Upgrade Python's build tools
RUN pip install --upgrade pip setuptools wheel

# 6. Copy and install Python packages (rebuilding spacy from source)
COPY requirements.txt .
RUN pip install --no-cache-dir --no-binary spacy -r requirements.txt

# 7. Copy your application code and set ownership
COPY --chown=appuser:appuser . .

# 8. Switch to the non-root user
USER appuser

# 9. Expose the port Streamlit runs on
EXPOSE 8501

# 10. The command to run the Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]