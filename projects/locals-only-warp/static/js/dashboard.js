class DashboardApp {
    constructor() {
        this.map = null;
        this.markers = [];
        this.infoWindow = null;
        this.currentCategory = 'restaurants';
        this.recommendations = [];
        this.selectedRecommendation = null;
        this.userLocation = window.USER_LOCATION || null;
        this.userPreferences = this.getUserPreferences();
        this.starredCategories = [];
        this.modalAnimating = false; // Fix for double flicker
        
        this.init();
    }
    
    getUserPreferences() {
        try {
            const stored = sessionStorage.getItem('userPreferences');
            const preferences = stored ? JSON.parse(stored) : [];
            console.log('📥 User preferences loaded from sessionStorage:', preferences);
            return preferences;
        } catch (error) {
            console.error('❌ Error loading preferences from sessionStorage:', error);
            return [];
        }
    }
    
    async loadStarredCategories() {
        try {
            console.log('🔄 Loading starred categories from backend...');
            
            // First, try to sync sessionStorage preferences to backend if they exist
            if (this.userPreferences.length > 0) {
                console.log('🔄 Syncing sessionStorage preferences to backend...');
                await this.syncPreferencesToBackend();
            }
            
            const response = await fetch('/api/get-preferences');
            const data = await response.json();
            if (data.success) {
                this.starredCategories = data.starred_categories || [];
                console.log('✅ Starred categories loaded from backend:', this.starredCategories);
                
                // If backend is empty but we have sessionStorage preferences, use those and sync
                if (this.starredCategories.length === 0 && this.userPreferences.length > 0) {
                    console.log('🔄 Backend empty, syncing sessionStorage preferences...');
                    this.starredCategories = [...this.userPreferences];
                    await this.syncPreferencesToBackend();
                }
            } else {
                console.warn('⚠️ Failed to load starred categories from backend:', data.error);
                // Fallback to sessionStorage preferences
                this.starredCategories = [...this.userPreferences];
            }
        } catch (error) {
            console.error('❌ Error loading starred categories:', error);
            // Fallback to sessionStorage preferences
            this.starredCategories = [...this.userPreferences];
        }
    }
    
    async syncPreferencesToBackend() {
        try {
            const response = await fetch('/api/update-preferences', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    starred_categories: this.userPreferences
                })
            });
            
            const data = await response.json();
            if (data.success) {
                console.log('✅ SessionStorage preferences synced to backend');
                this.starredCategories = data.starred_categories || this.userPreferences;
            } else {
                console.warn('⚠️ Failed to sync preferences to backend:', data.error);
            }
        } catch (error) {
            console.error('❌ Error syncing preferences to backend:', error);
        }
    }
    
    async init() {
        console.log('🚀 Initializing dashboard app...');
        await this.loadStarredCategories();
        this.setupCategoryButtons();
        this.setupLocationEditor();
        this.setupPreferredCategories();
        this.loadInitialRecommendations();
        console.log('✅ Dashboard app initialized');
    }
    
    setupLocationEditor() {
        const locationDisplay = document.getElementById('locationDisplay');
        const locationEditor = document.getElementById('locationEditor');
        const locationInput = document.getElementById('locationInput');
        
        if (locationDisplay) {
            locationDisplay.addEventListener('click', () => {
                this.startLocationEdit();
            });
        }
        
        if (locationInput) {
            locationInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    this.saveLocation();
                } else if (e.key === 'Escape') {
                    this.cancelLocationEdit();
                }
            });
        }
    }
    
    startLocationEdit() {
        const locationDisplay = document.getElementById('locationDisplay');
        const locationEditor = document.getElementById('locationEditor');
        const locationInput = document.getElementById('locationInput');
        
        if (locationDisplay && locationEditor && locationInput) {
            locationDisplay.classList.add('hidden');
            locationEditor.classList.remove('hidden');
            locationInput.focus();
            locationInput.value = this.userLocation?.zip_code || '';
        }
    }
    
    cancelLocationEdit() {
        const locationDisplay = document.getElementById('locationDisplay');
        const locationEditor = document.getElementById('locationEditor');
        
        if (locationDisplay && locationEditor) {
            locationDisplay.classList.remove('hidden');
            locationEditor.classList.add('hidden');
        }
    }
    
    async saveLocation() {
        const locationInput = document.getElementById('locationInput');
        const newZipCode = locationInput?.value.trim();
        
        if (!newZipCode) {
            this.showLocationError('Please enter a zip code');
            return;
        }
        
        // Validate zip code format
        const zipClean = newZipCode.replace('-', '').replace(' ', '');
        if (!(zipClean.match(/^\d{5}$/) || zipClean.match(/^\d{9}$/))) {
            this.showLocationError('Please enter a valid US zip code');
            return;
        }
        
        try {
            // Show loading state
            locationInput.disabled = true;
            
            // Get location details from zip code
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    zip_code: newZipCode,
                    category: 'restaurants' // Just to get location info
                })
            });
            
            const data = await response.json();
            
            if (data.success && data.location) {
                // Update user location
                this.userLocation = data.location;
                window.USER_LOCATION = data.location;
                
                // Update session
                await fetch('/api/set-location', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data.location)
                });
                
                // Update display
                this.updateLocationDisplay();
                this.cancelLocationEdit();
                
                // Reload recommendations for current category
                await this.loadRecommendations(this.currentCategory);
                
                // Update map center
                if (this.map) {
                    this.map.setCenter({
                        lat: data.location.latitude,
                        lng: data.location.longitude
                    });
                }
                
                this.showLocationSuccess('Location updated successfully!');
            } else {
                this.showLocationError(data.error || 'Invalid zip code');
            }
        } catch (error) {
            console.error('Error updating location:', error);
            this.showLocationError('Failed to update location');
        } finally {
            locationInput.disabled = false;
        }
    }
    
    updateLocationDisplay() {
        const locationText = document.querySelector('.location-text');
        if (locationText && this.userLocation) {
            locationText.textContent = `${this.userLocation.city}, ${this.userLocation.state} ${this.userLocation.zip_code}`;
        }
    }
    
    showLocationSuccess(message) {
        const locationInput = document.getElementById('locationInput');
        if (locationInput) {
            locationInput.classList.add('location-success');
            setTimeout(() => {
                locationInput.classList.remove('location-success');
            }, 2000);
        }
        console.log('✅', message);
    }
    
    showLocationError(message) {
        const locationInput = document.getElementById('locationInput');
        if (locationInput) {
            locationInput.classList.add('location-error');
            setTimeout(() => {
                locationInput.classList.remove('location-error');
            }, 2000);
        }
        console.error('❌', message);
    }
    
    setupCategoryButtons() {
        const categoryButtons = document.querySelectorAll('.category-bubble');
        categoryButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                const category = e.currentTarget.dataset.category;
                this.switchCategory(category);
            });
        });
        console.log(`Set up ${categoryButtons.length} category button listeners`);
    }
    
    setupPreferredCategories() {
        if (this.starredCategories.length > 0) {
            // Set the first starred category as the default category
            this.currentCategory = this.starredCategories[0];
            
            // Update the UI to show starred categories first
            this.reorderCategoryButtons();
            
            // Set the active category button
            this.updateActiveCategoryButton(this.currentCategory);
            
            console.log(`✅ Set preferred category: ${this.currentCategory}`);
        } else {
            // No starred categories, just update display
            this.reorderCategoryButtons();
        }
    }
    
    reorderCategoryButtons() {
        const categoryGrid = document.querySelector('.category-grid');
        if (!categoryGrid) return;
        
        const allButtons = Array.from(categoryGrid.querySelectorAll('.category-bubble'));
        
        // Sort buttons: starred categories first, then others
        allButtons.sort((a, b) => {
            const categoryA = a.dataset.category;
            const categoryB = b.dataset.category;
            
            const isStarredA = this.starredCategories.includes(categoryA);
            const isStarredB = this.starredCategories.includes(categoryB);
            
            if (isStarredA && !isStarredB) return -1;
            if (!isStarredA && isStarredB) return 1;
            
            // For starred categories, maintain the order from starredCategories array
            if (isStarredA && isStarredB) {
                return this.starredCategories.indexOf(categoryA) - this.starredCategories.indexOf(categoryB);
            }
            
            return 0;
        });
        
        // Add visual indicators for starred categories
        allButtons.forEach(button => {
            const category = button.dataset.category;
            
            // Remove existing star if any
            const existingStar = button.querySelector('.preference-star');
            if (existingStar) {
                existingStar.remove();
            }
            
            if (this.starredCategories.includes(category)) {
                button.classList.add('preferred');
                // Add a small star indicator
                const star = document.createElement('i');
                star.className = 'fas fa-star preference-star';
                star.style.fontSize = '10px';
                star.style.marginLeft = '4px';
                star.style.color = 'var(--primary-gold)';
                star.style.textShadow = '0 1px 2px rgba(0, 0, 0, 0.1)';
                button.appendChild(star);
                console.log(`⭐ Added star to ${category} button`);
            } else {
                button.classList.remove('preferred');
            }
        });
        
        // Re-append buttons in new order
        categoryGrid.innerHTML = '';
        allButtons.forEach(button => categoryGrid.appendChild(button));
        
        console.log('✅ Category buttons reordered with starred categories first');
    }
    
    switchCategory(category) {
        console.log(`Switching to category: ${category}`);
        this.currentCategory = category;
        this.updateActiveCategoryButton(category);
        this.loadRecommendations(category);
    }
    
    updateActiveCategoryButton(category) {
        // Remove active class from all buttons
        document.querySelectorAll('.category-bubble').forEach(btn => {
            btn.classList.remove('active');
        });
        
        // Add active class to selected button
        const activeButton = document.querySelector(`[data-category="${category}"]`);
        if (activeButton) {
            activeButton.classList.add('active');
        }
    }
    
    async loadInitialRecommendations() {
        if (!this.userLocation || !this.userLocation.zip_code) {
            console.error('No user location available');
            this.showError('Location not available. Please refresh the page.');
            return;
        }
        
        await this.loadRecommendations(this.currentCategory);
    }
    
    async loadRecommendations(category) {
        console.log(`Loading recommendations for ${category}`);
        console.log('User location:', this.userLocation);
        
        if (!this.userLocation || !this.userLocation.zip_code) {
            console.error('No user location available');
            this.showError('Location not available. Please refresh the page.');
            return;
        }
        
        // Show loading state
        this.showLoadingState();
        
        try {
            console.log('Making request to /api/recommendations...');
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    zip_code: this.userLocation.zip_code,
                    category: category
                })
            });
            
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Received recommendations:', data);
            
            if (data.success) {
                this.recommendations = data.recommendations || [];
                this.updateRecommendationsList();
                this.updateMapMarkers();
                console.log(`Loaded ${this.recommendations.length} recommendations`);
            } else {
                throw new Error(data.error || 'Failed to load recommendations');
            }
        } catch (error) {
            console.error('Error loading recommendations:', error);
            this.showError('Unable to load recommendations. Please try again.');
        } finally {
            this.hideLoadingState();
        }
    }
    
    showLoadingState() {
        const listContainer = document.getElementById('recommendationsList');
        if (listContainer) {
            listContainer.innerHTML = `
                <div class="loading-state" style="text-align: center; padding: 48px 24px;">
                    <div class="spinner"></div>
                    <p style="color: var(--gray-600); margin-top: 16px;">Finding local recommendations...</p>
                </div>
            `;
        }
    }
    
    hideLoadingState() {
        // Loading state will be replaced by updateRecommendationsList
    }
    
    showError(message) {
        const listContainer = document.getElementById('recommendationsList');
        if (listContainer) {
            listContainer.innerHTML = `
                <div class="no-results" style="text-align: center; padding: 48px 24px;">
                    <i class="fas fa-exclamation-triangle" style="font-size: 48px; margin-bottom: 16px; color: var(--error);"></i>
                    <p style="color: var(--gray-600); margin-bottom: 16px;">${message}</p>
                    <button class="btn btn-primary btn-sm" onclick="window.dashboardApp.loadRecommendations('${this.currentCategory}')">
                        <i class="fas fa-refresh"></i>
                        Try Again
                    </button>
                </div>
            `;
        }
    }
    
    updateRecommendationsList() {
        const listContainer = document.getElementById('recommendationsList');
        if (!listContainer) return;
        
        if (this.recommendations.length === 0) {
            listContainer.innerHTML = `
                <div class="no-results" style="text-align: center; padding: 48px 24px;">
                    <i class="fas fa-search" style="font-size: 48px; margin-bottom: 16px; color: var(--gray-300);"></i>
                    <p style="color: var(--gray-500); margin-bottom: 16px;">No ${this.currentCategory} found in your area.</p>
                    <button class="btn btn-primary btn-sm" onclick="window.dashboardApp.loadRecommendations('${this.currentCategory}')">
                        <i class="fas fa-refresh"></i>
                        Try Another Category
                    </button>
                </div>
            `;
            return;
        }
        
        const html = this.recommendations.map((rec, index) => {
            const stars = this.generateStars(rec.rating);
            return `
                <div class="recommendation-card" data-index="${index}" onclick="window.dashboardApp.selectRecommendation(${index})">
                    <div class="rec-header">
                        <div class="rec-title">${this.escapeHtml(rec.name)}</div>
                        <div class="rec-type">${this.escapeHtml(rec.type)}</div>
                    </div>
                    <div class="rec-rating">
                        <div class="stars">${stars}</div>
                        <span class="rating-text">${rec.rating || 'N/A'}</span>
                    </div>
                    <div class="rec-address">${this.escapeHtml(rec.address)}</div>
                    ${rec.local_focus ? '<div class="local-badge">Local Favorite</div>' : ''}
                </div>
            `;
        }).join('');
        
        listContainer.innerHTML = html;
        
        // Add click event listeners
        listContainer.querySelectorAll('.recommendation-card').forEach(card => {
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const index = parseInt(e.currentTarget.dataset.index);
                    this.selectRecommendation(index);
                }
            });
            card.setAttribute('tabindex', '0');
        });
    }
    
    selectRecommendation(index) {
        console.log(`Selecting recommendation ${index}`);
        
        // Update UI
        document.querySelectorAll('.recommendation-card').forEach(card => {
            card.classList.remove('active');
        });
        
        const selectedCard = document.querySelector(`[data-index="${index}"]`);
        if (selectedCard) {
            selectedCard.classList.add('active');
        }
        
        const recommendation = this.recommendations[index];
        if (recommendation && this.map && recommendation.latitude && recommendation.longitude) {
            // Pan to location on map
            const position = { lat: recommendation.latitude, lng: recommendation.longitude };
            this.map.panTo(position);
            this.map.setZoom(15);
            
            // Highlight marker
            if (this.markers[index]) {
                this.markers[index].setAnimation(google.maps.Animation.BOUNCE);
                setTimeout(() => this.markers[index].setAnimation(null), 2000);
            }
        }
        
        // Show details (you can implement a modal here)
        this.selectedRecommendation = recommendation;
        console.log('Selected recommendation:', recommendation);
    }
    
    updateMapMarkers() {
        if (!this.map) return;
        
        // Clear existing markers
        this.markers.forEach(marker => marker.setMap(null));
        this.markers = [];
        
        // Add new markers
        this.recommendations.forEach((rec, index) => {
            if (rec.latitude && rec.longitude) {
                const marker = new google.maps.Marker({
                    position: { lat: rec.latitude, lng: rec.longitude },
                    map: this.map,
                    title: rec.name,
                    icon: {
                        url: 'data:image/svg+xml,' + encodeURIComponent(`
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="32" height="32">
                                <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z" 
                                      fill="#F5BB00" stroke="#1B1B1E" stroke-width="1"/>
                                <circle cx="12" cy="9" r="2.5" fill="#1B1B1E"/>
                            </svg>
                        `),
                        scaledSize: new google.maps.Size(32, 32),
                        anchor: new google.maps.Point(16, 32)
                    }
                });
                
                // Info window
                const infoWindow = new google.maps.InfoWindow({
                    content: `
                        <div class="info-window">
                            <h4>${this.escapeHtml(rec.name)}</h4>
                            <div class="info-rating">
                                <div class="stars">${this.generateStars(rec.rating)}</div>
                                <span>${rec.rating || 'N/A'}</span>
                            </div>
                            <p>${this.escapeHtml(rec.address)}</p>
                            <button class="info-btn" onclick="window.dashboardApp.selectRecommendation(${index})">
                                View Details
                            </button>
                        </div>
                    `
                });
                
                marker.addListener('click', () => {
                    // Close other info windows
                    this.markers.forEach(m => {
                        if (m.infoWindow) {
                            m.infoWindow.close();
                        }
                    });
                    
                    infoWindow.open(this.map, marker);
                    this.selectRecommendation(index);
                });
                
                marker.infoWindow = infoWindow;
                this.markers.push(marker);
            }
        });
        
        // Adjust map bounds if we have markers
        if (this.markers.length > 0) {
            const bounds = new google.maps.LatLngBounds();
            
            // Include user location
            if (this.userLocation && this.userLocation.latitude && this.userLocation.longitude) {
                bounds.extend({ lat: this.userLocation.latitude, lng: this.userLocation.longitude });
            }
            
            // Include all markers
            this.markers.forEach(marker => {
                bounds.extend(marker.getPosition());
            });
            
            this.map.fitBounds(bounds);
            
            // Ensure minimum zoom level
            google.maps.event.addListenerOnce(this.map, 'bounds_changed', () => {
                if (this.map.getZoom() > 15) {
                    this.map.setZoom(15);
                }
            });
        }
    }
    
    generateStars(rating) {
        if (!rating || rating === 0) {
            return '<span class="star empty">★</span>'.repeat(5);
        }
        
        const fullStars = Math.floor(rating);
        const emptyStars = 5 - fullStars;
        
        return '<span class="star">★</span>'.repeat(fullStars) + 
               '<span class="star empty">★</span>'.repeat(emptyStars);
    }
    
    escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
}

// Global functions for HTML onclick handlers
// Location editing functions
function saveLocation() {
    console.log('🔄 saveLocation called');
    if (window.dashboardApp) {
        window.dashboardApp.saveLocation();
    } else {
        console.error('❌ Dashboard app not available');
    }
}

function cancelLocationEdit() {
    console.log('🔄 cancelLocationEdit called');
    if (window.dashboardApp) {
        window.dashboardApp.cancelLocationEdit();
    } else {
        console.error('❌ Dashboard app not available');
    }
}

// Categories modal functions - Fixed to prevent double flicker
function openCategoriesModal() {
    console.log('🔄 openCategoriesModal called');
    
    // Prevent opening if already animating
    if (window.dashboardApp && window.dashboardApp.modalAnimating) {
        console.log('⚠️ Modal already animating, ignoring request');
        return;
    }
    
    console.log('Dashboard app available:', !!window.dashboardApp);
    console.log('Starred categories:', window.dashboardApp?.starredCategories);
    
    const modal = document.getElementById('categoriesModal');
    console.log('Modal element found:', !!modal);
    
    if (modal && window.dashboardApp) {
        // Set animating flag to prevent double calls
        window.dashboardApp.modalAnimating = true;
        
        // Update modal state before showing
        updateCategoriesModal();
        
        // Show modal with single animation
        modal.classList.remove('hidden');
        
        // Reset animating flag after animation completes
        setTimeout(() => {
            window.dashboardApp.modalAnimating = false;
        }, 300);
        
        console.log('✅ Modal opened');
    } else {
        console.error('❌ Modal element or dashboard app not found');
    }
}

function closeCategoriesModal() {
    console.log('🔄 closeCategoriesModal called');
    const modal = document.getElementById('categoriesModal');
    if (modal) {
        modal.classList.add('hidden');
        console.log('✅ Modal closed');
    }
}

function updateCategoriesModal() {
    console.log('🔄 updateCategoriesModal called');
    const starredCategories = window.dashboardApp?.starredCategories || [];
    console.log('Current starred categories:', starredCategories);
    
    // Update toggle states
    document.querySelectorAll('.category-toggle').forEach(toggle => {
        const category = toggle.dataset.category;
        const isStarred = starredCategories.includes(category);
        
        const starBtn = toggle.querySelector('.category-star-btn');
        
        if (isStarred) {
            toggle.classList.add('starred');
            if (starBtn) starBtn.classList.add('starred');
        } else {
            toggle.classList.remove('starred');
            if (starBtn) starBtn.classList.remove('starred');
        }
        
        console.log(`Category ${category}: starred=${isStarred}`);
    });
}

function toggleCategoryStar(category) {
    console.log('🔄 toggleCategoryStar called for:', category);
    if (!window.dashboardApp) {
        console.error('❌ Dashboard app not available');
        return;
    }
    
    const index = window.dashboardApp.starredCategories.indexOf(category);
    
    if (index > -1) {
        // Remove from starred
        window.dashboardApp.starredCategories.splice(index, 1);
        console.log(`⭐ Removed ${category} from starred`);
    } else {
        // Add to starred
        window.dashboardApp.starredCategories.push(category);
        console.log(`⭐ Added ${category} to starred`);
    }
    
    console.log('Updated starred categories:', window.dashboardApp.starredCategories);
    
    // Update modal display immediately
    updateCategoriesModal();
}

async function saveCategoryPreferences() {
    console.log('🔄 saveCategoryPreferences called');
    if (!window.dashboardApp) {
        console.error('❌ Dashboard app not available');
        return;
    }
    
    console.log('Saving starred categories:', window.dashboardApp.starredCategories);
    
    try {
        const response = await fetch('/api/update-preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                starred_categories: window.dashboardApp.starredCategories
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update local state
            window.dashboardApp.starredCategories = data.starred_categories || [];
            
            // Also update sessionStorage to keep in sync
            try {
                sessionStorage.setItem('userPreferences', JSON.stringify(window.dashboardApp.starredCategories));
                console.log('✅ SessionStorage updated with saved preferences');
            } catch (error) {
                console.warn('⚠️ Failed to update sessionStorage:', error);
            }
            
            // Reorder category buttons to show visual changes
            window.dashboardApp.reorderCategoryButtons();
            
            // Close modal
            closeCategoriesModal();
            
            console.log('✅ Category preferences saved successfully');
        } else {
            console.error('❌ Failed to save preferences:', data.error);
        }
    } catch (error) {
        console.error('❌ Error saving preferences:', error);
    }
}

function initMap() {
    if (!window.USER_LOCATION || !window.USER_LOCATION.latitude || !window.USER_LOCATION.longitude) {
        console.error('No user location data available for map initialization');
        return;
    }

    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 13,
        center: new google.maps.LatLng(window.USER_LOCATION.latitude, window.USER_LOCATION.longitude),
        styles: [
            {
                featureType: 'poi',
                elementType: 'labels',
                stylers: [{ visibility: 'off' }]
            }
        ],
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true
    });

    // Add user location marker
    new google.maps.Marker({
        position: new google.maps.LatLng(window.USER_LOCATION.latitude, window.USER_LOCATION.longitude),
        map: map,
        title: 'Your Location',
        icon: {
            url: 'data:image/svg+xml,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24">
                    <circle cx="12" cy="12" r="8" fill="#F5BB00" stroke="#1B1B1E" stroke-width="2"/>
                    <circle cx="12" cy="12" r="3" fill="#1B1B1E"/>
                </svg>
            `),
            scaledSize: new google.maps.Size(24, 24),
            anchor: new google.maps.Point(12, 12)
        }
    });

    // Connect the map to the existing dashboard app
    if (window.dashboardApp) {
        window.dashboardApp.map = map;
        window.dashboardApp.infoWindow = new google.maps.InfoWindow();
        console.log('✅ Map connected to dashboard app');
        // Update markers for current recommendations
        window.dashboardApp.updateMapMarkers();
    } else {
        console.warn('Dashboard app not found when initializing map');
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 Dashboard page loaded, initializing app...');
    
    // Initialize dashboard app immediately, don't wait for Google Maps
    if (!window.dashboardApp) {
        window.dashboardApp = new DashboardApp();
        // The init method is now async and will handle everything in the right order
        console.log('✅ Dashboard app initialized and available globally');
    }
});
