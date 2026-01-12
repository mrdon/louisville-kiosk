#!/usr/bin/env python3
"""
Generate map images for Louisville businesses using staticmap library
"""
import yaml
import urllib.request
import urllib.parse
import time
import os
import re
import json
import hashlib
import glob
from staticmap import StaticMap, IconMarker
from PIL import Image, ImageDraw

def slugify(text):
    """Convert business name to filename slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def hash_address(address):
    """Create a short hash of the address for filename uniqueness"""
    # Create MD5 hash of address, return first 8 characters
    return hashlib.md5(address.encode()).hexdigest()[:8]

def clean_address(address):
    """
    Clean address by removing suite/unit/apartment numbers.

    Nominatim geocoding fails with secondary address components like:
    - Suite/Ste
    - Unit
    - Apartment/Apt
    - Room/Rm
    - Office/Ofc
    - #

    Best practice: geocode at the street/building level.
    """
    # Remove suite, unit, apartment, office, room numbers
    # Patterns like ", Ste 1", ", Unit D", ", Suite 120", ", Apt 5", " #225"
    patterns = [
        r',?\s+(Suite|Ste|Unit|Apartment|Apt|Room|Rm|Office|Ofc)\.?\s+[\w\d-]+',
        r',?\s+#\s*[\w\d-]+',
    ]

    cleaned = address
    for pattern in patterns:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)

    # Expand common abbreviations that Nominatim doesn't handle well
    # Hwy -> Highway
    cleaned = re.sub(r'\bHwy\b', 'Highway', cleaned, flags=re.IGNORECASE)

    return cleaned.strip()

def get_coordinates(address):
    """Get coordinates from OpenStreetMap Nominatim API"""
    # Clean address before geocoding
    cleaned_address = clean_address(address)

    if cleaned_address != address:
        print(f"  Cleaned address: {cleaned_address}")

    base_url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': cleaned_address,
        'format': 'json',
        'limit': 1
    }

    url = f"{base_url}?{urllib.parse.urlencode(params)}"
    headers = {'User-Agent': 'Louisville-Kiosk/1.0'}

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            results = json.loads(data)

            if results:
                lat = float(results[0]['lat'])
                lon = float(results[0]['lon'])
                return lat, lon
            else:
                print(f"  No results found for: {cleaned_address}")
    except Exception as e:
        print(f"  Error getting coordinates for '{cleaned_address}': {e}")

    return None, None

def create_pin_icon(size=48):
    """Create a red pin/pushpin icon for map markers"""
    # Create a new image with transparency
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw a pin shape (teardrop/marker shape)
    # Pin is centered at bottom middle of the image
    center_x = size // 2
    circle_radius = size // 3

    # Draw the circular top part of the pin
    draw.ellipse(
        [center_x - circle_radius, 0, center_x + circle_radius, circle_radius * 2],
        fill=(220, 20, 60, 255),  # Crimson red
        outline=(150, 0, 0, 255)   # Darker outline
    )

    # Draw the pointed bottom part (triangle)
    draw.polygon(
        [
            (center_x - circle_radius // 2, circle_radius * 1.5),
            (center_x + circle_radius // 2, circle_radius * 1.5),
            (center_x, size - 2)
        ],
        fill=(220, 20, 60, 255),  # Crimson red
        outline=(150, 0, 0, 255)   # Darker outline
    )

    # Draw a white circle in the center for visibility
    inner_radius = circle_radius // 2
    draw.ellipse(
        [center_x - inner_radius, circle_radius - inner_radius,
         center_x + inner_radius, circle_radius + inner_radius],
        fill=(255, 255, 255, 255)
    )

    return img

def generate_map_image(lat, lon, filename, business_name=None, zoom=18):
    """
    Generate map using staticmap library with pin markers.

    Uses the staticmap library which handles:
    - Automatic tile downloading from OpenStreetMap
    - Proper attribution
    - Marker placement
    - Map rendering

    Much cleaner than manually downloading tiles!
    """
    try:
        from PIL import ImageFont

        # Create map (800x600 output)
        m = StaticMap(800, 600, url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')

        # Create and save pin marker to temporary file
        pin_icon = create_pin_icon(60)
        pin_path = '/tmp/map_pin.png'
        pin_icon.save(pin_path)

        # Add pin marker at the location
        marker = IconMarker((lon, lat), pin_path, 30, 60)  # offset_x, offset_y to center pin point
        m.add_marker(marker)

        # Render map at specified zoom level
        image = m.render(zoom=zoom)

        # Save to file
        image.save(filename)

        return True

    except Exception as e:
        print(f"  Error generating map: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Generate location maps for businesses and events')
    parser.add_argument('--businesses-only', action='store_true', help='Only process businesses, skip events')
    parser.add_argument('--quiet', action='store_true', help='Suppress output for existing maps')
    args = parser.parse_args()

    print("Louisville Kiosk - Map Generator")
    print("Using staticmap library with OpenStreetMap tiles\n")

    # Load businesses data
    businesses_file = '/home/mrdon/dev/louisville-kiosk/data/businesses.yaml'
    events_file = '/home/mrdon/dev/louisville-kiosk/data/events.yaml'

    with open(businesses_file, 'r') as f:
        businesses = yaml.safe_load(f)

    # Load events if file exists (unless --businesses-only flag is set)
    events = []
    if not args.businesses_only and os.path.exists(events_file):
        with open(events_file, 'r') as f:
            events = yaml.safe_load(f) or []

    # Deduplicate events by (title, address) to avoid processing recurring events multiple times
    if events:
        seen = {}
        unique_events = []
        for event in events:
            key = (event.get('title'), event.get('address'))
            if key not in seen:
                seen[key] = True
                unique_events.append(event)
        events = unique_events

    # Create maps directory if needed
    maps_dir = '/home/mrdon/dev/louisville-kiosk/images/maps'
    os.makedirs(maps_dir, exist_ok=True)

    print(f"Found {len(businesses)} businesses and {len(events)} events\n")

    success_count = 0
    fail_count = 0

    # Process businesses
    print("=== PROCESSING BUSINESSES ===\n")
    for business in businesses:
        name = business['name']
        address = business.get('address')

        if not address:
            print(f"⚠ {name}: No address found, skipping")
            fail_count += 1
            continue

        print(f"Processing: {name}")
        print(f"  Address: {address}")

        # Generate filename with address hash
        slug = slugify(name)
        addr_hash = hash_address(address)
        filename = f"{maps_dir}/{slug}-{addr_hash}-map.jpg"

        # Check if map already exists
        if os.path.exists(filename):
            if not args.quiet:
                print(f"  ℹ Map already exists: {filename}")
                print()
            success_count += 1
            # No sleep needed for skipped items
            continue

        # Clean up old map files for this business (different address hash)
        old_maps = glob.glob(f"{maps_dir}/{slug}-*-map.jpg")
        for old_map in old_maps:
            if old_map != filename:
                os.remove(old_map)
                print(f"  🗑 Removed old map: {old_map}")

        # Get coordinates
        lat, lon = get_coordinates(address)

        if not lat or not lon:
            print(f"  ✗ Could not get coordinates")
            fail_count += 1
            print()
            continue

        print(f"  Coordinates: {lat}, {lon}")

        # Generate map image with business name
        if generate_map_image(lat, lon, filename, business_name=name):
            file_size = os.path.getsize(filename)
            print(f"  ✓ Map saved: {filename} ({file_size/1024:.1f} KB)")
            success_count += 1
        else:
            print(f"  ✗ Failed to generate map")
            fail_count += 1

        # Be nice to the API (Nominatim usage policy)
        time.sleep(1)
        print()

    # Process events
    if events:
        print("\n=== PROCESSING EVENTS ===\n")
        for event in events:
            title = event.get('title')
            address = event.get('address')

            if not address:
                print(f"⚠ {title}: No address found, skipping")
                fail_count += 1
                continue

            # If address is incomplete (no city/state), combine with location
            if 'CO' not in address and '80027' not in address:
                location = event.get('location', 'Louisville, CO')
                full_address = f"{address}, {location}"
                if not args.quiet:
                    print(f"Processing: {title}")
                    print(f"  Address: {address} → {full_address}")
                address = full_address
            else:
                print(f"Processing: {title}")
                print(f"  Address: {address}")

            # Generate filename with address hash
            slug = slugify(title)
            addr_hash = hash_address(address)
            filename = f"{maps_dir}/{slug}-{addr_hash}-map.jpg"

            # Check if map already exists
            if os.path.exists(filename):
                if not args.quiet:
                    print(f"  ℹ Map already exists: {filename}")
                    print()
                success_count += 1
                # No sleep needed for skipped items
                continue

            # Clean up old map files for this event (different address hash)
            old_maps = glob.glob(f"{maps_dir}/{slug}-*-map.jpg")
            for old_map in old_maps:
                if old_map != filename:
                    os.remove(old_map)
                    print(f"  🗑 Removed old map: {old_map}")

            # Get coordinates
            lat, lon = get_coordinates(address)

            if not lat or not lon:
                print(f"  ✗ Could not get coordinates")
                fail_count += 1
                print()
                continue

            print(f"  Coordinates: {lat}, {lon}")

            # Generate map image with event title
            if generate_map_image(lat, lon, filename, business_name=title):
                file_size = os.path.getsize(filename)
                print(f"  ✓ Map saved: {filename} ({file_size/1024:.1f} KB)")
                success_count += 1
            else:
                print(f"  ✗ Failed to generate map")
                fail_count += 1

            # Be nice to the API (Nominatim usage policy)
            time.sleep(1)
            print()

    print("=" * 60)
    print(f"Done! {success_count} maps generated, {fail_count} failed")
    print("=" * 60)

if __name__ == '__main__':
    main()
