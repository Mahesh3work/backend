# Use an official Python image as base
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port Flask will run on
EXPOSE 5000

# Start the Flask app using Gunicorn
# Total DB connections ≈ GUNICORN_WORKERS × DB_POOL_SIZE; keep under MySQL max_connections
ENV GUNICORN_WORKERS=2
CMD ["sh", "-c", "gunicorn -w ${GUNICORN_WORKERS} -b 0.0.0.0:5000 app:app"]
