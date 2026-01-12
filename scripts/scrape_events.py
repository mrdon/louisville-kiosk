#!/usr/bin/env python3
"""
Louisville Colorado Event Scraper

Scrapes events from various Louisville, CO websites and generates a JSON file
containing event information including time, duration, location, URL, image, and
whether it's a major event.

Data structure:
{
  "events": [
    {
      "title": "Event Title",
      "description": "Event description",
      "time": "2026-01-15T19:00:00",
      "duration": 120,
      "location": "Venue Name",
      "address": "123 Main St, Louisville, CO 80027",
      "url": "https://event-url.com",
      "image": "images/events/event-name.jpg",
      "is_major": false,
      "related_business": "Business Name"
    }
  ],
  "last_updated": "2026-01-11T12:00:00"
}
"""
import json
import os
import sys
import re
import yaml
from datetime import datetime
from typing import List, Dict, Optional
import requests

# Add scrapers directory to Python path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SCRAPERS_DIR = os.path.join(SCRIPT_DIR, 'scrapers')
sys.path.insert(0, SCRAPERS_DIR)

# Configuration
OUTPUT_FILE = '/home/mrdon/dev/louisville-kiosk/data/events.yaml'
EVENTS_IMAGE_DIR = '/home/mrdon/dev/louisville-kiosk/images/events'


def slugify(text):
    """Convert text to URL-friendly slug"""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')




def download_event_image(image_url: str, event_title: str) -> Optional[str]:
    """
    Download an event image and save it locally

    Returns the local path to the image or None if download failed
    """
    if not image_url:
        return None

    try:
        # Create events directory if it doesn't exist
        os.makedirs(EVENTS_IMAGE_DIR, exist_ok=True)

        # Generate filename
        slug = slugify(event_title)
        ext = image_url.split('.')[-1].split('?')[0]  # Get extension, remove query params
        if ext not in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
            ext = 'jpg'

        filename = f"{slug}.{ext}"
        filepath = os.path.join(EVENTS_IMAGE_DIR, filename)

        # Download image
        headers = {'User-Agent': 'Louisville-Kiosk/1.0'}
        response = requests.get(image_url, headers=headers, timeout=10)
        response.raise_for_status()

        # Save image
        with open(filepath, 'wb') as f:
            f.write(response.content)

        # Return relative path for JSON
        return f"images/events/{filename}"

    except Exception as e:
        print(f"  ⚠ Failed to download image for {event_title}: {e}")
        return None


def scrape_all_events() -> List[Dict]:
    """
    Scrape events from all configured sources
    """
    all_events = []

    print("Louisville Kiosk - Event Scraper")
    print("=" * 60)

    # Import all scrapers
    from scrape_chamber_calendar import scrape_chamber_calendar
    from scrape_community_calendar import scrape_community_calendar
    from scrape_eventbrite import scrape_eventbrite

    scrapers = [
        ('Chamber of Commerce Calendar', scrape_chamber_calendar),
        ('Community Calendar', scrape_community_calendar),
        ('Eventbrite', scrape_eventbrite),
    ]

    # Run each scraper
    for scraper_name, scraper_func in scrapers:
        print(f"\n{scraper_name}")
        print("-" * 60)
        try:
            events = scraper_func()
            all_events.extend(events)
            print(f"  ✓ Added {len(events)} events from {scraper_name}")
        except Exception as e:
            print(f"  ✗ Error running {scraper_name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"Total events scraped: {len(all_events)}")

    # Filter out past events
    all_events = filter_future_events(all_events)
    print(f"Future events (after filtering): {len(all_events)}")

    return all_events


def filter_future_events(events: List[Dict]) -> List[Dict]:
    """
    Filter events to only include those happening today or in the future
    """
    from datetime import datetime, timezone

    now = datetime.now()
    # Set to start of today (midnight)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    future_events = []
    past_count = 0

    for event in events:
        try:
            # Parse event time
            event_time_str = event.get('time')
            if not event_time_str:
                continue

            # Parse ISO 8601 datetime
            event_time = datetime.fromisoformat(event_time_str.replace('Z', '+00:00'))

            # Remove timezone info for comparison if present
            if event_time.tzinfo:
                event_time = event_time.replace(tzinfo=None)

            # Keep events happening today or later
            if event_time >= today:
                future_events.append(event)
            else:
                past_count += 1

        except Exception as e:
            print(f"  ⚠ Error parsing event time for '{event.get('title', 'Unknown')}': {e}")
            # Keep events with invalid dates rather than discarding
            future_events.append(event)

    if past_count > 0:
        print(f"  Filtered out {past_count} past events")

    return future_events


def save_events(events: List[Dict]):
    """
    Save events to YAML file
    """
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Add metadata comment at top
    header = f"# Louisville Colorado Events\n# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n# Total events: {len(events)}\n\n"

    with open(OUTPUT_FILE, 'w') as f:
        f.write(header)
        yaml.dump(events, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\n✓ Events saved to {OUTPUT_FILE}")


def main():
    """
    Main scraper function
    """
    # Scrape events from all sources
    events = scrape_all_events()

    # Save to JSON file
    save_events(events)

    print("\nEvent scraper completed successfully!")


if __name__ == '__main__':
    main()
