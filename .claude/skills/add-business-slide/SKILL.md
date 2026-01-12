---
name: add-business-slide
description: Add new business slides to the Louisville kiosk slideshow. Use when the user wants to add, create, or feature a new Louisville, Colorado business in the kiosk display. Handles: (1) Finding real Louisville businesses, (2) Sourcing images from business websites, (3) Getting user approval on images, (4) Adding entries to businesses.yaml, (5) Generating location maps and QR codes, (6) Verifying the complete slide with hash anchor navigation.
---

# Add Business Slide

## Business Slide Requirements

Each business slide needs:
- **background_image**: Shared background from `images/backgrounds/`
- **primary_image**: Unique image saved to `images/primary/`
- **map_image**: Generated map in `images/maps/`
- **qr_code**: Generated QR code in `images/qrcodes/`
- **Business details**: name, logo emoji, tagline, CTA, address, phone, website

## Workflow

### 1. Gather Business Information

If user hasn't specified a business:
- Ask what type they want to feature
- Use WebSearch to find real Louisville, CO businesses
- Present 2-3 options with name, description, full address, website
- Let user choose

If user specified a business:
- Use WebSearch to find details
- Present complete information and confirm with user

### 2. Find and Select Business Image

1. Use WebFetch to visit the business website
2. Look for images showing interior/storefront/products/branding
3. Present image URL options to user with descriptions
4. Ask user which image they want (by number or description)
5. Once user selects an image URL, download directly to final location:
   ```bash
   curl -o images/primary/[business-slug].jpg "[selected-url]"
   ```
6. If none are good, search again with different queries

**DO NOT:**
- Download images to /tmp for preview
- Ask for confirmation after user selects an image URL
- Use the Read tool to show images during selection
- Once user picks a URL, proceed directly to downloading to final location

### 3. Generate Additional Content

Choose appropriate:
- **Emoji logo**: ☕ cafe, 🍕 restaurant, 💊 pharmacy, 🦷 dental, 🔨 hardware, 🧘 wellness, 🎨 art
- **Tagline**: Compelling one-liner (reference existing entries in businesses.yaml)
- **CTA**: Invitation to visit
- **Background**:
  - `historic-downtown.jpg` (Main Street)
  - `colorado-town-scene.jpg` (general)
  - `indoor-community.jpg` (indoor/services)
  - `colorado-mountains.jpg` (wellness/outdoor)
  - `community-gathering.jpg` (events)

### 4. Add Business to Data File

Add to `data/businesses.yaml`:

```yaml
- name: Business Name
  logo: 🎨
  tagline: Compelling one-liner
  cta: Call to action
  address: Full address, City, State ZIP
  phone: (xxx) xxx-xxxx
  website: https://...
  background_image: images/backgrounds/[chosen].jpg
  primary_image: images/primary/[business-slug].jpg
  map_image: images/maps/[business-slug]-map.jpg
  qr_code: images/qrcodes/[business-slug]-qr.png
  notes: Real business - Brief description
```

Append to end, maintain proper YAML formatting.

### 5. Generate Map and QR Code

**IMPORTANT: Always run after adding to businesses.yaml**

```bash
make generate-all
```

This command runs both:
- `generate_maps.py` - Geocodes the address and generates `images/maps/[business-slug]-map.jpg` with red marker
- `generate_qrcodes.py` - Generates `images/qrcodes/[business-slug]-qr.png` from website URL

Alternatively, run individually:
```bash
uv run python generate_maps.py
uv run python generate_qrcodes.py
```

**If map generation fails:** Use the `fix-map-generation` skill to resolve geocoding errors, service failures, or address parsing issues. The skill ensures every business gets a correct map for their actual location.

### 6. Open Slide in Browser

**Final verification step**

```bash
xdg-open "http://localhost:8080#[business-slug]"
```

Hash anchor navigates directly to the slide and disables auto-rotation.

Verify with user:
- Primary image showing
- Map overlay in bottom-right corner
- QR code overlay in bottom-left corner (if website present)
- Business details visible
- Colors and layout correct

### 7. Final Summary

Provide:
- Business name added
- File paths (primary image, map, QR code)
- Link: `http://localhost:8080#[business-slug]`
- Confirmation slide is ready

## Key Notes

- Only add real Louisville, CO businesses
- Present image URLs to user for selection - once they pick one, download directly to final location
- Do NOT download images to /tmp for preview or ask for confirmation after user selects
- Always run `make generate-all` after adding to businesses.yaml (generates both map and QR code)
- QR codes are only generated for businesses with website URLs
- Test with hash anchor to verify complete slide
- Fetch images from business website, not stock photos
- Follow existing style in businesses.yaml

## File Naming

Use slugify format:
- Lowercase
- Hyphens for spaces
- No special characters
- Example: "Bittersweet Cafe & Confections" → "bittersweet-cafe-confections"
