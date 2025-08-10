class DashboardApp {
    constructor() {
        this.map = null;
        this.markers = [];
        this.infoWindow = null;
        this.currentCategory = 'restaurants'; // Default to restaurants instead of general
        this.recommendations = [];
        this.selectedRecommendation = null;
        this.userLocation = window.USER_LOCATION || null;
        
        this.loadInitialRecommendations();
    }
    
    async loadInitialRecommendations() {
        if (!this.userLocation || !this.userLocation.zip_code) {
            console.error('No user location available');
            return;
        }
        
        await this.loadRecommendations(this.currentCategory);
    }
    
    async loadRecommendations(category) {
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.classList.remove('hidden');
        
        try {
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
            
            const data = await response.json();
            
            if (data.success) {
                this.recommendations = data.recommendations || [];
                this.updateRecommendationsList();
                this.updateMapMarkers();
            } else {
                console.error('Failed to load recommendations:', data.error);
                this.showError(data.error);
            }
        } catch (error) {
            console.error('Error loading recommendations:', error);
            this.showError('Failed to load recommendations. Please try again.');
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    }
    
    switchCategory(category) {        
        this.currentCategory = category;
        this.loadRecommendations(category);
    }
    
    updateRecommendationsList() {
        const listContainer = document.getElementById('recommendationsList');
        
        if (this.recommendations.length === 0) {
            listContainer.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <p>No recommendations found for this category.</p>
                </div>
            `;
            return;
        }
        
        const html = this.recommendations.map((rec, index) => {
            const stars = this.generateStarsHTML(rec.rating || 0);
            return `
                <div class="recommendation-card" data-index="${index}" onclick="selectRecommendation(${index})">
                    <div class="rec-header">
                        <h4 class="rec-title">${rec.name || 'Unknown'}</h4>
                        <span class="rec-type">${rec.type || 'Place'}</span>
                    </div>
                    <div class="rec-rating">
                        <div class="stars">${stars}</div>
                        <span class="rating-text">${rec.rating ? rec.rating.toFixed(1) : 'N/A'}</span>
                    </div>
                    <p class="rec-address">${rec.address || 'Address not available'}</p>
                </div>
            `;
        }).join('');
        
        listContainer.innerHTML = html;
    }
    
    generateStarsHTML(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);
        
        let starsHTML = '';
        
        // Full stars
        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<i class="fas fa-star star"></i>';
        }
        
        // Half star
        if (hasHalfStar) {
            starsHTML += '<i class="fas fa-star-half-alt star"></i>';
        }
        
        // Empty stars
        for (let i = 0; i < emptyStars; i++) {
            starsHTML += '<i class="far fa-star star empty"></i>';
        }
        
        return starsHTML;
    }
    
    selectRecommendation(index) {
        // Update visual selection
        document.querySelectorAll('.recommendation-card').forEach(card => {
            card.classList.remove('active');
        });
        
        document.querySelector(`[data-index="${index}"]`).classList.add('active');
        
        this.selectedRecommendation = this.recommendations[index];
        
        // Center map on selected recommendation
        if (this.map && this.selectedRecommendation.latitude && this.selectedRecommendation.longitude) {
            const position = new google.maps.LatLng(
                this.selectedRecommendation.latitude,
                this.selectedRecommendation.longitude
            );
            this.map.panTo(position);
            this.map.setZoom(16);
            
            // Show info window
            const marker = this.markers[index];
            if (marker && this.infoWindow) {
                this.infoWindow.setContent(`
                    <div class="info-window">
                        <h4>${this.selectedRecommendation.name}</h4>
                        <p>${this.selectedRecommendation.type}</p>
                        <div class="info-rating">
                            ${this.generateStarsHTML(this.selectedRecommendation.rating || 0)}
                            <span>${this.selectedRecommendation.rating ? this.selectedRecommendation.rating.toFixed(1) : 'N/A'}</span>
                        </div>
                        <button onclick="showRecommendationModal(${index})" class="info-btn">
                            View Details
                        </button>
                    </div>
                `);
                this.infoWindow.open(this.map, marker);
            }
        }
    }
    
    updateMapMarkers() {
        // Clear existing markers
        this.markers.forEach(marker => marker.setMap(null));
        this.markers = [];
        
        if (!this.map) return;
        
        // Add markers for recommendations
        this.recommendations.forEach((rec, index) => {
            if (rec.latitude && rec.longitude) {
                const marker = new google.maps.Marker({
                    position: new google.maps.LatLng(rec.latitude, rec.longitude),
                    map: this.map,
                    title: rec.name,
                    icon: {
                        url: this.getMarkerIcon(this.currentCategory),
                        scaledSize: new google.maps.Size(32, 32),
                        anchor: new google.maps.Point(16, 32)
                    }
                });
                
                // Add click listener
                marker.addListener('click', () => {
                    this.selectRecommendation(index);
                });
                
                this.markers.push(marker);
            }
        });
        
        // Fit map to show all markers
        if (this.markers.length > 0) {
            const bounds = new google.maps.LatLngBounds();
            this.markers.forEach(marker => {
                bounds.extend(marker.getPosition());
            });
            
            // Also include user location
            if (this.userLocation && this.userLocation.latitude && this.userLocation.longitude) {
                bounds.extend(new google.maps.LatLng(this.userLocation.latitude, this.userLocation.longitude));
            }
            
            this.map.fitBounds(bounds);
        }
    }
    
    getMarkerIcon(category) {
        // Updated marker icons for new categories
        const iconMap = {
            'restaurants': 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="12" fill="#e74c3c" stroke="#fff" stroke-width="2"/>
                    <text x="16" y="20" text-anchor="middle" fill="white" font-size="10" font-family="Arial">🍽️</text>
                </svg>
            `),
            'coffee': 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="12" fill="#8b4513" stroke="#fff" stroke-width="2"/>
                    <text x="16" y="20" text-anchor="middle" fill="white" font-size="10" font-family="Arial">☕</text>
                </svg>
            `),
            'thrift': 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="12" fill="#7fb069" stroke="#fff" stroke-width="2"/>
                    <text x="16" y="20" text-anchor="middle" fill="white" font-size="10" font-family="Arial">👕</text>
                </svg>
            `),
            'nightlife': 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="12" fill="#2c3e50" stroke="#fff" stroke-width="2"/>
                    <text x="16" y="20" text-anchor="middle" fill="white" font-size="10" font-family="Arial">🍸</text>
                </svg>
            `),
            'hiking': 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="12" fill="#7fb069" stroke="#fff" stroke-width="2"/>
                    <text x="16" y="20" text-anchor="middle" fill="white" font-size="10" font-family="Arial">🥾</text>
                </svg>
            `),
            'beaches': 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="12" fill="#2d8f83" stroke="#fff" stroke-width="2"/>
                    <text x="16" y="20" text-anchor="middle" fill="white" font-size="10" font-family="Arial">🏖️</text>
                </svg>
            `),
            'shopping': 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="12" fill="#e67e22" stroke="#fff" stroke-width="2"/>
                    <text x="16" y="20" text-anchor="middle" fill="white" font-size="10" font-family="Arial">🛍️</text>
                </svg>
            `)
        };
        
        return iconMap[category] || iconMap['restaurants'];
    }
    
    showError(message) {
        const listContainer = document.getElementById('recommendationsList');
        listContainer.innerHTML = `
            <div class="error-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
                <button onclick="retryRecommendations()" class="retry-btn">Try Again</button>
            </div>
        `;
    }
    
    centerOnUser() {
        if (this.map && this.userLocation && this.userLocation.latitude && this.userLocation.longitude) {
            const userPosition = new google.maps.LatLng(
                this.userLocation.latitude,
                this.userLocation.longitude
            );
            this.map.panTo(userPosition);
            this.map.setZoom(14);
        }
    }
    
    toggleMapType() {
        if (!this.map) return;
        
        const currentType = this.map.getMapTypeId();
        const newType = currentType === 'roadmap' ? 'satellite' : 'roadmap';
        this.map.setMapTypeId(newType);
    }
    
    showRecommendationModal(index) {
        const rec = this.recommendations[index];
        if (!rec) return;
        
        const modal = document.getElementById('recommendationModal');
        const title = document.getElementById('modalTitle');
        const rating = document.getElementById('modalRating');
        const ratingText = document.getElementById('modalRatingText');
        const address = document.getElementById('modalAddress');
        const description = document.getElementById('modalDescription');
        const reason = document.getElementById('modalReason');
        const image = document.getElementById('modalImage');
        
        title.textContent = rec.name || 'Unknown Place';
        rating.innerHTML = this.generateStarsHTML(rec.rating || 0);
        ratingText.textContent = rec.rating ? `${rec.rating.toFixed(1)} stars` : 'No rating';
        address.textContent = rec.address || 'Address not available';
        description.textContent = rec.description || 'No description available.';
        reason.textContent = rec.recommendation_reason || '';
        
        // Handle photo
        if (rec.photo_reference && window.GOOGLE_MAPS_API_KEY) {
            const photoUrl = `/api/photo?photo_reference=${rec.photo_reference}&maxwidth=400`;
            image.style.backgroundImage = `url(${photoUrl})`;
            image.innerHTML = '';
        } else {
            image.style.backgroundImage = 'none';
            image.innerHTML = '<i class="fas fa-image"></i><span>No photo available</span>';
        }
        
        this.selectedRecommendation = rec;
        modal.classList.remove('hidden');
    }
}

// Initialize Google Maps
function initMap() {
    if (!window.USER_LOCATION || !window.USER_LOCATION.latitude || !window.USER_LOCATION.longitude) {
        console.error('No user location available for map initialization');
        return;
    }
    
    const mapOptions = {
        zoom: 13,
        center: new google.maps.LatLng(window.USER_LOCATION.latitude, window.USER_LOCATION.longitude),
        mapTypeId: 'roadmap',
        styles: [
            {
                featureType: 'poi',
                elementType: 'labels.text.fill',
                stylers: [{ color: '#6b7280' }]
            },
            {
                featureType: 'poi',
                elementType: 'labels.text.stroke',
                stylers: [{ color: '#ffffff' }, { weight: 2 }]
            }
        ]
    };
    
    const map = new google.maps.Map(document.getElementById('map'), mapOptions);
    
    // Add user location marker
    const userMarker = new google.maps.Marker({
        position: new google.maps.LatLng(window.USER_LOCATION.latitude, window.USER_LOCATION.longitude),
        map: map,
        title: 'Your Location',
        icon: {
            url: 'data:image/svg+xml;charset=UTF-8,' + encodeURIComponent(`
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32">
                    <circle cx="16" cy="16" r="12" fill="#2d8f83" stroke="#fff" stroke-width="3"/>
                    <circle cx="16" cy="16" r="4" fill="#fff"/>
                </svg>
            `),
            scaledSize: new google.maps.Size(32, 32),
            anchor: new google.maps.Point(16, 32)
        }
    });
    
    // Initialize dashboard app
    window.dashboardApp = new DashboardApp();
    window.dashboardApp.map = map;
    window.dashboardApp.infoWindow = new google.maps.InfoWindow();
}

// Global functions for template
function selectRecommendation(index) {
    if (window.dashboardApp) {
        window.dashboardApp.selectRecommendation(index);
    }
}

function showRecommendationModal(index) {
    if (window.dashboardApp) {
        window.dashboardApp.showRecommendationModal(index);
    }
}

function centerOnUser() {
    if (window.dashboardApp) {
        window.dashboardApp.centerOnUser();
    }
}

function toggleMapType() {
    if (window.dashboardApp) {
        window.dashboardApp.toggleMapType();
    }
}

function closeModal() {
    const modal = document.getElementById('recommendationModal');
    modal.classList.add('hidden');
}

// Updated to use business name instead of coordinates
function getDirections() {
    if (window.dashboardApp && window.dashboardApp.selectedRecommendation) {
        const rec = window.dashboardApp.selectedRecommendation;
        // Use business name and address for clearer destination
        const destination = encodeURIComponent(`${rec.name}, ${rec.address}`);
        const url = `https://www.google.com/maps/dir/?api=1&destination=${destination}`;
        window.open(url, '_blank');
    }
}

// Updated to use business name instead of coordinates
function openInMaps() {
    if (window.dashboardApp && window.dashboardApp.selectedRecommendation) {
        const rec = window.dashboardApp.selectedRecommendation;
        // Use business name and address for clearer search
        const query = encodeURIComponent(`${rec.name}, ${rec.address}`);
        const url = `https://www.google.com/maps/search/?api=1&query=${query}`;
        window.open(url, '_blank');
    }
}

// Updated to go to change-location route instead of onboarding
function changeLocation() {
    window.location.href = '/change-location';
}

function retryRecommendations() {
    if (window.dashboardApp) {
        window.dashboardApp.loadRecommendations(window.dashboardApp.currentCategory);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Dashboard app will be initialized by initMap callback
    console.log('Dashboard page loaded');
});
