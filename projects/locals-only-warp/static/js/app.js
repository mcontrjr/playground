class LocalsOnlyApp {
    constructor() {
        this.currentZipCode = '';
        this.currentCategory = 'general';
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadFromLocalStorage();
    }

    bindEvents() {
        // Search functionality
        const searchBtn = document.getElementById('searchBtn');
        const zipCodeInput = document.getElementById('zipCode');
        const retryBtn = document.getElementById('retryBtn');

        searchBtn.addEventListener('click', () => this.handleSearch());
        zipCodeInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.handleSearch();
            }
        });

        // Auto-format zip code input
        zipCodeInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, '');
            if (value.length > 5) {
                value = value.slice(0, 5) + '-' + value.slice(5, 9);
            }
            e.target.value = value;
        });

        retryBtn.addEventListener('click', () => this.handleSearch());

        // Category selection
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectCategory(e.target.closest('.category-btn'));
            });
        });
    }

    loadFromLocalStorage() {
        // Load previous search if available
        const savedZipCode = localStorage.getItem('lastZipCode');
        if (savedZipCode) {
            document.getElementById('zipCode').value = savedZipCode;
        }
    }

    selectCategory(button) {
        // Remove active class from all buttons
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('active');
        });

        // Add active class to clicked button
        button.classList.add('active');
        this.currentCategory = button.getAttribute('data-category');

        // If we have a current search, refresh with new category
        if (this.currentZipCode) {
            this.performSearch(this.currentZipCode, this.currentCategory);
        }
    }

    handleSearch() {
        const zipCode = document.getElementById('zipCode').value.trim();
        
        if (!zipCode) {
            this.showError('Please enter a zip code');
            return;
        }

        // Basic zip code validation
        const zipPattern = /^\d{5}(-\d{4})?$/;
        if (!zipPattern.test(zipCode)) {
            this.showError('Please enter a valid zip code (e.g., 12345 or 12345-6789)');
            return;
        }

        this.currentZipCode = zipCode;
        localStorage.setItem('lastZipCode', zipCode);
        this.performSearch(zipCode, this.currentCategory);
    }

    async performSearch(zipCode, category) {
        this.showLoading();
        this.hideError();
        this.hideResults();

        try {
            const response = await fetch('/api/recommendations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    zip_code: zipCode,
                    category: category
                })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                this.displayResults(data);
            } else {
                this.showError(data.error || 'Failed to get recommendations');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            this.hideLoading();
        }
    }

    displayResults(data) {
        const resultsSection = document.getElementById('resultsSection');
        const locationTitle = document.getElementById('locationTitle');
        const locationAddress = document.getElementById('locationAddress');
        const recommendationsList = document.getElementById('recommendationsList');

        // Update location info
        locationTitle.textContent = `Recommendations for ${this.formatCategory(data.category)}`;
        locationAddress.textContent = data.location.address;

        // Clear previous recommendations
        recommendationsList.innerHTML = '';

        // Add new recommendations
        if (data.recommendations && data.recommendations.length > 0) {
            data.recommendations.forEach((rec, index) => {
                const card = this.createRecommendationCard(rec, index);
                recommendationsList.appendChild(card);
            });
        } else {
            recommendationsList.innerHTML = `
                <div class="no-results">
                    <p>No recommendations found for this area. Try a different zip code or category.</p>
                </div>
            `;
        }

        this.showResults();
        
        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    createRecommendationCard(recommendation, index) {
        const card = document.createElement('div');
        card.className = 'recommendation-card';
        card.style.animationDelay = `${index * 0.1}s`;

        const type = recommendation.type || 'local';
        const name = recommendation.name || 'Local Recommendation';
        const description = recommendation.description || 'A great local spot worth checking out.';
        const address = recommendation.address || '';
        const reason = recommendation.recommendation_reason || recommendation.reason || '';

        card.innerHTML = `
            <div class="card-header">
                <h3 class="card-title">${this.escapeHtml(name)}</h3>
                <span class="card-type">${this.escapeHtml(type)}</span>
            </div>
            <p class="card-description">${this.escapeHtml(description)}</p>
            ${address ? `<div class="card-address"><i class="fas fa-map-pin"></i>${this.escapeHtml(address)}</div>` : ''}
            ${reason ? `<div class="card-reason">"${this.escapeHtml(reason)}"</div>` : ''}
        `;

        return card;
    }

    formatCategory(category) {
        const categoryMap = {
            'general': 'All Categories',
            'restaurants': 'Restaurants & Food',
            'activities': 'Activities & Attractions',
            'entertainment': 'Entertainment & Fun',
            'shopping': 'Shopping & Services'
        };
        return categoryMap[category] || category;
    }

    showLoading() {
        document.getElementById('loadingSpinner').classList.remove('hidden');
    }

    hideLoading() {
        document.getElementById('loadingSpinner').classList.add('hidden');
    }

    showResults() {
        document.getElementById('resultsSection').classList.remove('hidden');
    }

    hideResults() {
        document.getElementById('resultsSection').classList.add('hidden');
    }

    showError(message) {
        const errorMessage = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        
        errorText.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    hideError() {
        document.getElementById('errorMessage').classList.add('hidden');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LocalsOnlyApp();
});

// Add service worker registration for PWA (optional)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/sw.js')
            .then(registration => console.log('SW registered'))
            .catch(error => console.log('SW registration failed'));
    });
}
