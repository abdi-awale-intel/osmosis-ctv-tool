# Dockerfile for containerized builds with Python 3.13.1
FROM python:3.13.1-windowsservercore

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY images/ ./images/
COPY *.spec ./
COPY *.py ./

# Install the application
RUN pip install -e .

# Build executable
RUN pyinstaller ctvlist_gui.spec --clean --noconfirm

# Set up the final image
FROM mcr.microsoft.com/windows/servercore:ltsc2022
COPY --from=0 /app/dist/ /app/

# Set entry point
WORKDIR /app
CMD ["ctvlist_gui.exe"]
