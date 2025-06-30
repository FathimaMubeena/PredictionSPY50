
# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY src/main/requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application code into the container at /app
# This includes app.py and the 'resources' directory
COPY src/main/python/app.py .
COPY src/main/python/main.py .

# Expose the port that Dash runs on
# Your app.py specifies port 8050

EXPOSE 8050

# Run the app.py when the container launches
# Use '0.0.0.0' to ensure the Dash app is accessible from outside the container
CMD ["python", "app.py"]