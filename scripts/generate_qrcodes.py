#!/usr/bin/env python3
"""
Generate QR code images for any item with a URL in YAML data files
"""
import yaml
import os
import re
import glob
import qrcode
from PIL import Image

def slugify(text):
    """Convert text to filename slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')

def generate_qr_code(url, filename):
    """
    Generate QR code image for a URL.

    Uses the qrcode library with:
    - High error correction (L level is fine for URLs)
    - Good size for kiosk display
    - White background, black foreground
    """
    try:
        # Create QR code instance
        qr = qrcode.QRCode(
            version=1,  # Auto-size
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )

        # Add data
        qr.add_data(url)
        qr.make(fit=True)

        # Create image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to file
        img.save(filename)

        return True

    except Exception as e:
        print(f"  Error generating QR code: {e}")
        import traceback
        traceback.print_exc()
        return False

def get_item_identifier(item, file_basename):
    """
    Extract a human-readable identifier from an item based on common fields.
    Returns (identifier, type) where type is 'name', 'title', 'content', or 'unknown'
    """
    # Try common identifier fields in order of preference
    if 'name' in item:
        return (item['name'], 'name')
    elif 'title' in item:
        return (item['title'], 'title')
    elif 'content' in item:
        # For content, truncate to first 50 chars
        content = item['content'][:50] + "..." if len(item['content']) > 50 else item['content']
        return (content, 'content')
    else:
        return (f"Item from {file_basename}", 'unknown')

def generate_qr_filename(item, idx, file_basename, qrcodes_dir):
    """
    Generate an appropriate QR code filename based on the item and file type.

    For businesses: use slug of name (e.g., "bittersweet-cafe-qr.png")
    For events: use event-slug (e.g., "event-board-meeting-qr.png")
    For facts: use fact-N (e.g., "fact-1-qr.png")
    For others: use basename-N (e.g., "town-images-1-qr.png")
    """
    identifier, id_type = get_item_identifier(item, file_basename)

    if file_basename == 'town-facts':
        # Special case: facts use numbered format
        return f"{qrcodes_dir}/fact-{idx}-qr.png"
    elif file_basename == 'events':
        # Special case: events use event- prefix
        slug = slugify(identifier)
        return f"{qrcodes_dir}/event-{slug}-qr.png"
    elif file_basename == 'businesses' and id_type == 'name':
        # Special case: businesses use name directly (legacy format)
        slug = slugify(identifier)
        return f"{qrcodes_dir}/{slug}-qr.png"
    elif id_type in ('name', 'title'):
        # Use slugified name or title with file basename prefix
        slug = slugify(identifier)
        return f"{qrcodes_dir}/{file_basename}-{slug}-qr.png"
    else:
        # Use file basename + index
        return f"{qrcodes_dir}/{file_basename}-{idx}-qr.png"

def process_yaml_file(filepath, qrcodes_dir):
    """
    Process a single YAML file and generate QR codes for all items with URLs.
    Returns (success_count, skip_count, fail_count)
    """
    file_basename = os.path.splitext(os.path.basename(filepath))[0]

    with open(filepath, 'r') as f:
        items = yaml.safe_load(f)

    # Skip if not a list
    if not isinstance(items, list):
        print(f"  Skipping - not a list of items\n")
        return (0, 0, 0)

    print(f"Found {len(items)} items\n")

    success_count = 0
    skip_count = 0
    fail_count = 0

    # For large files (>50 items), suppress individual item output
    verbose = len(items) < 50

    for idx, item in enumerate(items, 1):
        if not isinstance(item, dict):
            skip_count += 1
            continue

        # Check for URL field (try both 'url' and 'website')
        url = item.get('url') or item.get('website')

        if not url:
            identifier, _ = get_item_identifier(item, file_basename)
            if verbose:
                print(f"⚠ {identifier}: No URL found, skipping")
            skip_count += 1
            continue

        identifier, _ = get_item_identifier(item, file_basename)

        if verbose:
            print(f"Processing: {identifier}")
            print(f"  URL: {url}")

        # Generate filename
        filename = generate_qr_filename(item, idx, file_basename, qrcodes_dir)

        # Check if QR code already exists
        if os.path.exists(filename):
            if verbose:
                print(f"  ℹ QR code already exists: {filename}")
                print()
            success_count += 1
            continue

        # Generate QR code
        if generate_qr_code(url, filename):
            file_size = os.path.getsize(filename)
            if verbose:
                print(f"  ✓ QR code saved: {filename} ({file_size/1024:.1f} KB)")
                print()
            success_count += 1
        else:
            if verbose:
                print(f"  ✗ Failed to generate QR code")
                print()
            fail_count += 1

    # For large files, print a summary
    if not verbose:
        print(f"  Processed {len(items)} items: {success_count} generated, {skip_count} skipped, {fail_count} failed\n")

    return (success_count, skip_count, fail_count)

def main():
    print("Louisville Kiosk - QR Code Generator")
    print("Generating QR codes for all items with URLs\n")

    # Get data directory
    data_dir = '/home/mrdon/dev/louisville-kiosk/data'

    # Create qrcodes directory if needed
    qrcodes_dir = '/home/mrdon/dev/louisville-kiosk/images/qrcodes'
    os.makedirs(qrcodes_dir, exist_ok=True)

    # Find all YAML files in data directory
    yaml_files = glob.glob(f"{data_dir}/*.yaml")
    yaml_files.sort()

    print(f"Found {len(yaml_files)} YAML files to process\n")

    total_success = 0
    total_skip = 0
    total_fail = 0

    # Process each YAML file
    for yaml_file in yaml_files:
        file_basename = os.path.splitext(os.path.basename(yaml_file))[0]

        print("=" * 60)
        print(f"Processing: {file_basename}.yaml")
        print("=" * 60 + "\n")

        try:
            success, skip, fail = process_yaml_file(yaml_file, qrcodes_dir)
            total_success += success
            total_skip += skip
            total_fail += fail

            print(f"{file_basename}: {success} QR codes, {skip} skipped (no URL), {fail} failed\n")
        except Exception as e:
            print(f"  Error processing file: {e}\n")
            import traceback
            traceback.print_exc()

    print("=" * 60)
    print(f"Total: {total_success} QR codes generated, {total_skip} skipped, {total_fail} failed")
    print("=" * 60)

if __name__ == '__main__':
    main()
