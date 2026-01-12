#!/usr/bin/env python3
"""
Scraper for Louisville Colorado Chamber of Commerce calendar
URL: https://business.louisvillechamber.com/chambercalendar
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from typing import List, Dict, Optional
import json


def scrape_chamber_calendar() -> List[Dict]:
    """
    Scrape events from Louisville Chamber of Commerce calendar

    Returns list of events in the standard format
    """
    url = "https://business.louisvillechamber.com/chambercalendar"

    events = []

    try:
        # Use proper headers
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive'
        }

        print(f"  Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # Save HTML for debugging
        debug_file = '/tmp/chamber_calendar_debug.html'
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"  Debug HTML saved to: {debug_file}")

        # Find event containers
        # Based on WebFetch analysis: gz-list-col, gz-grid-col, or gz-calendar-col
        event_items = soup.select('.gz-list-col, .gz-grid-col, .gz-calendar-col')

        if not event_items:
            print(f"  ⚠ No events found with standard selectors, trying alternatives...")
            event_items = soup.select('[class*="gz-"][class*="-col"]')

        print(f"  Found {len(event_items)} event items")

        for item in event_items:
            try:
                event = parse_event_item(item, url)
                if event:
                    events.append(event)
            except Exception as e:
                print(f"  ⚠ Error parsing event item: {e}")
                continue

        print(f"  ✓ Scraped {len(events)} events from Chamber calendar")

    except requests.exceptions.RequestException as e:
        print(f"  ✗ Error fetching Chamber calendar: {e}")
    except Exception as e:
        print(f"  ✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

    return events


def parse_event_item(item, base_url: str) -> Optional[Dict]:
    """
    Parse a single event item from the HTML
    """
    try:
        # Extract title from link
        title_elem = item.select_one('a.gz-card-title')
        if not title_elem:
            return None
        title = title_elem.get_text(strip=True)

        # Extract event URL
        event_url = ""
        if title_elem.has_attr('href'):
            event_url = title_elem['href']

        # Extract date components
        month_elem = item.select_one('.gz-start-dt')
        day_elem = item.select_one('.gz-start-dy')

        month_text = month_elem.get_text(strip=True) if month_elem else ""
        day_text = day_elem.get_text(strip=True) if day_elem else ""

        # Extract time
        time_elem = item.select_one('h5.gz-event-card-time')
        time_text = time_elem.get_text(strip=True) if time_elem else ""

        # Try to use the schema.org datetime first
        schema_date_elem = item.select_one('meta[itemprop="startDate"]')
        if schema_date_elem and schema_date_elem.has_attr('content'):
            datetime_text = schema_date_elem['content']
            event_time = parse_schema_datetime(datetime_text)
        else:
            # Combine date and time for parsing
            datetime_text = f"{month_text} {day_text} {time_text}".strip()
            event_time = parse_datetime(datetime_text)

        if not event_time:
            print(f"  ⚠ Could not parse date for event: {title}")
            # Try to extract just the date and use default time
            event_time = parse_date_only(date_text)
            if not event_time:
                return None

        # Extract location
        location_elem = item.select_one('.gz-location, .gz-venue, [class*="location"]')
        location = location_elem.get_text(strip=True) if location_elem else "Louisville, CO"

        # Extract description
        desc_elem = item.select_one('.gz-description, .gz-event-description, p')
        description = desc_elem.get_text(strip=True) if desc_elem else ""

        # Determine if it's a major event
        # Major events: Feel Good Festival, Taste of Louisville, Pints in the Park, etc.
        is_major = any(keyword in title.lower() for keyword in [
            'festival', 'taste of louisville', 'pints in the park',
            'golf scramble', 'awards dinner', 'summerfest'
        ])

        # Try to match with known businesses
        related_business = match_related_business(title, description, location)

        return {
            'title': title,
            'description': description,
            'time': event_time,
            'duration': 120,  # Default 2 hours
            'location': location,
            'address': extract_address(location, description),
            'url': event_url,
            'image': None,  # Could extract from item if images are present
            'is_major': is_major,
            'related_business': related_business
        }

    except Exception as e:
        print(f"  ⚠ Error parsing event: {e}")
        return None


def parse_schema_datetime(datetime_text: str) -> Optional[str]:
    """
    Parse schema.org datetime format
    Example: "1/15/2026 9:00:00 AM"
    """
    if not datetime_text:
        return None

    try:
        # Try various formats
        formats = [
            '%m/%d/%Y %I:%M:%S %p',  # 1/15/2026 9:00:00 AM
            '%m/%d/%Y %I:%M %p',     # 1/15/2026 9:00 AM
            '%m/%d/%Y',              # 1/15/2026
        ]

        for fmt in formats:
            try:
                dt = datetime.strptime(datetime_text, fmt)
                return dt.isoformat()
            except:
                continue

    except Exception as e:
        print(f"  ⚠ Error parsing schema datetime: {e}")

    return None


def parse_datetime(datetime_text: str) -> Optional[str]:
    """
    Parse Chamber calendar date/time formats into ISO 8601

    Common formats:
    - "THU January 15 9:00 AM - 11:00 AM"
    - "FRI February 28 10:00 AM - 8:00 PM"
    """
    if not datetime_text:
        return None

    # Try ISO format first
    try:
        dt = datetime.fromisoformat(datetime_text.replace('Z', '+00:00'))
        return dt.isoformat()
    except:
        pass

    # Pattern: "DAY Month DD H:MM AM/PM"
    # Example: "THU January 15 9:00 AM"
    pattern = r'(?:\w{3}\s+)?(\w+)\s+(\d+)(?:,?\s+(\d{4}))?\s+(\d+):(\d+)\s*(AM|PM)?'
    match = re.search(pattern, datetime_text, re.IGNORECASE)

    if match:
        try:
            month_name = match.group(1)
            day = match.group(2).zfill(2)
            year = match.group(3) if match.group(3) else str(datetime.now().year)
            hour = match.group(4)
            minute = match.group(5)
            meridiem = match.group(6)

            month = month_to_num(month_name)
            time_24h = convert_to_24h(hour, minute, meridiem)

            return f"{year}-{month}-{day}T{time_24h}:00"
        except Exception as e:
            print(f"  ⚠ Error converting datetime: {e}")

    return None


def parse_date_only(date_text: str) -> Optional[str]:
    """
    Parse just the date and use a default time (6:00 PM)
    """
    if not date_text:
        return None

    # Pattern: "DAY Month DD" or "Month DD"
    pattern = r'(?:\w{3}\s+)?(\w+)\s+(\d+)(?:,?\s+(\d{4}))?'
    match = re.search(pattern, date_text, re.IGNORECASE)

    if match:
        try:
            month_name = match.group(1)
            day = match.group(2).zfill(2)
            year = match.group(3) if match.group(3) else str(datetime.now().year)

            month = month_to_num(month_name)

            # Default to 6:00 PM
            return f"{year}-{month}-{day}T18:00:00"
        except Exception as e:
            print(f"  ⚠ Error converting date: {e}")

    return None


def month_to_num(month_name: str) -> str:
    """Convert month name to number"""
    months = {
        'jan': '01', 'january': '01',
        'feb': '02', 'february': '02',
        'mar': '03', 'march': '03',
        'apr': '04', 'april': '04',
        'may': '05',
        'jun': '06', 'june': '06',
        'jul': '07', 'july': '07',
        'aug': '08', 'august': '08',
        'sep': '09', 'september': '09',
        'oct': '10', 'october': '10',
        'nov': '11', 'november': '11',
        'dec': '12', 'december': '12'
    }
    return months.get(month_name.lower(), '01')


def convert_to_24h(hour: str, minute: str, meridiem: Optional[str]) -> str:
    """Convert 12-hour time to 24-hour format"""
    hour_int = int(hour)

    if meridiem:
        meridiem = meridiem.upper()
        if meridiem == 'PM' and hour_int != 12:
            hour_int += 12
        elif meridiem == 'AM' and hour_int == 12:
            hour_int = 0

    return f"{hour_int:02d}:{minute}"


def extract_address(location: str, description: str) -> str:
    """
    Try to extract a full address from location or description
    """
    # Common Louisville addresses
    text = f"{location} {description}".lower()

    # Look for street addresses
    address_pattern = r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|drive|dr|way|boulevard|blvd|lane|ln|court|ct|place|pl)'
    match = re.search(address_pattern, text, re.IGNORECASE)

    if match:
        address = match.group(0)
        # Add Louisville, CO if not present
        if 'louisville' not in text:
            address += ", Louisville, CO 80027"
        return address

    # If no specific address, return the location as-is
    return location if location else "Louisville, CO 80027"


def match_related_business(title: str, description: str, location: str) -> Optional[str]:
    """
    Try to match events with known businesses
    """
    # Common business names to look for (these should match businesses.yaml)
    businesses = [
        '12Degree Brewing',
        'Bittersweet Cafe',
        'Moxie Bread',
        'Shopey\'s Pizza',
        'Louisville Center for the Arts'
    ]

    text = f"{title} {description} {location}".lower()

    for business in businesses:
        if business.lower() in text:
            return business

    return None


def main():
    """Test the scraper"""
    print("Louisville Chamber of Commerce Calendar Scraper")
    print("=" * 60)

    events = scrape_chamber_calendar()

    print("\n" + "=" * 60)
    print(f"Total events scraped: {len(events)}")

    if events:
        print("\nSample events:")
        for i, event in enumerate(events[:3]):
            print(f"\n{i+1}. {event['title']}")
            print(f"   Time: {event['time']}")
            print(f"   Location: {event['location']}")
            print(f"   Major: {event['is_major']}")


if __name__ == '__main__':
    main()
