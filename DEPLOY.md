# Deploying to Dokku

This static site is deployed using **nginx:alpine** via Docker for minimal resource usage (~5-10MB).

## Features

- **Lightweight**: nginx:alpine image (minimal footprint)
- **Optimized**: Gzip compression, cache headers
- **Secure**: Security headers included
- **Fast**: Static file serving with efficient caching

## Prerequisites

- Dokku server set up and accessible
- Git remote configured for Dokku

## Deployment Steps

### 1. Check deployment readiness

```bash
make deploy-check
```

This validates all YAML files and checks that required deployment files exist.

### 2. Create app on Dokku server (first time only)

```bash
# SSH into your Dokku server
dokku apps:create louisville

# Set domain (optional)
dokku domains:add louisville yourdomain.com

# Enable SSL with Let's Encrypt (optional but recommended)
dokku letsencrypt:enable louisville
```

### 3. Set up git remote (first time only)

```bash
git remote add dokku dokku@your-server.com:louisville
```

### 4. Deploy

```bash
git push dokku main
```

Or if your branch is named differently:
```bash
git push dokku master:main
```

## Files Used

- **Dockerfile** - nginx:alpine container configuration
- **nginx.conf** - Web server configuration with caching and security
- **.dockerignore** - Excludes unnecessary files from build

## Resource Usage

The nginx:alpine container is extremely lightweight:
- **Image size**: ~5-10MB compressed
- **Memory**: ~2-5MB at runtime
- **CPU**: Minimal (static file serving)

Perfect for a kiosk display running 24/7!