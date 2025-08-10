class OnboardingFlow {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 3;
        this.userLocation = null;
        this.selectedPreferences = [];
        
        this.initializeEventListeners();
        this.updateProgress();
    }
    
    initializeEventListeners() {
        // Zip code input validation
        const zipInput = document.getElementById('zipCodeInput');
        if (zipInput) {
            zipInput.addEventListener('input', this.validateZipCode.bind(this));
            zipInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.verifyLocation();
                }
            });
        }
        
        // Verify location button
        const verifyBtn = document.getElementById('verifyLocationBtn');
        if (verifyBtn) {
            verifyBtn.addEventListener('click', this.verifyLocation.bind(this));
        }
        
        // Preference cards
        const preferenceCards = document.querySelectorAll('.preference-card');
        preferenceCards.forEach(card => {
            card.addEventListener('click', () => this.togglePreference(card));
        });
    }
    
    validateZipCode() {
        const zipInput = document.getElementById('zipCodeInput');
        const verifyBtn = document.getElementById('verifyLocationBtn');
        const nextBtn = document.getElementById('step2NextBtn');
        
        const zipCode = zipInput.value.trim();
        const zipPattern = /^\d{5}(-\d{4})?$/;
        
        const isValid = zipPattern.test(zipCode);
        verifyBtn.disabled = !isValid;
        
        if (isValid) {
            verifyBtn.style.opacity = '1';
        } else {
            verifyBtn.style.opacity = '0.5';
            nextBtn.disabled = true;
            this.hideLocationResult();
        }
    }
    
    async verifyLocation() {
        const zipInput = document.getElementById('zipCodeInput');
        const zipCode = zipInput.value.trim();
        
        if (!zipCode) return;
        
        this.showLoadingState(true);
        this.hideLocationError();
        
        try {
            // Use Google Geocoding API if available
            if (window.GOOGLE_MAPS_API_KEY) {
                const response = await fetch(`https://maps.googleapis.com/maps/api/geocode/json?address=${encodeURIComponent(zipCode)}&components=country:US&key=${window.GOOGLE_MAPS_API_KEY}`);
                const data = await response.json();
                
                if (data.status === 'OK' && data.results.length > 0) {
                    const result = data.results[0];
                    const location = result.geometry.location;
                    
                    let city = '';
                    let state = '';
                    
                    result.address_components.forEach(component => {
                        if (component.types.includes('locality')) {
                            city = component.long_name;
                        } else if (component.types.includes('administrative_area_level_1')) {
                            state = component.short_name;
                        }
                    });
                    
                    this.userLocation = {
                        zip_code: zipCode,
                        latitude: location.lat,
                        longitude: location.lng,
                        city: city,
                        state: state,
                        formatted_address: result.formatted_address
                    };
                    
                    this.showLocationResult(this.userLocation);
                    document.getElementById('step2NextBtn').disabled = false;
                } else {
                    this.showLocationError('Location not found. Please check your zip code.');
                }
            } else {
                this.showLocationError('Location service unavailable. Please check your internet connection.');
            }
        } catch (error) {
            console.error('Location verification error:', error);
            this.showLocationError('Unable to verify location. Please try again.');
        } finally {
            this.showLoadingState(false);
        }
    }
    
    async requestCurrentLocation() {
        if (!navigator.geolocation) {
            this.showLocationError('Geolocation is not supported by this browser.');
            return;
        }
        
        this.showLoadingState(true);
        
        navigator.geolocation.getCurrentPosition(
            async (position) => {
                try {
                    const { latitude, longitude } = position.coords;
                    
                    // Reverse geocoding with Google Maps API
                    if (window.GOOGLE_MAPS_API_KEY) {
                        const response = await fetch(`https://maps.googleapis.com/maps/api/geocode/json?latlng=${latitude},${longitude}&key=${window.GOOGLE_MAPS_API_KEY}`);
                        const data = await response.json();
                        
                        if (data.status === 'OK' && data.results.length > 0) {
                            const result = data.results[0];
                            
                            let city = '';
                            let state = '';
                            let zipCode = '';
                            
                            result.address_components.forEach(component => {
                                if (component.types.includes('locality')) {
                                    city = component.long_name;
                                } else if (component.types.includes('administrative_area_level_1')) {
                                    state = component.short_name;
                                } else if (component.types.includes('postal_code')) {
                                    zipCode = component.long_name;
                                }
                            });
                            
                            this.userLocation = {
                                zip_code: zipCode,
                                latitude: latitude,
                                longitude: longitude,
                                city: city,
                                state: state,
                                formatted_address: result.formatted_address
                            };
                            
                            // Update zip code input
                            document.getElementById('zipCodeInput').value = zipCode;
                            
                            this.showLocationResult(this.userLocation);
                            document.getElementById('step2NextBtn').disabled = false;
                        } else {
                            this.showLocationError('Unable to determine your location details.');
                        }
                    }
                } catch (error) {
                    console.error('Reverse geocoding error:', error);
                    this.showLocationError('Unable to get location details.');
                } finally {
                    this.showLoadingState(false);
                }
            },
            (error) => {
                this.showLoadingState(false);
                switch(error.code) {
                    case error.PERMISSION_DENIED:
                        this.showLocationError('Location access denied. Please enable location services.');
                        break;
                    case error.POSITION_UNAVAILABLE:
                        this.showLocationError('Location information is unavailable.');
                        break;
                    case error.TIMEOUT:
                        this.showLocationError('Location request timed out.');
                        break;
                    default:
                        this.showLocationError('An unknown error occurred while retrieving location.');
                        break;
                }
            }
        );
    }
    
    showLocationResult(location) {
        const resultDiv = document.getElementById('locationResult');
        const cityEl = document.getElementById('locationCity');
        const addressEl = document.getElementById('locationAddress');
        
        cityEl.textContent = `${location.city}, ${location.state}`;
        addressEl.textContent = location.formatted_address;
        
        resultDiv.classList.remove('hidden');
        this.hideLocationError();
    }
    
    hideLocationResult() {
        const resultDiv = document.getElementById('locationResult');
        resultDiv.classList.add('hidden');
    }
    
    showLocationError(message) {
        const errorDiv = document.getElementById('locationError');
        const errorText = document.getElementById('locationErrorText');
        
        errorText.textContent = message;
        errorDiv.classList.remove('hidden');
    }
    
    hideLocationError() {
        const errorDiv = document.getElementById('locationError');
        errorDiv.classList.add('hidden');
    }
    
    showLoadingState(show) {
        const verifyBtn = document.getElementById('verifyLocationBtn');
        if (show) {
            verifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            verifyBtn.disabled = true;
        } else {
            verifyBtn.innerHTML = '<i class="fas fa-check"></i>';
            verifyBtn.disabled = false;
        }
    }
    
    togglePreference(card) {
        const category = card.dataset.category;
        
        if (card.classList.contains('selected')) {
            card.classList.remove('selected');
            this.selectedPreferences = this.selectedPreferences.filter(pref => pref !== category);
        } else {
            card.classList.add('selected');
            this.selectedPreferences.push(category);
        }
    }
    
    nextStep() {
        // Validate current step
        if (this.currentStep === 2 && !this.userLocation) {
            this.showLocationError('Please verify your location first.');
            return;
        }
        
        this.currentStep++;
        this.showStep(this.currentStep);
        this.updateProgress();
    }
    
    previousStep() {
        this.currentStep--;
        this.showStep(this.currentStep);
        this.updateProgress();
    }
    
    showStep(stepNumber) {
        // Hide all steps
        document.querySelectorAll('.onboarding-step').forEach(step => {
            step.classList.remove('active');
        });
        
        // Show current step
        const currentStepEl = document.getElementById(`step${stepNumber}`);
        if (currentStepEl) {
            currentStepEl.classList.add('active');
        }
    }
    
    updateProgress() {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        const progressPercentage = (this.currentStep / this.totalSteps) * 100;
        progressFill.style.width = `${progressPercentage}%`;
        progressText.textContent = `Step ${this.currentStep} of ${this.totalSteps}`;
    }
    
    async completeOnboarding() {
        if (!this.userLocation) {
            this.showLocationError('Please set your location first.');
            return;
        }
        
        const loadingOverlay = document.getElementById('loadingOverlay');
        loadingOverlay.classList.remove('hidden');
        
        try {
            const response = await fetch('/api/set-location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    ...this.userLocation,
                    preferences: this.selectedPreferences
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Redirect to dashboard
                window.location.href = '/dashboard';
            } else {
                throw new Error(result.error || 'Failed to complete setup');
            }
        } catch (error) {
            console.error('Onboarding completion error:', error);
            alert('Failed to complete setup. Please try again.');
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    }
}

// Initialize onboarding when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.onboardingFlow = new OnboardingFlow();
});

// Global functions for template
function nextStep() {
    window.onboardingFlow.nextStep();
}

function previousStep() {
    window.onboardingFlow.previousStep();
}

function requestCurrentLocation() {
    window.onboardingFlow.requestCurrentLocation();
}

function completeOnboarding() {
    window.onboardingFlow.completeOnboarding();
}
