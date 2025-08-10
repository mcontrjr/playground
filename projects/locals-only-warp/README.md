# Locals Only - Enhanced with Google Maps

A modern web application for discovering local businesses and hidden gems in your neighborhood, featuring Google Maps integration and a complete app-like experience.

## ✨ Features

### 🗺️ Google Maps Integration
- Interactive Google Maps with custom markers
- Real-time location services
- Google Places API for authentic business data
- Street View and satellite map views
- Turn-by-turn directions with business names

### 📱 App-Like Experience
- **Landing Page**: Beautiful introduction with feature highlights
- **Onboarding Flow**: 3-step setup process for first-time users
- **Dashboard**: Main app interface with category bubbles and full-screen map
- **Responsive Design**: Works seamlessly on desktop, tablet, and mobile

### 🎯 Enhanced Categories
- **Restaurants** 🍽️ - Local eateries and dining
- **Coffee** ☕ - Coffee shops and cafes
- **Thrift Stores** 👕 - Second-hand and vintage shops
- **Nightlife** 🍸 - Bars, clubs, and nightlife
- **Hiking** 🥾 - Trails and outdoor activities
- **Beaches & Lakes** 🏖️ - Waterfront and swimming spots
- **Shopping** 🛍️ - Retail and markets

### 🤖 AI-Enhanced Recommendations
- Local insights powered by Claude AI
- Contextual descriptions and recommendations
- Authentic local knowledge integration

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Google Maps API Key with the following services enabled:
  - Geocoding API
  - Geolocation API
  - Maps JavaScript API
  - Maps Embed API
  - Places API
  - Street View Static API
  - Maps Platform Datasets API
  - Places API (New)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd locals-only-warp
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here  # Optional
SECRET_KEY=your_secret_key_here
```

4. **Run the application**
```bash
python app.py
```

5. **Open your browser**
Navigate to `http://localhost:5005`

## 🏗️ Architecture

### Frontend
- **Vanilla JavaScript**: Modern ES6+ with classes and async/await
- **Responsive CSS**: Mobile-first design with CSS Grid and Flexbox
- **Google Maps JavaScript API**: Interactive maps and location services
- **Font Awesome**: Icons and UI elements

### Backend
- **Flask**: Python web framework
- **Google Places API**: Real business data and reviews
- **LangChain + Anthropic**: AI-enhanced local insights
- **Session Management**: User preferences and location storage

### User Flow
1. **Landing Page**: Introduction and call-to-action
2. **Onboarding**: 3-step setup (welcome → location → preferences)
3. **Dashboard**: Main app with category bubbles, map, and recommendations

## 📁 Project Structure
```
locals-only-warp/
├── app.py                      # Main Flask application
├── templates/pages/
│   ├── landing.html           # Landing page
│   ├── onboarding.html        # Setup flow
│   └── dashboard.html         # Main app
├── static/
│   ├── css/app.css           # All styles
│   ├── js/
│   │   ├── onboarding.js     # Setup logic
│   │   └── dashboard.js      # Main app logic
│   └── localsonly.jpg        # Logo
├── requirements.txt           # Dependencies
├── .env.example              # Environment template
└── start.sh                  # Easy startup script
```

## 🎨 Design System

### Colors (Logo-Inspired)
- Primary Teal: `#2d8f83`
- Primary Orange: `#e67e22`
- Secondary Navy: `#2c3e50`
- Accent Coral: `#e74c3c`
- Warm Beige: `#f4e5d3`
- Soft Mint: `#7fb069`
- Deep Brown: `#8b4513`

### Typography
- Font: Inter (Google Fonts)
- Weights: 300, 400, 500, 600, 700

## 🔧 Development

### API Endpoints
- `GET /` - Landing page or redirect to dashboard
- `GET /onboarding` - Setup flow
- `GET /dashboard` - Main application (requires location)
- `POST /api/set-location` - Save user location
- `POST /api/recommendations` - Get recommendations
- `GET /api/photo` - Proxy for Google Places photos
- `GET /api/health` - Health check

### Development Commands
```bash
# Using Make
make install        # Install dependencies
make run           # Start dev server
make lint          # Check code quality
make format        # Format code
make clean         # Clean up

# Direct commands
python app.py      # Start server
pip install -r requirements.txt
```

## 🚀 Production Deployment

### Environment Variables
```env
GOOGLE_MAPS_API_KEY=your_production_api_key
ANTHROPIC_API_KEY=your_anthropic_key
SECRET_KEY=secure_random_key
```

### Docker Deployment
```bash
# Build and run
docker-compose up --build

# Or with Docker directly
docker build -t locals-only .
docker run -p 5005:5005 --env-file .env locals-only
```

### Production Server
```bash
gunicorn --bind 0.0.0.0:5005 --workers 4 app:app
```

## 🔑 Google Maps API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable required APIs (listed in Prerequisites)
4. Create API Key
5. Set up restrictions for security

### API Restrictions (Recommended)
- **API Restrictions**: Limit to the services listed above
- **Application Restrictions**: HTTP referrers for your domain

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Google Maps Platform for location services
- Anthropic for AI capabilities
- Font Awesome for icons
- Inter font family

---

**Ready to discover your neighborhood? Start exploring with Locals Only!** 🗺️✨
