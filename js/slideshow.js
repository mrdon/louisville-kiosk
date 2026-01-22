// Kiosk Slideshow Manager
class KioskSlideshow {
    constructor() {
        this.slides = [];
        this.currentIndex = 0;
        this.slideDuration = 10000; // 10 seconds per slide
        this.slideContainer = document.getElementById('slideshow');
        this.loadingElement = document.getElementById('loading');
        this.pauseIndicator = document.getElementById('pause-indicator');
        this.animationProbability = 0.4; // 40% chance of animation
        this.rotationInterval = null; // Track the rotation interval
        this.slideStats = new Map(); // Track times shown per unique slide
        this.isPaused = false; // Track pause state
        this.slideHistory = []; // Track history of slides shown for back navigation

        // Master weight configuration
        // Higher weight = appears more frequently in rotation
        this.weights = {
            business: 2,        // More frequent than facts/images
            fact: 1,            // Normal frequency
            image: 1,           // Normal frequency
            dailyEvents: 2,     // Today's events (same as recent events)
            event: {
                next7Days: 2,   // Recent events (happening soon!)
                days8to30: 1,   // Normal frequency
                days31Plus: 0,  // Don't show unless major
                major: 1        // Weight for major events beyond 30 days
            }
        };
    }

    slugify(text) {
        // Convert text to URL-friendly slug
        return text.toLowerCase()
            .replace(/[^\w\s-]/g, '')
            .replace(/[\s_-]+/g, '-')
            .replace(/^-+|-+$/g, '');
    }

    getUniqueId(slide) {
        // Generate unique identifier for a slide to track repeats
        // Use name/title as primary identifier, fallback to content
        switch (slide.type) {
            case 'business':
                return `business:${slide.name}`;
            case 'fact':
                return `fact:${slide.content.substring(0, 50)}`; // First 50 chars
            case 'image':
                return `image:${slide.title}`;
            case 'major-event':
                return `event:${slide.title}:${slide.time}`;
            case 'daily-events':
                return 'daily-events'; // Only one daily events slide
            default:
                return `unknown:${JSON.stringify(slide).substring(0, 50)}`;
        }
    }

    calculateSlideScore(slide) {
        // Calculate selection score based on weight and how often it's been shown
        const uniqueId = this.getUniqueId(slide);
        const timesShown = this.slideStats.get(uniqueId) || 0;

        // Recency multiplier: the more times shown, the lower the multiplier
        // Formula: 1 / (timesShown + 1)
        // First time: 1/1 = 1.0 (100%)
        // Second time: 1/2 = 0.5 (50%)
        // Third time: 1/3 = 0.33 (33%)
        const recencyMultiplier = 1 / (timesShown + 1);

        return slide.weight * recencyMultiplier;
    }

    weightedRandomSelect(scores) {
        // Select an index based on weighted random selection
        // scores is array of {idx, score}

        // Calculate total score
        const totalScore = scores.reduce((sum, item) => sum + item.score, 0);

        // Pick random value between 0 and totalScore
        let random = Math.random() * totalScore;

        // Find which index this corresponds to
        for (const item of scores) {
            random -= item.score;
            if (random <= 0) {
                return item.idx;
            }
        }

        // Fallback (shouldn't happen)
        return scores[scores.length - 1].idx;
    }

    selectNextSlide() {
        // Calculate scores for all slides
        const scores = this.slides.map((slide, idx) => ({
            idx,
            score: this.calculateSlideScore(slide)
        }));

        // Select using weighted random
        const selectedIndex = this.weightedRandomSelect(scores);

        // Update stats for the selected slide
        const selectedSlide = this.slides[selectedIndex];
        const uniqueId = this.getUniqueId(selectedSlide);
        const timesShown = this.slideStats.get(uniqueId) || 0;
        this.slideStats.set(uniqueId, timesShown + 1);

        // Log selection for debugging
        const slideName = selectedSlide.name || selectedSlide.title || selectedSlide.type;
        console.log(`Selected: "${slideName}" (shown ${timesShown + 1} times, score: ${scores[selectedIndex].score.toFixed(2)})`);

        return selectedIndex;
    }

    async init() {
        try {
            // Load all content from YAML files
            const [businesses, facts, images, events] = await Promise.all([
                this.loadYAML('data/businesses.yaml'),
                this.loadYAML('data/town-facts.yaml'),
                this.loadYAML('data/town-images.yaml'),
                this.loadYAML('data/events.yaml').catch(() => [])
            ]);

            // Build slide playlist
            this.buildPlaylist(businesses, facts, images, events || []);

            // Render all slides
            this.renderSlides();

            // Hide loading, show first slide (or slide from hash anchor)
            this.loadingElement.classList.add('hidden');

            // Check for hash anchor to navigate to specific slide
            const startIndex = this.getSlideIndexFromHash();
            this.currentIndex = startIndex;
            this.showSlide(startIndex);

            // Start slideshow rotation (but not if there's a hash anchor)
            if (!window.location.hash) {
                this.startRotation();
            } else {
                console.log('Hash anchor present, auto-rotation disabled');
                this.isPaused = true;
                this.updatePauseIndicator();
            }

            // Listen for hash changes to start/stop rotation
            window.addEventListener('hashchange', () => {
                if (window.location.hash) {
                    console.log('Hash added, pausing rotation');
                    this.isPaused = true;
                    this.stopRotation();
                    this.updatePauseIndicator();
                    // Navigate to the slide specified by the new hash
                    const newIndex = this.getSlideIndexFromHash();
                    this.currentIndex = newIndex;
                    this.showSlide(newIndex);
                } else {
                    console.log('Hash removed, resuming rotation');
                    this.isPaused = false;
                    this.startRotation();
                    this.updatePauseIndicator();
                }
            });

            // Refresh data files every 6 hours
            setInterval(() => this.refreshData(), 6 * 60 * 60 * 1000);

            // Auto-refresh page every 12 hours (picks up code/CSS updates)
            setTimeout(() => location.reload(true), 12 * 60 * 60 * 1000);

            // Setup keyboard controls
            this.setupKeyboardControls();

        } catch (error) {
            console.error('Failed to load content:', error);
            this.loadingElement.textContent = 'Error loading content. Please check data files.';
        }
    }

    setupKeyboardControls() {
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case ' ':
                    // Space bar: pause/resume
                    e.preventDefault();
                    this.togglePause();
                    break;
                case 'ArrowRight':
                    // Right arrow: next slide
                    e.preventDefault();
                    this.nextSlide();
                    break;
                case 'ArrowLeft':
                    // Left arrow: previous slide
                    e.preventDefault();
                    this.previousSlide();
                    break;
            }
        });
    }

    updatePauseIndicator() {
        if (this.isPaused) {
            this.pauseIndicator.classList.remove('hidden');
        } else {
            this.pauseIndicator.classList.add('hidden');
        }
    }

    togglePause() {
        if (this.isPaused) {
            console.log('Resuming slideshow');
            this.isPaused = false;
            this.startRotation();
        } else {
            console.log('Pausing slideshow');
            this.isPaused = true;
            this.stopRotation();
        }
        this.updatePauseIndicator();
    }

    nextSlide() {
        // Stop rotation if playing, select next slide manually
        if (this.rotationInterval) {
            this.stopRotation();
            this.isPaused = true;
            this.updatePauseIndicator();
        }

        // Add current slide to history before moving to next
        this.slideHistory.push(this.currentIndex);

        // Keep only last 10 slides in history
        if (this.slideHistory.length > 10) {
            this.slideHistory.shift();
        }

        this.currentIndex = this.selectNextSlide();
        this.showSlide(this.currentIndex);
    }

    previousSlide() {
        // Stop rotation if playing, go to previous slide manually
        if (this.rotationInterval) {
            this.stopRotation();
            this.isPaused = true;
            this.updatePauseIndicator();
        }

        // Go back in history if available
        if (this.slideHistory.length > 0) {
            this.currentIndex = this.slideHistory.pop();
            this.showSlide(this.currentIndex);
        } else {
            console.log('No previous slide in history');
        }
    }

    async refreshData() {
        try {
            console.log('Refreshing data files...');

            // Reload all content from YAML files
            const [businesses, facts, images, events] = await Promise.all([
                this.loadYAML('data/businesses.yaml'),
                this.loadYAML('data/town-facts.yaml'),
                this.loadYAML('data/town-images.yaml'),
                this.loadYAML('data/events.yaml').catch(() => [])
            ]);

            // Rebuild slide playlist
            this.buildPlaylist(businesses, facts, images, events || []);

            // Clear existing slides from DOM
            this.slideContainer.innerHTML = '';

            // Re-render slides with new data
            this.renderSlides();

            // Reset slide stats to give new/updated slides fair chance
            this.slideStats.clear();

            // Reset to first slide and continue rotation
            this.currentIndex = 0;
            this.showSlide(0);

            console.log(`Data refresh complete - loaded ${this.slides.length} slides`);

        } catch (error) {
            console.error('Failed to refresh data:', error);
        }
    }

    async loadYAML(url) {
        // Add cache busting to ensure fresh data
        const cacheBuster = `?v=${Date.now()}`;
        const response = await fetch(url + cacheBuster);
        const text = await response.text();
        return jsyaml.load(text);
    }

    buildPlaylist(businesses, facts, images, events) {
        // Separate major events from daily events
        const majorEvents = events.filter(e => e.is_major);
        const dailyEvents = events.filter(e => !e.is_major);

        // Combine all content with type tags and weights
        const allContent = [
            ...businesses.map(b => ({ ...b, type: 'business', weight: this.weights.business })),
            ...facts.map(f => ({ ...f, type: 'fact', weight: this.weights.fact })),
            ...images.map(i => ({ ...i, type: 'image', weight: this.weights.image })),
            ...majorEvents.map(e => ({ ...e, type: 'major-event', weight: this.calculateEventWeight(e) }))
        ];

        // Add daily events slide only if there are events today
        const todaysEvents = this.getTodaysEvents(dailyEvents);
        if (todaysEvents.length > 0) {
            allContent.push({
                type: 'daily-events',
                events: todaysEvents,
                weight: this.weights.dailyEvents
            });
        }

        // Filter out slides with weight 0 (e.g., far-out events that aren't major)
        const filteredContent = allContent.filter(slide => slide.weight > 0);

        // With score-based selection, we don't need to duplicate slides
        // The weight is factored into the selection probability
        this.slides = filteredContent;

        // Randomly assign animations
        this.slides = this.slides.map(slide => ({
            ...slide,
            animate: Math.random() < this.animationProbability
        }));
    }

    calculateEventWeight(event) {
        // Calculate weight based on days until event
        const now = new Date();
        now.setHours(0, 0, 0, 0);

        const eventDate = new Date(event.time);
        eventDate.setHours(0, 0, 0, 0);

        const daysUntil = Math.floor((eventDate - now) / (1000 * 60 * 60 * 24));

        // Weight based on proximity (using centralized weights config)
        if (daysUntil < 0) {
            // Past event (shouldn't happen, but just in case)
            return 0;
        } else if (daysUntil <= 7) {
            return this.weights.event.next7Days;
        } else if (daysUntil <= 30) {
            return this.weights.event.days8to30;
        } else {
            // 31+ days: only show if major event
            return event.is_major ? this.weights.event.major : this.weights.event.days31Plus;
        }
    }

    getTodaysEvents(events) {
        // Filter events happening today
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        return events.filter(event => {
            const eventDate = new Date(event.time);
            return eventDate >= today && eventDate < tomorrow;
        });
    }

    renderSlides() {
        this.slides.forEach((slide, index) => {
            const slideElement = document.createElement('div');
            slideElement.className = `slide ${slide.type}`;

            // Set background image if provided
            if (slide.background_image) {
                slideElement.style.backgroundImage = `url('${slide.background_image}')`;
            }

            slideElement.innerHTML = this.getSlideHTML(slide);
            this.slideContainer.appendChild(slideElement);
        });
    }

    getSlideIndexFromHash() {
        // Check if there's a hash in the URL
        const hash = window.location.hash.slice(1); // Remove the '#'

        if (!hash) {
            return 0;
        }

        // Try to find a slide that matches the hash
        for (let i = 0; i < this.slides.length; i++) {
            const slide = this.slides[i];
            const slideName = slide.name || slide.title || '';
            const slideSlug = this.slugify(slideName);

            if (slideSlug === hash) {
                console.log(`Found slide "${slideName}" at index ${i} for hash #${hash}`);
                return i;
            }
        }

        console.log(`No slide found for hash #${hash}, starting at beginning`);
        return 0;
    }

    getSlideHTML(slide) {
        // Generate primary image HTML if available
        const primaryImageHTML = slide.primary_image ?
            `<div class="primary-image-container">
                <img src="${slide.primary_image}" alt="${slide.title || slide.name || 'Image'}"
                     onerror="this.parentElement.style.display='none'">
             </div>` : '';

        // For businesses, add map overlay if available
        const mapOverlayHTML = (slide.type === 'business' && slide.map_image) ?
            `<div class="map-overlay">
                <img src="${slide.map_image}" alt="Location map"
                     onerror="this.parentElement.style.display='none'">
             </div>` : '';

        // For businesses and major events, add QR code section if available
        const qrCodeHTML = ((slide.type === 'business' || slide.type === 'major-event') && slide.qr_code) ?
            `<div class="qr-section">
                <img src="${slide.qr_code}" alt="Scan for more info"
                     onerror="this.parentElement.style.display='none'">
                <div class="qr-label">${slide.type === 'business' ? 'Scan to Visit' : 'Scan for Details'}</div>
             </div>` : '';

        switch (slide.type) {
            case 'business':
                return `
                    <h2 class="business-name">${slide.name}</h2>
                    <div class="business-image-wrapper">
                        ${primaryImageHTML}
                        ${mapOverlayHTML}
                    </div>
                    <div class="business-content">
                        ${qrCodeHTML}
                        <div class="business-text">
                            <div class="business-tagline">${slide.tagline}</div>
                            ${slide.address ? `<div class="business-address">${slide.address}</div>` : ''}
                            ${slide.phone ? `<div class="business-phone">${slide.phone}</div>` : ''}
                            <div class="business-cta">${slide.cta || 'Visit us today!'}</div>
                        </div>
                    </div>
                `;

            case 'fact':
                return `
                    ${primaryImageHTML}
                    <h2>Did You Know?</h2>
                    <div class="fact-content">${slide.content}</div>
                `;

            case 'image':
                return `
                    <div class="image-container">
                        ${slide.primary_image ?
                            `<img src="${slide.primary_image}" alt="${slide.title}" onerror="this.parentElement.innerHTML='<div class=\\'image-placeholder\\'><div class=\\'placeholder-text\\'>Image: ${slide.title}</div></div>'">` :
                            `<div class="image-placeholder"><div class="placeholder-text">Image: ${slide.title}</div></div>`
                        }
                        <div class="image-info">
                            <div class="image-title">${slide.title}</div>
                            <div class="image-caption">${slide.caption || ''}</div>
                        </div>
                    </div>
                `;

            case 'major-event':
                const eventTime = new Date(slide.time);
                const timeStr = eventTime.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
                const dateStr = eventTime.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

                // Use event image or default calendar image
                const eventImage = slide.image || 'images/primary/calendar.jpg';
                const eventImageHTML = `<div class="primary-image-container">
                    <img src="${eventImage}" alt="${slide.title}"
                         onerror="this.src='images/backgrounds/community-gathering.jpg'">
                 </div>`;

                return `
                    ${eventImageHTML}
                    <div class="event-content">
                        ${qrCodeHTML}
                        <div class="event-text">
                            <h2>${slide.title}</h2>
                            <div class="event-details">${dateStr} • ${timeStr}</div>
                            <div class="event-details">${slide.location}</div>
                            ${slide.description ? `<div class="event-description">${slide.description}</div>` : ''}
                        </div>
                    </div>
                `;

            case 'daily-events':
                if (!slide.events || slide.events.length === 0) {
                    return `
                        <h2>Today's Events</h2>
                        <div class="daily-events-empty">No events scheduled for today</div>
                    `;
                }

                const eventsListHTML = slide.events.map(event => {
                    const eventTime = new Date(event.time);
                    const timeStr = eventTime.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });

                    return `
                        <div class="daily-event-item">
                            <div class="daily-event-time">${timeStr}</div>
                            <div class="daily-event-info">
                                <div class="daily-event-title">${event.title}</div>
                                <div class="daily-event-location">${event.location}</div>
                            </div>
                        </div>
                    `;
                }).join('');

                return `
                    <h2>Today's Events</h2>
                    <div class="daily-events-list">
                        ${eventsListHTML}
                    </div>
                `;

            default:
                return '<p>Unknown content type</p>';
        }
    }

    showSlide(index) {
        const allSlides = this.slideContainer.querySelectorAll('.slide');
        allSlides.forEach((slide, i) => {
            if (i === index) {
                slide.classList.add('active');
                // Add zoom animation class based on slide data
                if (this.slides[i].animate) {
                    slide.classList.add('animate-zoom');
                }
            } else {
                slide.classList.remove('active', 'animate-zoom');
            }
        });
    }

    startRotation() {
        // Don't start if already running, paused, or if hash is present
        if (this.rotationInterval || this.isPaused || window.location.hash) {
            return;
        }

        this.rotationInterval = setInterval(() => {
            // Add current slide to history before moving to next
            this.slideHistory.push(this.currentIndex);

            // Keep only last 10 slides in history
            if (this.slideHistory.length > 10) {
                this.slideHistory.shift();
            }

            // Use score-based selection instead of linear playback
            this.currentIndex = this.selectNextSlide();

            // Periodically reset stats to allow slides to "recover" from being shown too much
            // Reset after each slide has been shown ~3 times on average
            const totalShown = Array.from(this.slideStats.values()).reduce((sum, val) => sum + val, 0);
            if (totalShown >= this.slides.length * 3) {
                console.log('Resetting slide statistics to allow fresh rotation');
                this.slideStats.clear();
            }

            this.showSlide(this.currentIndex);
        }, this.slideDuration);
    }

    stopRotation() {
        if (this.rotationInterval) {
            clearInterval(this.rotationInterval);
            this.rotationInterval = null;
        }
    }

}

// Initialize when page loads (or immediately if already loaded)
function initKiosk() {
    const kiosk = new KioskSlideshow();
    kiosk.init();
}

if (document.readyState === 'loading') {
    // DOM not ready yet, wait for it
    document.addEventListener('DOMContentLoaded', initKiosk);
} else {
    // DOM is already ready, init immediately
    initKiosk();
}
