# Locals Only - Discover Your Area 🏘️

A modern, AI-powered web app that helps users discover local businesses, restaurants, and activities in their neighborhood using just their zip code.

## Features ✨

- **Smart Recommendations**: Uses LangChain + Anthropic Claude to provide intelligent local recommendations
- **Zip Code Search**: Simple zip code input to find local gems
- **Category Filtering**: Filter by restaurants, activities, entertainment, shopping, or view all
- **Mobile-First Design**: Optimized for mobile devices with responsive design
- **Real-time Location Data**: Geocoding integration for accurate location information
- **Modern UI**: Clean, intuitive interface with local-inspired color palette

## Tech Stack 🛠️

- **Backend**: Flask (Python)
- **AI**: LangChain + Anthropic Claude
- **Frontend**: Vanilla JavaScript, HTML5, CSS3
- **APIs**: Geopy for geocoding
- **Styling**: Modern CSS with mobile-first responsive design

## Setup & Installation 🚀

1. **Clone and navigate to the project**:
   ```bash
   cd /path/to/locals-only-warp
   ```

2. **Ensure Python environment is set up**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # or `.venv/bin/activate` on Linux/Mac
   ```

3. **Install dependencies**:
   ```bash
   pip install flask langchain langchain-anthropic requests python-dotenv geopy folium
   ```

4. **Set up environment variables**:
   Create a `.env` file with your Anthropic API key:
   ```
   ANTHROPIC_API_KEY=your_api_key_here
   SECRET_KEY=your_secret_key_here
   ```

5. **Run the application**:
   ```bash
   python main.py
   ```

6. **Access the app**:
   Open your browser and go to `http://localhost:5005`

## Usage 📱

1. **Enter your zip code** in the search field
2. **Select a category** (All, Food, Activities, Fun, Shopping)
3. **Click search** or press Enter
4. **Browse recommendations** powered by local AI knowledge
5. **Change categories** to see different types of recommendations for the same area

## API Endpoints 🔌

- `GET /` - Main application interface
- `POST /api/recommendations` - Get recommendations for a zip code and category
- `GET /api/health` - Health check endpoint

## Mobile Development 📱

The app is designed to work seamlessly on mobile devices and can be accessed via:

- **Web browser** on any device
- **iOS Safari** for iPhone/iPad testing
- **Development server** accessible on local network for device testing

For iOS development and testing:
- The app runs on `0.0.0.0:5005` making it accessible on your local network
- Test on physical iPhone by connecting to the same WiFi and visiting `http://[your-computer-ip]:5005`
- Use iOS Simulator through Xcode if available

## Project Structure 📁

```
locals-only-warp/
├── app.py              # Main Flask application
├── main.py             # Application entry point
├── templates/
│   └── index.html      # Main HTML template
├── static/
│   ├── css/
│   │   └── style.css   # Responsive styles
│   ├── js/
│   │   └── app.js      # Frontend JavaScript
│   └── sw.js           # Service Worker (PWA)
├── .env                # Environment variables
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Color Palette 🎨

The app uses a warm, local-inspired color scheme:
- **Primary**: Deep Forest Green (#2D5A27)
- **Secondary**: Warm Brown (#8B4513) 
- **Accent**: Vibrant Orange (#FF6B35)
- **Fresh Green**: (#7FB069)
- **Warm Beige**: (#F4F1DE)

## Development Notes 💡

- Built with mobile-first responsive design
- Uses modern CSS features and animations
- Implements proper error handling and loading states
- Includes local storage for user preferences
- Progressive Web App (PWA) ready with service worker
- Accessible design with proper focus states and semantic HTML

## Contributing 🤝

This is a development project. Feel free to extend functionality or improve the design!

---

**Powered by local knowledge & AI** 🤖✨
