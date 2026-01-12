# Business Location Maps

This directory contains map images showing the location of each business featured in the kiosk.

## Map Images Needed

The following map images need to be created for each business:

1. **bittersweet-cafe-map.jpg** - 836 Main St, Louisville, CO 80027
2. **chinook-pharmacy-map.jpg** - 625 Main St, Ste 1, Louisville, CO 80027
3. **boulder-valley-dental-map.jpg** - 1805 Hwy 42, Ste 120, Louisville, CO 80027
4. **shopeys-pizza-map.jpg** - 640 Main St, Unit D, Louisville, CO 80027
5. **coal-creek-ace-hardware-map.jpg** - 1343 E South Boulder Rd, Louisville, CO 80027
6. **yoga-junction-map.jpg** - 927 Main St, Louisville, CO 80027

## How to Generate Map Images

### Option 1: Google Maps Static API
```
https://maps.googleapis.com/maps/api/staticmap?center=ADDRESS&zoom=15&size=600x400&markers=color:red%7CADDRESS&key=YOUR_API_KEY
```

### Option 2: OpenStreetMap Screenshot
1. Visit https://www.openstreetmap.org
2. Search for each address
3. Zoom to appropriate level (zoom 16-17 works well)
4. Take a screenshot of the map area
5. Crop to 600x400 pixels
6. Save as JPEG

### Option 3: Mapbox Static API
```
https://api.mapbox.com/styles/v1/mapbox/streets-v11/static/pin-s+ff0000(LONGITUDE,LATITUDE)/LONGITUDE,LATITUDE,15,0/600x400?access_token=YOUR_ACCESS_TOKEN
```

### Option 4: Manual Screenshots
1. Use Google Maps (https://maps.google.com)
2. Search for the address
3. Switch to satellite or street view as appropriate
4. Take a screenshot
5. Crop and resize to 600x400 pixels
6. Save as JPEG with the appropriate filename

## Coordinates Reference

For APIs that require lat/lon coordinates:

- **Bittersweet Cafe**: 39.9779° N, 105.1319° W
- **Chinook Pharmacy**: 39.9774° N, 105.1327° W
- **Boulder Valley Dental**: 39.9658° N, 105.1533° W
- **Shopey's Pizza**: 39.9773° N, 105.1321° W
- **Coal Creek Ace Hardware**: 39.9646° N, 105.1247° W
- **Yoga Junction**: 39.9783° N, 105.1310° W

## Image Specifications

- **Size**: 600x400 pixels
- **Format**: JPEG
- **Quality**: 85-90%
- **Zoom Level**: 15-17 (street level detail)
- **Marker**: Red pin at business location
- **Style**: Street map view preferred
