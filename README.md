# Louisville Kiosk Display

A fullscreen kiosk application for displaying local events, business advertisements, town facts, and historical images for Louisville, Colorado.

## Features

- **Fullscreen Display**: Clean, distraction-free interface designed for waiting rooms
- **Smart Randomization**: Content shuffled on load with intelligent sequencing to prevent repeats
- **Random Animations**: Subtle zoom and floating effects applied randomly (40% probability) to avoid predictability
- **Five Content Types**:
  - Community events (farmers markets, festivals, public gatherings)
  - Business events (events hosted by local businesses)
  - Business advertisements (local shops and services)
  - Town facts (Louisville history and information)
  - Town images (current and historical photos)
- **YAML Configuration**: Easy-to-edit human-readable config files
- **Auto-refresh**: Page reloads daily to fetch updated content
- **Clock Display**: Live time and date in status bar

## Getting Started

### Quick Start with Makefile

The easiest way to get started is using the included Makefile:

```bash
make serve          # Start local web server
make open           # Open kiosk in browser
make fullscreen     # Launch in fullscreen kiosk mode
make stats          # Show content statistics
make validate       # Validate YAML files
```

Run `make help` to see all available commands.

### Manual Setup

#### 1. Open the Kiosk

Simply open `index.html` in any modern web browser. For best results, use Chrome or Firefox.

#### 2. Enter Fullscreen Mode

Press `F11` (Windows/Linux) or use your browser's fullscreen option to enter kiosk mode.

#### 3. Add Your Content

Edit the YAML files in the `data/` folder:

- `data/community-events.yaml` - Public events and town activities
- `data/business-events.yaml` - Events hosted by local businesses
- `data/businesses.yaml` - Business advertisements
- `data/town-facts.yaml` - Interesting Louisville facts
- `data/town-images.yaml` - Photo slide definitions

#### 4. Add Images

Place your image files (JPG, PNG) in the `images/` folder and reference them in `town-images.yaml`.

## YAML Format Examples

**Community Events:**
```yaml
- title: Farmers Market
  date: Every Saturday
  time: 8:00 AM - 1:00 PM
  location: Main Street
  description: Fresh local produce
  icon: 🌽
```

**Business Events:**
```yaml
- business: Rocky Mountain Coffee
  title: Live Jazz Nights
  date: Every Friday
  time: 7:00 PM - 9:00 PM
  description: Enjoy local jazz musicians
  icon: 🎷
```

**Businesses:**
```yaml
- name: Coffee Shop
  logo: ☕
  tagline: Your neighborhood coffee shop
  cta: Visit us today!
```

**Town Facts:**
```yaml
- content: Louisville was founded in 1877 as a mining community.
  icon: ⛏️
```

**Town Images:**
```yaml
- title: Historic Main Street, 1920s
  caption: Downtown during the coal mining era
  image: images/historic-main-street.jpg
  category: historical
```

## Content Categories

The kiosk automatically mixes content from these categories:

1. **Community Events** - Town-wide events open to all residents
2. **Business Events** - Events at specific local businesses
3. **Business Ads** - Advertisements for local shops and services
4. **Town Facts** - Historical and demographic information
5. **Images** - Current and historical photos of Louisville

The smart sequencing ensures variety by avoiding consecutive slides of the same type.

## Makefile Commands

The included Makefile provides useful commands for development and deployment:

### Development
- `make serve` - Start local web server (default port 8080)
- `make open` - Open kiosk in default browser
- `make dev` - Validate YAML and start server
- `make fullscreen` - Launch in fullscreen kiosk mode

### Content Management
- `make stats` - Show content statistics
- `make add-event` - Interactively add a community event
- `make add-business` - Interactively add a business
- `make backup` - Backup all data to backups/ folder
- `make restore` - Restore from latest backup
- `make list-backups` - List all available backups

### Validation & Testing
- `make validate` - Validate all YAML files
- `make lint-yaml` - Check YAML syntax
- `make test-images` - Verify all image files exist

### Deployment
- `make prepush` - Validate and backup before pushing
- `make deploy` - Prepare for deployment
- `make clean` - Clean temporary files

Run `make help` for the complete list of commands.

## Configuration

### Slide Duration
Edit `js/slideshow.js` line 6:
```javascript
this.slideDuration = 10000; // milliseconds (10 seconds)
```

### Animation Probability
Edit `js/slideshow.js` line 9:
```javascript
this.animationProbability = 0.4; // 40% of slides animate
```

## Browser Setup for Kiosk Mode

For a permanent installation:

1. **Disable screensaver/sleep mode** in OS settings
2. **Auto-start browser** on boot pointing to `index.html`
3. **Use F11 fullscreen** or a browser kiosk extension
4. **Disable browser updates/notifications** for uninterrupted display

## Technology Stack

- Vanilla JavaScript (minimal dependencies)
- js-yaml for YAML parsing (loaded from CDN)
- CSS3 animations
- YAML-based content management
- Responsive design

## File Structure

```
/index.html                      # Main kiosk display
/css/styles.css                  # Styling and animations
/js/slideshow.js                 # Slideshow logic
/data/
  ├── community-events.yaml      # Public events
  ├── business-events.yaml       # Business-hosted events
  ├── businesses.yaml            # Business ads
  ├── town-facts.yaml            # Town facts
  └── town-images.yaml           # Image definitions
/images/                         # Your image files go here
  └── README.md                  # Image folder instructions
```

## Animations

The kiosk uses two subtle animations:

1. **Gentle Zoom** (40% of slides): Slowly zooms from 1x to 1.03x and back over 10 seconds
2. **Floating Icon** (40% of slides): Icons gently float up and down

Animation is applied randomly to avoid predictability and reduce visual fatigue.

## Troubleshooting

**Content not loading?**
- Check that all YAML files are valid (use yamllint.com or a YAML validator)
- Open browser console (F12) to check for errors
- Ensure js-yaml library loads from CDN

**Slides not rotating?**
- Ensure JavaScript is enabled
- Check console for errors

**Images not showing?**
- Verify image paths in `town-images.yaml` match actual files
- Image paths should be relative: `images/filename.jpg`
- Check image file permissions

**Display looks wrong?**
- Try different browser (Chrome recommended)
- Check screen resolution settings
- Verify CSS loaded correctly

## Customization Tips

- Use emojis for icons - they scale well and work across all browsers
- Keep text concise - slides are only visible for 10 seconds
- High-contrast colors work best for visibility from distance
- Test on the actual display hardware before deploying
- Update content regularly to keep it fresh
