# Event Scrapers

This directory contains individual scraper modules for different Louisville event sources.

## Current Scrapers

### Louisville City Calendar
**File:** `scrape_louisville_calendar.py`
**URL:** https://www.louisvilleco.gov/exploring-louisville/about-us/advanced-components/list-detail-pages/calendar-meeting-list

## Testing a Scraper

To test an individual scraper:

```bash
cd scripts/scrapers
uv run python scrape_louisville_calendar.py
```

This will:
1. Fetch the calendar page
2. Save the HTML to `/tmp/louisville_calendar_debug.html` for inspection
3. Attempt to parse events
4. Display sample output

## Customizing the Louisville Calendar Scraper

The scraper includes placeholder selectors that need to be customized based on the actual HTML structure:

1. **Run the scraper once** to save the HTML to `/tmp/louisville_calendar_debug.html`
2. **Inspect the HTML file** to identify the correct CSS selectors:
   - Event container: `div.calendar-item`, `li.event`, etc.
   - Title: `h2`, `h3`, `.event-title`, etc.
   - Date/Time: `.event-date`, `time`, etc.
   - Location: `.location`, `.venue`, etc.
   - Description: `.description`, `p.summary`, etc.
3. **Update the selectors** in `parse_event_item()` function
4. **Test again** until events are correctly parsed

## Adding a New Scraper

1. Create a new file: `scrape_<source_name>.py`
2. Implement the main scraping function that returns a list of events
3. Use this structure:

```python
def scrape_source_name() -> List[Dict]:
    """
    Scrape events from Source Name

    Returns list of events in standard format
    """
    events = []

    # Your scraping logic here

    return events
```

4. Update `scripts/scrape_events.py` to import and use your scraper:

```python
try:
    from scrape_source_name import scrape_source_name
    scrapers.append(('Source Name', scrape_source_name))
except ImportError as e:
    print(f"\n⚠ Could not import Source scraper: {e}")
```

## Event Data Format

Each scraper should return events in this format:

```python
{
    'title': str,              # Event name
    'description': str,        # Event description
    'time': str,              # ISO 8601 format: "2026-01-15T19:00:00"
    'duration': int,          # Duration in minutes
    'location': str,          # Venue name
    'address': str,           # Full address for map generation
    'url': str,               # Link to event page
    'image': str or None,     # Path to downloaded image
    'is_major': bool,         # True for major events (get dedicated slide)
    'related_business': str or None  # Business name from businesses.yaml
}
```

## Troubleshooting

### 403 Forbidden Errors
The scraper uses proper browser headers to avoid 403 errors. If you still get blocked:
- Check if the site requires cookies/sessions
- Try adjusting the User-Agent string
- Consider adding delays between requests

### Parsing Issues
- Always save debug HTML and inspect it first
- Use browser DevTools to identify correct selectors
- Test selectors with `soup.select()` in a Python REPL

### Date Parsing
The Louisville scraper includes common date format patterns. Add new patterns to `parse_datetime()` if needed.
