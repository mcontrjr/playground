class OnboardingFlow {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 3;
        this.userLocation = null;
        this.selectedPreferences = [];
        this.geocodeTimeout = null; // For auto-checking zip codes
        this.isAutoChecking = false;

        this.init();
    }

    init() {
        console.log('🚀 Onboarding flow initialized');
        this.updateProgress();
        this.loadPreferences();
        this.setupLocationInput();
        this.setupPreferenceCards();
    }

    setupPreferenceCards() {
        const preferenceCards = document.querySelectorAll('.preference-card');
        preferenceCards.forEach(card => {
            // Add click event listener
            card.addEventListener('click', (e) => {
                const category = e.currentTarget.dataset.category;
                this.togglePreference(category);
            });
            
            // Make cards keyboard accessible
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            card.setAttribute('aria-pressed', 'false');
            
            // Add keyboard support
            card.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const category = e.currentTarget.dataset.category;
                    this.togglePreference(category);
                }
            });
        });
        
        console.log(`Set up ${preferenceCards.length} preference card listeners`);
    }

    setupLocationInput() {
        const zipInput = document.getElementById('zipCodeInput');
        const verifyBtn = document.getElementById('verifyLocationBtn');

        if (zipInput) {
            // Auto-check as user types with debouncing
            zipInput.addEventListener('input', (e) => {
                const zipCode = e.target.value.trim();

                // Clear existing timeout
                if (this.geocodeTimeout) {
                    clearTimeout(this.geocodeTimeout);
                }

                // Only auto-check if we have a reasonable zip code format
                if (zipCode.length >= 5) {
                    this.geocodeTimeout = setTimeout(() => {
                        this.autoCheckZipCode(zipCode);
                    }, 1000); // Wait 1 second after user stops typing
                }
            });

            // Still keep Enter key functionality
            zipInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.verifyLocation();
                }
            });
        }

        if (verifyBtn) {
            verifyBtn.addEventListener('click', () => {
                this.verifyLocation();
            });
        }
    }

    async autoCheckZipCode(zipCode) {
        // Don't auto-check if user is actively verifying
        if (this.isAutoChecking) return;

        const zipClean = zipCode.replace('-', '').replace(' ', '');
        if (!(zipClean.match(/^\d{5}$/) || zipClean.match(/^\d{9}$/))) {
            return; // Invalid format, don't auto-check
        }

        console.log('🔄 Auto-checking zip code:', zipCode);
        this.isAutoChecking = true;

        try {
            const response = await fetch('https://api.zippopotam.us/us/' + zipCode.slice(0, 5));

            if (response.ok) {
                const data = await response.json();
                const city = data.places[0]['place name'];
                const state = data.places[0]['state abbreviation'];

                // Show success indication but don't enable next button yet
                this.showLocationResult({
                    city: city,
                    state: state,
                    zip_code: zipCode,
                    formatted_address: `${city}, ${state} ${zipCode}`,
                    auto_checked: true
                });
                this.enableNextButton();
                console.log('✅ Auto-check successful:', { city, state, zipCode });
            }
        } catch (error) {
            // Silently fail auto-checks, user can still manually verify
            console.log('⚠️ Auto-check failed, user can manually verify');
        } finally {
            this.isAutoChecking = false;
        }
    }

    async verifyLocation() {
        const zipInput = document.getElementById('zipCodeInput');
        const zipCode = zipInput?.value.trim();

        if (!zipCode) {
            this.showLocationError('Please enter a zip code.');
            return;
        }

        // Validate US zip code format (5 or 9 digits)
        const zipClean = zipCode.replace('-', '').replace(' ', '');
        if (!(zipClean.match(/^\d{5}$/) || zipClean.match(/^\d{9}$/))) {
            this.showLocationError('Please enter a valid US zip code (e.g., 12345 or 12345-6789).');
            return;
        }

        console.log('🔄 Verifying location:', zipCode);

        try {
            // Show loading on verify button
            const verifyBtn = document.getElementById('verifyLocationBtn');
            if (verifyBtn) {
                verifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
                verifyBtn.disabled = true;
            }

            // Use Google Geocoding API through our backend
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    zip_code: zipCode,
                    category: 'restaurants' // Just for location verification
                })
            });

            const data = await response.json();

            if (data.success && data.location) {
                this.userLocation = data.location;
                this.showLocationResult(data.location);
                this.enableNextButton();
                console.log('✅ Location verified:', data.location);
            } else {
                this.showLocationError(data.error || 'Unable to verify this zip code. Please check and try again.');
            }
        } catch (error) {
            console.error('Location verification error:', error);
            this.showLocationError('Network error. Please check your connection and try again.');
        } finally {
            // Reset verify button
            const verifyBtn = document.getElementById('verifyLocationBtn');
            if (verifyBtn) {
                verifyBtn.innerHTML = '<i class="fas fa-check"></i>';
                verifyBtn.disabled = false;
            }
        }
    }

    showLocationResult(location) {
        const resultDiv = document.getElementById('locationResult');
        const errorDiv = document.getElementById('locationError');
        const cityElement = document.getElementById('locationCity');
        const addressElement = document.getElementById('locationAddress');

        // Hide error if showing
        if (errorDiv) {
            errorDiv.classList.add('hidden');
        }

        // Show result
        if (resultDiv && cityElement && addressElement) {
            cityElement.textContent = `${location.city}, ${location.state}`;
            addressElement.textContent = location.formatted_address;

            // Add visual indicator if this was auto-checked
            if (location.auto_checked) {
                addressElement.innerHTML += ' <span style="color: var(--primary-gold); font-size: 0.75rem;"><i class="fas fa-magic"></i> Auto-detected</span>';
            }

            resultDiv.classList.remove('hidden');
        }
    }

    showLocationError(message) {
        const errorDiv = document.getElementById('locationError');
        const errorText = document.getElementById('locationErrorText');
        const resultDiv = document.getElementById('locationResult');

        // Hide result if showing
        if (resultDiv) {
            resultDiv.classList.add('hidden');
        }

        // Show error
        if (errorDiv && errorText) {
            errorText.textContent = message;
            errorDiv.classList.remove('hidden');
        }

        this.disableNextButton();
        this.userLocation = null;
    }

    enableNextButton() {
        const nextBtn = document.getElementById('step2NextBtn');
        if (nextBtn) {
            nextBtn.disabled = false;
        }
    }

    disableNextButton() {
        const nextBtn = document.getElementById('step2NextBtn');
        if (nextBtn) {
            nextBtn.disabled = true;
        }
    }

    async requestCurrentLocation() {
        if (!navigator.geolocation) {
            this.showLocationError('Geolocation is not supported by your browser.');
            return;
        }

        console.log('🔄 Requesting current location...');

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const { latitude, longitude } = position.coords;

                try {
                    // Reverse geocode to get zip code
                    const response = await fetch(`https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=${latitude}&longitude=${longitude}&localityLanguage=en`);
                    const data = await response.json();

                    if (data.postcode) {
                        // Update input and verify
                        const zipInput = document.getElementById('zipCodeInput');
                        if (zipInput) {
                            zipInput.value = data.postcode;
                        }

                        // Verify the detected zip code
                        await this.verifyLocation();
                    } else {
                        this.showLocationError('Unable to determine zip code from your location.');
                    }
                } catch (error) {
                    console.error('Reverse geocoding error:', error);
                    this.showLocationError('Unable to determine your zip code.');
                }
            },
            (error) => {
                console.error('Geolocation error:', error);
                let message = 'Unable to access your location. ';

                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        message += 'Please enable location access and try again.';
                        break;
                    case error.POSITION_UNAVAILABLE:
                        message += 'Location information is unavailable.';
                        break;
                    case error.TIMEOUT:
                        message += 'Location request timed out.';
                        break;
                    default:
                        message += 'An unknown error occurred.';
                        break;
                }

                this.showLocationError(message);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    }

    nextStep() {
        if (this.currentStep < this.totalSteps) {
            // Hide current step
            const currentStepElement = document.getElementById(`step${this.currentStep}`);
            if (currentStepElement) {
                currentStepElement.classList.remove('active');
            }

            // Show next step
            this.currentStep++;
            const nextStepElement = document.getElementById(`step${this.currentStep}`);
            if (nextStepElement) {
                nextStepElement.classList.add('active');
            }

            this.updateProgress();

            console.log(`Step ${this.currentStep} of ${this.totalSteps}`);
        }
    }

    previousStep() {
        if (this.currentStep > 1) {
            // Hide current step
            const currentStepElement = document.getElementById(`step${this.currentStep}`);
            if (currentStepElement) {
                currentStepElement.classList.remove('active');
            }

            // Show previous step
            this.currentStep--;
            const previousStepElement = document.getElementById(`step${this.currentStep}`);
            if (previousStepElement) {
                previousStepElement.classList.add('active');
            }

            this.updateProgress();

            console.log(`Step ${this.currentStep} of ${this.totalSteps}`);
        }
    }

    togglePreference(category) {
        const card = document.querySelector(`[data-category="${category}"]`);
        if (!card) return;

        const index = this.selectedPreferences.indexOf(category);

        if (index > -1) {
            // Remove from preferences
            this.selectedPreferences.splice(index, 1);
            card.classList.remove('selected');
            card.setAttribute('aria-pressed', 'false');
        } else {
            // Add to preferences
            this.selectedPreferences.push(category);
            card.classList.add('selected');
            card.setAttribute('aria-pressed', 'true');
        }

        // Save preferences to sessionStorage whenever they change
        this.savePreferences();

        console.log('Updated preferences:', this.selectedPreferences);
    }

    savePreferences() {
        try {
            sessionStorage.setItem('userPreferences', JSON.stringify(this.selectedPreferences));
            console.log('✅ User preferences saved to sessionStorage:', this.selectedPreferences);
        } catch (error) {
            console.error('❌ Error saving preferences:', error);
        }
    }

    loadPreferences() {
        try {
            const stored = sessionStorage.getItem('userPreferences');
            if (stored) {
                this.selectedPreferences = JSON.parse(stored);
                console.log('✅ User preferences loaded from sessionStorage:', this.selectedPreferences);

                // Update UI to reflect loaded preferences
                this.selectedPreferences.forEach(category => {
                    const card = document.querySelector(`[data-category="${category}"]`);
                    if (card) {
                        card.classList.add('selected');
                        card.setAttribute('aria-pressed', 'true');
                    }
                });
            }
        } catch (error) {
            console.error('❌ Error loading preferences:', error);
            this.selectedPreferences = [];
        }
    }

    showAlert(title, message) {
        const modal = document.getElementById('alertModal');
        const titleElement = document.getElementById('alertTitle');
        const messageElement = document.getElementById('alertMessage');

        if (modal && titleElement && messageElement) {
            titleElement.textContent = title;
            messageElement.textContent = message;
            modal.classList.remove('hidden');
        }
    }

    updateProgress() {
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        if (!progressFill || !progressText) return;

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
            // Save preferences one final time before completing
            this.savePreferences();

            // Save location to backend session
            const locationResponse = await fetch('/api/set-location', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(this.userLocation)
            });

            const locationResult = await locationResponse.json();

            if (locationResult.success) {
                // Save starred categories to backend
                if (this.selectedPreferences.length > 0) {
                    const prefsResponse = await fetch('/api/update-preferences', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            starred_categories: this.selectedPreferences
                        })
                    });

                    const prefsResult = await prefsResponse.json();
                    if (prefsResult.success) {
                        console.log('✅ Preferences saved to backend:', this.selectedPreferences);
                    } else {
                        console.warn('⚠️ Failed to save preferences to backend:', prefsResult.error);
                    }
                }

                // Mark onboarding as complete in sessionStorage
                sessionStorage.setItem('onboardingCompleted', 'true');

                console.log('✅ Onboarding completed with preferences:', this.selectedPreferences);

                // Redirect to dashboard
                window.location.href = '/dashboard';
            } else {
                throw new Error(locationResult.error || 'Failed to save location');
            }
        } catch (error) {
            console.error('❌ Onboarding completion error:', error);
            this.showAlert('Setup Error', 'There was an error completing your setup. Please try again.');
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    }
}

// Global functions for HTML onclick handlers
function nextStep() {
    if (window.onboardingFlow) {
        window.onboardingFlow.nextStep();
    }
}

function previousStep() {
    if (window.onboardingFlow) {
        window.onboardingFlow.previousStep();
    }
}

function togglePreference(category) {
    if (window.onboardingFlow) {
        window.onboardingFlow.togglePreference(category);
    }
}

function requestCurrentLocation() {
    if (window.onboardingFlow) {
        window.onboardingFlow.requestCurrentLocation();
    }
}

function completeOnboarding() {
    if (window.onboardingFlow) {
        window.onboardingFlow.completeOnboarding();
    }
}

function closeAlert() {
    const modal = document.getElementById('alertModal');
    if (modal) {
        modal.classList.add('hidden');
    }
}

// Initialize onboarding when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('📱 Onboarding page loaded, initializing flow...');
    window.onboardingFlow = new OnboardingFlow();
});
