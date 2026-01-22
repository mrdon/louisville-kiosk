FROM nginx:alpine

# Install Python, cron, and timezone support
RUN apk add --no-cache python3 py3-pip dcron tzdata

# Copy project config and install dependencies from pyproject.toml
COPY pyproject.toml /app/
RUN pip3 install --no-cache-dir --break-system-packages /app/

# Copy scraper scripts
COPY scripts /app/scripts

# Copy static files to nginx html directory
COPY index.html /usr/share/nginx/html/
COPY css /usr/share/nginx/html/css
COPY js /usr/share/nginx/html/js
COPY images /usr/share/nginx/html/images
COPY data /usr/share/nginx/html/data

# Also copy data to seed location (used when persistent storage is empty)
COPY data /app/data-seed

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy crontab and startup script
COPY docker/crontab /etc/crontabs/root
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

# Set timezone
ENV TZ=America/Denver

# Expose port 5000 (Dokku default)
EXPOSE 5000

# Start nginx and cron
CMD ["/start.sh"]
