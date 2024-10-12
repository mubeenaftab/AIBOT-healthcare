# Pull official latest Python Docker image
FROM python:latest

# Set the working directory
WORKDIR /usr/backend

# Add ARG for log path
ARG LOG_PATH=/usr/backend/app.log

# Expose the log path as an ENV variable
ENV LOG_PATH=$LOG_PATH
# Set up Python behavior
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV VIRTUAL_ENV=/opt/venv

# Switch on virtual environment
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set the server port
EXPOSE 8000

# Install system dependencies
RUN apt-get update \
  && apt-get -y install netcat-openbsd gcc postgresql-client \
  && apt-get clean

# Install Python dependencies
RUN pip install --upgrade pip
COPY requirements.txt ./
RUN pip install -r requirements.txt

# Copy all files from the backend folder (where Dockerfile and start.sh are)
COPY . .

# Create the Invoices directory inside /usr/backend
RUN mkdir -p /usr/backend/Invoices

# Use the script as the entry point, adding the migration command directly
CMD alembic upgrade head && uvicorn src.main:backend_app --reload --workers 4 --host 0.0.0.0 --port 8000
