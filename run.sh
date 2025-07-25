#!/bin/bash

# This script sets up and runs the YouTube Downloader web application.

# Exit immediately if a command exits with a non-zero status
set -e

# Check if Python3 and pip are installed
if ! command -v python3 &> /dev/null || ! command -v pip &> /dev/null; then
    echo "Python3 and pip are required to run this application. Please install them and try again."
    exit 1
fi

# Create a virtual environment
echo "Creating a virtual environment..."
python3 -m venv venv

# Activate the virtual environment
echo "Activating the virtual environment..."
# For macOS and Linux
if [[ "$OSTYPE" == "linux-gnu"* || "$OSTYPE" == "darwin"* ]]; then
    source venv/bin/activate
# For Windows
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    echo "Unsupported OS. Please activate the virtual environment manually."
    exit 1
fi

# Install the required packages
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the Flask application
echo "Starting the Flask application..."
export FLASK_APP=src/web.py
export FLASK_ENV=development
flask run

# Note: To stop the server, use Ctrl+C in the terminal.