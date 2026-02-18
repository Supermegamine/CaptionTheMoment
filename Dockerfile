# Use a slim python image
FROM python:3.11-slim

# Set a working dir
WORKDIR /app

# Avoid Python writing bytecode + set environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Streamlit server options
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false

# Copy and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app
COPY . .

# Expose the port (provider will set PORT as env)
EXPOSE 8501

# Start command uses PORT env if available
CMD streamlit run app.py --server.port ${PORT:-8501} --server.headless true
