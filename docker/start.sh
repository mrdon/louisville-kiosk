#!/bin/sh
# Louisville Kiosk startup script
# Starts both nginx (web server) and crond (scheduled tasks)

echo "Starting Louisville Kiosk..."

# Seed data directory if empty (happens on first deploy with persistent storage)
if [ -z "$(ls -A /usr/share/nginx/html/data 2>/dev/null)" ]; then
    echo "Data directory empty, seeding from built-in data..."
    cp -r /app/data-seed/* /usr/share/nginx/html/data/
    echo "Data seeded successfully"
fi

# Create log file
touch /var/log/scraper.log

# Start cron daemon in background
echo "Starting cron daemon..."
crond -b -l 8

# Run initial scrape on startup (in background so nginx starts quickly)
echo "Running initial event scrape in background..."
/app/scripts/run-scrapers.sh >> /var/log/scraper.log 2>&1 &

# Start nginx in foreground
echo "Starting nginx..."
exec nginx -g 'daemon off;'
