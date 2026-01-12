---
name: fix-map-generation
description: Fix map generation failures when adding business slides to the Louisville kiosk. Use this skill when `make generate-all` fails to generate a map file for a business (errors like "HTTP Error 503", "Could not get coordinates", or Python errors during geocoding). This skill ensures every business gets a map for their actual location without modifying their address.
---

# Fix Map Generation

When adding businesses to the Louisville kiosk, `make generate-all` sometimes fails to generate map files due to geocoding service errors, API rate limits, or address parsing issues.

## When This Happens

After running `make generate-all`, you'll see errors like:

```
Processing: Business Name
  Address: 901 Front St #B100
  Error getting coordinates: HTTP Error 503: Service Unavailable
  ✗ Could not get coordinates
```

## Solution Workflow

### Step 1: Check for Same Address

Check if another business in `data/businesses.yaml` has the same address (same building/street number).

**Example:**
- Failed: `Centerstage Theatre Company` at `901 Front St #B100`
- Found: `Pica's Mexican Taqueria` at `901 Front St`

Same building = same location = can use same map.

### Step 2: Copy Map from Same Address

Find the existing map:

```bash
ls -la images/maps/ | grep -i pica
```

Result: `picas-mexican-taqueria-c1f8984c-map.jpg`

Copy the map, keeping the same hash:

```bash
cp images/maps/picas-mexican-taqueria-c1f8984c-map.jpg images/maps/centerstage-theatre-company-c1f8984c-map.jpg
```

**Important:** The hash represents the geocoded coordinates for that address.

Update `data/businesses.yaml`:

```yaml
map_image: images/maps/centerstage-theatre-company-c1f8984c-map.jpg
```

### Step 3: Verify the Map

Open the slide to verify:

```bash
xdg-open "http://localhost:8080#business-slug"
```

## If No Same Address Exists

If no other business has the same address, the map MUST be generated correctly.

### Temporary Service Errors (HTTP 503, Rate Limits)

These are transient. Retry after 30-60 seconds:

```bash
make generate-all
```

### Script Bugs (Python errors, parsing failures)

If the error is a Python exception or parsing error with the address format:

**DO NOT modify the business address.** Suite numbers, unit designators, and other address details are important business information.

**FIX THE SCRIPT INSTEAD:**

1. Read the map generation script:
   ```bash
   uv run python generate_maps.py
   ```

2. Identify why it's failing for this address format
3. Update `generate_maps.py` to handle the address format correctly
4. Test the fix by running `make generate-all` again

Common script issues:
- Not handling suite numbers (`#B100`, `Ste 1`, `Unit D`)
- Address parsing assumes specific format
- Geocoding API parameters need adjustment for complex addresses

## Never Do These

**DO NOT:**
- Use generic city-level maps (hash `99b41919`)
- Remove suite numbers or address details to make geocoding work
- Modify the business address in any way

**ALWAYS:**
- Keep the exact address as provided
- Fix the script if it can't handle the address format
- Copy from same address if available
