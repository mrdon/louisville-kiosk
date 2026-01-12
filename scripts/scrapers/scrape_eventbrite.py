#!/usr/bin/env python3
"""
Scrape events from Eventbrite for Louisville, Colorado
Searches for events at The Louisville Underground venue
"""
import json
import re
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup


def parse_eventbrite_date(date_str: str) -> Optional[str]:
    """
    Parse Eventbrite ISO 8601 datetime string
    """
    try:
        # Eventbrite uses ISO 8601 format
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        # Remove timezone for consistency
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt.isoformat()
    except Exception as e:
        print(f"  ⚠ Could not parse date '{date_str}': {e}")
        return None


def scrape_eventbrite() -> List[Dict]:
    """
    Scrape events from Eventbrite for Louisville, Colorado
    """
    events = []

    # Search for all Louisville, CO events
    url = "https://www.eventbrite.com/d/co--louisville/events/"

    print(f"Fetching: {url}")

    try:
        headers = {'User-Agent': 'Louisville-Kiosk/1.0'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find JSON-LD structured data
        json_ld_scripts = soup.find_all('script', type='application/ld+json')

        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)

                # Handle both single event and list of events
                event_list = []
                if isinstance(data, dict):
                    if data.get('@type') == 'Event':
                        event_list = [data]
                    elif data.get('@type') == 'ItemList':
                        event_list = data.get('itemListElement', [])
                elif isinstance(data, list):
                    event_list = data

                for item in event_list:
                    # Extract event from itemListElement structure
                    event_data = item
                    if isinstance(item, dict) and 'item' in item:
                        event_data = item['item']

                    if not isinstance(event_data, dict) or event_data.get('@type') != 'Event':
                        continue

                    # Extract event details
                    name = event_data.get('name')
                    if not name:
                        continue

                    # Get start date/time
                    start_date = event_data.get('startDate')
                    if not start_date:
                        continue

                    event_time = parse_eventbrite_date(start_date)
                    if not event_time:
                        continue

                    # If time is midnight (00:00:00), default to 7:00 PM
                    if event_time.endswith('T00:00:00'):
                        event_time = event_time.replace('T00:00:00', 'T19:00:00')

                    # Calculate duration
                    duration = 120  # Default 2 hours
                    end_date = event_data.get('endDate')
                    if end_date:
                        try:
                            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                            duration = int((end_dt - start_dt).total_seconds() / 60)
                        except:
                            pass

                    # Get location info
                    location_data = event_data.get('location', {})
                    location_name = None
                    address = None

                    if isinstance(location_data, dict):
                        if location_data.get('name'):
                            location_name = location_data['name']
                        if location_data.get('address'):
                            addr = location_data['address']
                            if isinstance(addr, dict):
                                # Build address from components
                                parts = []
                                if addr.get('streetAddress'):
                                    parts.append(addr['streetAddress'])
                                if addr.get('addressLocality'):
                                    parts.append(addr['addressLocality'])
                                if addr.get('addressRegion'):
                                    parts.append(addr['addressRegion'])
                                if addr.get('postalCode'):
                                    parts.append(addr['postalCode'])
                                if parts:
                                    address = ', '.join(parts)
                            elif isinstance(addr, str):
                                address = addr

                    # Skip online-only events
                    if not location_name or 'online' in location_name.lower():
                        continue
                    if not address:
                        continue

                    # Skip events not in Louisville, CO
                    if 'louisville' not in address.lower() or 'co' not in address.lower():
                        continue

                    # Get event URL
                    event_url = event_data.get('url', url)

                    # Get event image
                    image = event_data.get('image')
                    if isinstance(image, list) and image:
                        image = image[0]
                    if isinstance(image, dict):
                        image = image.get('url')

                    # Get description
                    description = event_data.get('description', '')
                    if len(description) > 200:
                        description = description[:200] + '...'

                    # Try to match venue to known businesses
                    related_business = None
                    location_lower = location_name.lower()
                    if 'louisville underground' in location_lower:
                        related_business = 'The Louisville Underground'
                    # Add more venue mappings as needed

                    # Create event object
                    event = {
                        'title': name,
                        'description': description or f"Event at {location_name}",
                        'time': event_time,
                        'duration': duration,
                        'location': location_name,
                        'address': address,
                        'url': event_url,
                        'image': image,
                        'is_major': False,
                        'related_business': related_business
                    }

                    events.append(event)
                    print(f"  ✓ {name}")

            except json.JSONDecodeError:
                continue
            except Exception as e:
                print(f"  ⚠ Error parsing event: {e}")
                continue

    except Exception as e:
        print(f"  ✗ Error scraping Eventbrite: {e}")
        import traceback
        traceback.print_exc()

    return events


def main():
    """Test the scraper"""
    events = scrape_eventbrite()
    print(f"\nTotal events found: {len(events)}")

    if events:
        print("\nSample event:")
        import json
        print(json.dumps(events[0], indent=2))


if __name__ == '__main__':
    main()
