# Locals Only Backend - Google Places API Service

A clean, modern FastAPI backend service that provides local business recommendations using Google's new Places API. Designed to be maintainable, scalable, and production-ready.

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
cd locals-only-warp/backend
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
# Optional: install development dependencies
pip install -r requirements-dev.txt
```

3. **Set up environment variables**
```bash
cp .env.example .env
```

Edit `.env` and add your API keys:
```env
GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

4. **Run the application**
```bash
./run.sh --dev              # Development mode with auto-reload
# OR
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

5. **Access the API**
- API Documentation: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/api/v1/health`
- ReDoc Documentation: `http://localhost:8000/redoc`

## 🏗️ Architecture

### Backend (FastAPI Service)
- **FastAPI**: Modern, fast Python web framework with automatic OpenAPI docs
- **Google Places API (New)**: Latest Places API with enhanced features
- **Google Geocoding API**: For zip code to coordinate conversion
- **DuckDB**: Lightweight, embedded database for user data
- **Pydantic**: Data validation and serialization
- **Clean Architecture**: Separated concerns with models, routes, and services

### Key Components
- `src/main.py`: FastAPI application factory and configuration
- `src/routes.py`: API endpoint definitions with full OpenAPI documentation
- `src/places_client.py`: Google Places API client with comprehensive error handling
- `src/config.py`: Centralized configuration management using Pydantic Settings
- `src/database.py`: DuckDB database manager for user data storage
- `models/`: Comprehensive Pydantic models mirroring Google Places API schema

### Database
- **DuckDB**: Lightweight, embedded SQL database
- **User Management**: Phone numbers, starred categories, bookmarks, cached recommendations
- **Development**: Persistent storage in `data/app.duckdb`
- **Production**: In-memory for scalability
- **CLI Tools**: Complete database management via `db.py`

## 📁 Project Structure
```
locals-only-warp/backend/
├── src/
│   ├── main.py               # FastAPI application factory
│   ├── routes.py             # API endpoint definitions
│   ├── places_client.py      # Google Places API client
│   ├── config.py             # Configuration management
│   └── database.py           # DuckDB database manager
├── models/
│   ├── __init__.py           # Model exports
│   ├── base.py               # Base types and enums
│   ├── place.py              # Place model
│   ├── requests_new.py       # New Places API requests
│   ├── responses_new.py      # New Places API responses
│   ├── responses.py          # Core response models
│   ├── geocoding.py          # Geocoding models
│   ├── recommendation.py     # Recommendation models
│   └── user.py               # User CRUD models
├── data/
│   └── app.duckdb           # Development database
├── logs/                    # Application logs
├── db.py                   # Database CLI utility
├── places.py              # Places API testing utility
├── run.sh                # Development server script
├── requirements.txt      # Python dependencies
├── requirements-dev.txt  # Development dependencies
├── pyproject.toml       # Modern Python packaging
└── .env.example        # Environment variables template
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
**Core API Routes (`/api/v1/`)**
- `GET /health` - Health check endpoint
- `POST /rec_from_zip` - Get recommendations from zip code (New Places API)
- `POST /rec_from_text` - Get recommendations from text search (New Places API)

**User Management**
- `POST /users` - Create a new user
- `GET /users` - List users with pagination
- `GET /users/{user_id}` - Get user by ID
- `PUT /users/{user_id}` - Update user information
- `DELETE /users/{user_id}` - Delete user by ID
- `GET /users/phone/{phone_number}` - Get user by phone number

**Documentation**
- `GET /docs` - Interactive Swagger UI documentation
- `GET /redoc` - ReDoc API documentation
- `GET /openapi.json` - OpenAPI schema

### Development Commands
```bash
# Start the development server
./run.sh --dev              # Development mode with auto-reload
./run.sh --port 8080        # Use custom port
./run.sh --venv             # Use virtual environment

# Database management
python db.py --init                        # Initialize database
python db.py --create-user +1234567890     # Create a user
python db.py --list                        # List all users
python db.py --count                       # Count users

# Test the API
python places.py --test all                # Run full test suite
python places.py --health                  # Health check
python places.py --nearby --location "-33.8688,151.2093" --radius 1500

# Development tools
black .                     # Code formatting
isort .                     # Import sorting
flake8 .                    # Linting
mypy .                      # Type checking
bandit -r src/              # Security scanning
pytest                      # Run tests
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
