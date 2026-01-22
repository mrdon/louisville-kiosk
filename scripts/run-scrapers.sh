#!/bin/sh
# Louisville Kiosk - Scraper runner
# Called by cron to update event data

set -e

echo "========================================"
echo "Louisville Kiosk Scraper"
echo "Started: $(date)"
echo "========================================"

# Set paths
export DATA_DIR="/usr/share/nginx/html/data"
export IMAGES_DIR="/usr/share/nginx/html/images"

# Run the event scraper
cd /app/scripts
python3 scrape_events.py --output "$DATA_DIR/events.yaml" --images "$IMAGES_DIR/events"

echo ""
echo "Scraper completed: $(date)"
echo "========================================"
