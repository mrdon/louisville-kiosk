.PHONY: help serve open validate lint-yaml backup restore clean install-deps convert-backgrounds-grayscale deploy-check

# Default target
help: ## Show this help message
	@echo "Louisville Kiosk - Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

# Variables
PORT?=8080
BACKUP_DIR=backups
TIMESTAMP=$(shell date +%Y%m%d_%H%M%S)

serve: ## Start local web server on port 8080 (PORT=XXXX to change)
	@echo "Starting web server on http://localhost:$(PORT)"
	@echo "Press Ctrl+C to stop"
	@which python3 > /dev/null && python3 -m http.server $(PORT) || \
	 (which python > /dev/null && python -m SimpleHTTPServer $(PORT) || \
	  (which php > /dev/null && php -S localhost:$(PORT) || \
	   echo "Error: No suitable web server found. Install Python or PHP."))

open: ## Open kiosk in default browser (starts server if needed)
	@if ! curl -s http://localhost:$(PORT) > /dev/null 2>&1; then \
		echo "Starting web server..."; \
		make serve & \
		sleep 2; \
	fi
	@echo "Opening kiosk in browser..."
	@which xdg-open > /dev/null && xdg-open http://localhost:$(PORT) || \
	 (which open > /dev/null && open http://localhost:$(PORT) || \
	  echo "Please open http://localhost:$(PORT) in your browser")

validate: lint-yaml ## Validate all configuration files

lint-yaml: ## Validate YAML syntax in all data files
	@echo "Validating YAML files..."
	@VALID=0; \
	INVALID=0; \
	for file in data/*.yaml; do \
		if python3 -c "import yaml; yaml.safe_load(open('$$file'))" 2>/dev/null; then \
			echo "✓ $$file"; \
			VALID=$$((VALID + 1)); \
		else \
			echo "✗ $$file - INVALID"; \
			INVALID=$$((INVALID + 1)); \
		fi; \
	done; \
	echo ""; \
	echo "Results: $$VALID valid, $$INVALID invalid"; \
	if [ $$INVALID -gt 0 ]; then exit 1; fi

backup: ## Backup current data files to backups/ folder
	@echo "Creating backup..."
	@mkdir -p $(BACKUP_DIR)
	@tar -czf $(BACKUP_DIR)/kiosk-data-$(TIMESTAMP).tar.gz data/ images/
	@echo "✓ Backup created: $(BACKUP_DIR)/kiosk-data-$(TIMESTAMP).tar.gz"
	@ls -lh $(BACKUP_DIR)/ | tail -5

restore: ## Restore from latest backup (BACKUP=filename to specify)
	@if [ -z "$(BACKUP)" ]; then \
		LATEST=$$(ls -t $(BACKUP_DIR)/kiosk-data-*.tar.gz 2>/dev/null | head -1); \
		if [ -z "$$LATEST" ]; then \
			echo "No backups found in $(BACKUP_DIR)/"; \
			exit 1; \
		fi; \
		echo "Restoring from latest backup: $$LATEST"; \
		tar -xzf "$$LATEST"; \
	else \
		echo "Restoring from $(BACKUP)"; \
		tar -xzf "$(BACKUP)"; \
	fi
	@echo "✓ Restore complete"

list-backups: ## List all available backups
	@echo "Available backups in $(BACKUP_DIR)/:"
	@ls -lh $(BACKUP_DIR)/kiosk-data-*.tar.gz 2>/dev/null || echo "No backups found"

clean: ## Clean up temporary files and caches
	@echo "Cleaning temporary files..."
	@find . -name ".DS_Store" -delete 2>/dev/null || true
	@find . -name "Thumbs.db" -delete 2>/dev/null || true
	@find . -name "*~" -delete 2>/dev/null || true
	@echo "✓ Cleanup complete"

install-deps: ## Install development dependencies (Python, YAML validator)
	@echo "Checking dependencies..."
	@which python3 > /dev/null || (echo "✗ Python3 not found. Please install Python 3" && exit 1)
	@echo "✓ Python3 found"
	@python3 -c "import yaml" 2>/dev/null || \
		(echo "Installing PyYAML..." && pip3 install pyyaml --user)
	@echo "✓ All dependencies installed"

# Content management
add-business: ## Add a new business (interactive)
	@echo "Adding new business..."
	@echo "Name: "; read name; \
	echo "Logo (emoji): "; read logo; \
	echo "Tagline: "; read tagline; \
	echo "Call to action: "; read cta; \
	echo "" >> data/businesses.yaml; \
	echo "- name: $$name" >> data/businesses.yaml; \
	echo "  logo: $$logo" >> data/businesses.yaml; \
	echo "  tagline: $$tagline" >> data/businesses.yaml; \
	echo "  cta: $$cta" >> data/businesses.yaml; \
	echo "✓ Business added to data/businesses.yaml"

stats: ## Show content statistics
	@echo "Content Statistics:"
	@echo "  Businesses:       $$(grep -c '^- name:' data/businesses.yaml)"
	@echo "  Town Facts:       $$(grep -c '^- content:' data/town-facts.yaml)"
	@echo "  Images:           $$(grep -c '^- title:' data/town-images.yaml)"
	@echo "  Events:           $$([ -f data/events.yaml ] && grep -c '^- title:' data/events.yaml || echo 0)"
	@echo "  Image Files:      $$(find images -type f \( -iname "*.jpg" -o -iname "*.png" -o -iname "*.jpeg" \) 2>/dev/null | wc -l)"
	@echo ""
	@echo "Total Slides:      $$(( $$(grep -c '^- name:' data/businesses.yaml) + $$(grep -c '^- content:' data/town-facts.yaml) + $$(grep -c '^- title:' data/town-images.yaml) ))"

# Deployment helpers
fullscreen: ## Launch kiosk in fullscreen mode (requires browser CLI)
	@echo "Launching in fullscreen mode..."
	@which google-chrome > /dev/null && \
		google-chrome --kiosk --app=file://$(CURDIR)/index.html || \
	 (which chromium > /dev/null && \
		chromium --kiosk --app=file://$(CURDIR)/index.html || \
	  (which firefox > /dev/null && \
		firefox --kiosk file://$(CURDIR)/index.html || \
	   echo "No suitable browser found for kiosk mode"))

test-images: ## Test that all referenced images exist
	@echo "Checking image references..."
	@MISSING=0; \
	for img in $$(grep 'image:' data/town-images.yaml | awk '{print $$2}'); do \
		if [ -f "$$img" ]; then \
			echo "✓ $$img"; \
		else \
			echo "✗ $$img - MISSING"; \
			MISSING=$$((MISSING + 1)); \
		fi; \
	done; \
	if [ $$MISSING -gt 0 ]; then \
		echo ""; \
		echo "⚠ $$MISSING image(s) missing"; \
		exit 1; \
	else \
		echo ""; \
		echo "✓ All images found"; \
	fi

generate-maps: ## Generate location maps for all businesses
	@echo "Generating business location maps..."
	@uv run python scripts/generate_maps.py --quiet

generate-qrcodes: ## Generate QR codes for all business websites
	@echo "Clearing old QR codes..."
	@rm -f images/qrcodes/*.png
	@echo "Generating business QR codes..."
	@uv run python scripts/generate_qrcodes.py

convert-backgrounds-grayscale: ## Convert all background images to grayscale
	@echo "Converting background images to grayscale..."
	@uv run scripts/convert_backgrounds_grayscale.py

scrape-events: ## Scrape events from Louisville websites
	@echo "Scraping events from Louisville websites..."
	@uv run python scripts/scrape_events.py

test-chamber-scraper: ## Test Chamber of Commerce scraper (saves debug HTML)
	@echo "Testing Chamber of Commerce scraper..."
	@cd scripts/scrapers && uv run python scrape_chamber_calendar.py
	@echo ""
	@echo "Debug HTML saved to: /tmp/chamber_calendar_debug.html"

test-community-scraper: ## Test Community calendar scraper (saves debug HTML)
	@echo "Testing Community calendar scraper..."
	@cd scripts/scrapers && uv run python scrape_community_calendar.py
	@echo ""
	@echo "Debug HTML saved to: /tmp/community_calendar_debug.html"

test-eventbrite-scraper: ## Test Eventbrite scraper
	@echo "Testing Eventbrite scraper..."
	@cd scripts/scrapers && uv run python scrape_eventbrite.py

test-all-scrapers: test-chamber-scraper test-community-scraper test-eventbrite-scraper ## Test all event scrapers

generate-all: generate-maps generate-qrcodes ## Generate both maps and QR codes

# Development workflow
dev: validate serve ## Validate and start development server

prepush: validate backup ## Run before pushing changes (validate + backup)
	@echo "✓ Ready to push"

deploy-check: validate ## Check if ready for deployment
	@echo "Checking deployment readiness..."
	@echo ""
	@echo "✓ Validating YAML files..."
	@$(MAKE) -s lint-yaml
	@echo ""
	@echo "✓ Checking required files..."
	@test -f index.html || (echo "✗ Missing index.html" && exit 1)
	@test -f Dockerfile || (echo "✗ Missing Dockerfile" && exit 1)
	@test -f nginx.conf || (echo "✗ Missing nginx.conf" && exit 1)
	@echo "  - index.html"
	@echo "  - Dockerfile"
	@echo "  - nginx.conf"
	@echo ""
	@echo "✓ Ready to deploy!"
	@echo ""
	@echo "Deployment commands:"
	@echo "  1. git add . && git commit -m 'Deploy'"
	@echo "  2. git push dokku main"

deploy: backup validate ## Prepare for deployment (backup + validate)
	@echo "✓ Ready to deploy"
	@echo "Copy files to deployment location or run 'make open' to test"
