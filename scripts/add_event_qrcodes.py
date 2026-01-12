#!/usr/bin/env python3
"""
Add qr_code fields to events.yaml for events that have URLs
"""
import yaml
import re
from datetime import datetime

def slugify(text):
    """Convert event title to filename slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def main():
    print("Adding QR code fields to events.yaml\n")

    events_file = '/home/mrdon/dev/louisville-kiosk/data/events.yaml'

    # Load events
    with open(events_file, 'r') as f:
        events = yaml.safe_load(f)

    print(f"Found {len(events)} events\n")

    updated_count = 0
    skipped_count = 0

    # Add qr_code field to events with URLs
    for event in events:
        title = event['title']
        url = event.get('url')

        if not url:
            print(f"⚠ {title}: No URL, skipping")
            skipped_count += 1
            continue

        # Generate QR code path
        slug = slugify(title)
        qr_code_path = f"images/qrcodes/event-{slug}-qr.png"

        # Add qr_code field
        event['qr_code'] = qr_code_path

        print(f"✓ {title}")
        print(f"  QR code: {qr_code_path}")
        updated_count += 1

    # Save updated events.yaml
    print(f"\nUpdating {events_file}...")

    with open(events_file, 'w') as f:
        # Write header comment
        f.write("# Louisville Colorado Events\n")
        f.write(f"# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Total events: {len(events)}\n\n")

        # Write events with proper YAML formatting
        yaml.dump(events, f,
                  default_flow_style=False,
                  allow_unicode=True,
                  sort_keys=False,
                  width=120)

    print(f"\n✓ Updated {updated_count} events with QR code fields")
    print(f"⚠ Skipped {skipped_count} events without URLs")

if __name__ == '__main__':
    main()
