# Images Directory

## Structure

- **backgrounds/** - Background images for slides (referenced in YAML files)
- **primary/** - Main images for businesses, town facts, and photo carousels
- **events/** - Event-specific images
- **maps/** - Auto-generated location maps (via `make generate-maps`)
- **qrcodes/** - Auto-generated QR codes (via `make generate-qrcodes`)

## Adding Images

Add new images to `primary/` and reference them in data files:
- Business ads: `data/businesses.yaml` → `primary_image: images/primary/your-file.jpg`
- Town facts: `data/town-facts.yaml` → `image: images/primary/your-file.jpg`
- Photo carousel: `data/town-images.yaml` → `image: images/primary/your-file.jpg`

Maps and QR codes are generated automatically - don't add them manually.