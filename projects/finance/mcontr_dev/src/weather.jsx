import { useState, useEffect } from 'react';
import '../styles/stock.css';
import error_img from './assets/rainy.svg';
import Footer from './components/footer';
import logo from './assets/weather-logo.svg';
import light from './assets/light.svg';
import dark from './assets/dark.svg';

// Theme toggle hook
function useTheme() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'light';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'light' ? 'dark' : 'light');
  };

  return { theme, toggleTheme };
}

// Theme Toggle Component
function ThemeToggle({ theme, toggleTheme }) {
  return (
    <button 
      className="theme-toggle" 
      onClick={toggleTheme}
      aria-label="Toggle theme"
      title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? <img src={light} alt="Dark mode" /> : <img src={dark} alt="Light mode" />}
    </button>
  );
}

// Modern Header Component
function ModernHeader({ theme, toggleTheme }) {
  return (
    <header className="my-header">
      <div className="my-header-content">
        <div className="my-logo">
          <img src={logo} alt="mcontr-logo" />
          <div className="my-logo-text">mcontr</div>
        </div>
        <nav className="my-nav" style={{ gap: '0.5rem' }}>
          <a href="/" className="my-button">
            Home
          </a>
          <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
        </nav>
      </div>
    </header>
  );
}

// Weather API function
async function getWeatherData(location) {
  try {
    const apiKey = import.meta.env.VITE_WEATHER_API_KEY;
    const response = await fetch(`https://api.weatherapi.com/v1/current.json?key=${apiKey}&q=${encodeURIComponent(location)}&aqi=no`);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    return { success: true, data };
  } catch (error) {
    console.error('Weather API error:', error);
    return { success: false, error: error.message };
  }
}

// Components
function SearchInterface({ location, setLocation, onSearch, loading, message }) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      onSearch();
    }
  };

  return (
    <div className="my-card animate-fade-in-up" style={{ maxWidth: '500px', margin: '0 auto 3rem auto' }}>
      <div className="my-card-body">
        <p className="mb-3" style={{ fontSize: '1.1rem', color: 'var(--text-secondary)' }}>
          {message}
        </p>
        
        <div className="photo-search-container">
          <input
            type="text"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            onKeyDown={handleKeyPress}
            placeholder="Enter city name or zip code..."
            disabled={loading}
            className="photo-search-input"
          />
          <button 
            className="my-button"
            onClick={onSearch}
            disabled={loading || !location.trim()}
          >
            {loading ? 'Loading...' : 'Get Weather'}
          </button>
        </div>
      </div>
    </div>
  );
}

function WeatherProfileCard({ weatherData }) {
  return (
    <div className="animate-fade-in-up" style={{ marginBottom: '3rem' }}>
      <div className="my-card weather-profile-card">
        <div className="my-card-body">
          {/* Profile Header */}
          <div className="weather-profile-header">
            <div className="weather-location-info">
              <h2 className="weather-location-name">
                {weatherData.location.name}
              </h2>
              <p className="weather-location-region">
                {weatherData.location.region}, {weatherData.location.country}
              </p>
              <p className="weather-location-time">
                Local time: {new Date(weatherData.location.localtime).toLocaleString()}
              </p>
            </div>
            
            <div className="weather-icon-temp-container">
              <div className="weather-icon-container">
                <img 
                  src={weatherData.current.condition.icon} 
                  alt={weatherData.current.condition.text}
                  className="weather-icon"
                />
                <p className="weather-condition-text">
                  {weatherData.current.condition.text}
                </p>
              </div>
              
              <div className="weather-temperature-container">
                <div className="weather-temperature-main">
                  {weatherData.current.temp_c}
                  <span className="weather-temperature-unit">
                    °C
                  </span>
                </div>
                <p className="weather-temperature-secondary">
                  {weatherData.current.temp_f}°F
                </p>
              </div>
            </div>
          </div>

          {/* Weather Stats Grid */}
          <div className="weather-stats-grid">
            <div className="weather-stat-item">
              <h4 className="weather-stat-title">Feels Like</h4>
              <div className="weather-stat-value">
                {weatherData.current.feelslike_c}°C
              </div>
              <p className="weather-stat-subtitle">
                {weatherData.current.feelslike_f}°F
              </p>
            </div>
            
            <div className="weather-stat-item">
              <h4 className="weather-stat-title">Humidity</h4>
              <div className="weather-stat-value">
                {weatherData.current.humidity}%
              </div>
              <p className="weather-stat-subtitle">
                Relative humidity
              </p>
            </div>
            
            <div className="weather-stat-item">
              <h4 className="weather-stat-title">Wind Speed</h4>
              <div className="weather-stat-value">
                {weatherData.current.wind_kph} km/h
              </div>
              <p className="weather-stat-subtitle">
                {weatherData.current.wind_mph} mph {weatherData.current.wind_dir}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function WeatherTable({ weatherData }) {
  const currentData = [
    ['Condition', weatherData.current.condition.text],
    ['Cloud Cover', `${weatherData.current.cloud}%`],
    ['Pressure', `${weatherData.current.pressure_mb} mb (${weatherData.current.pressure_in} in)`],
    ['Visibility', `${weatherData.current.vis_km} km (${weatherData.current.vis_miles} mi)`],
    ['UV Index', weatherData.current.uv],
    ['Precipitation', `${weatherData.current.precip_mm} mm (${weatherData.current.precip_in} in)`],
    ['Wind Gust', `${weatherData.current.gust_kph} km/h (${weatherData.current.gust_mph} mph)`]
  ];

  return (
    <div className="animate-fade-in-up">
      <h3 className="text-center mb-3" style={{ color: 'var(--text-primary)' }}>
        Detailed Weather Information
      </h3>
      <div className="custom-table-container">
        <table className="custom-table">
          <thead>
            <tr>
              <th style={{ color: 'var(--text-primary)' }}>Metric</th>
              <th style={{ color: 'var(--text-primary)' }}>Value</th>
            </tr>
          </thead>
          <tbody>
            {currentData.map((row, index) => (
              <tr key={index} className="custom-table-row">
                <td style={{ color: 'var(--text-primary)' }}>{row[0]}</td>
                <td style={{ color: 'var(--text-primary)' }}>{row[1]}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}


function LoadingState() {
  return (
    <div className="text-center animate-fade-in-up">
      <div style={{ 
        width: '40px', 
        height: '40px', 
        border: '4px solid var(--border)', 
        borderTop: '4px solid var(--accent)', 
        borderRadius: '50%', 
        animation: 'spin 1s linear infinite',
        margin: '2rem auto'
      }}></div>
      <p style={{ color: 'var(--text-secondary)' }}>Loading weather data...</p>
    </div>
  );
}

function ErrorState({ error }) {
  return (
    <div className="animate-fade-in-up text-center">
      <img src={error_img} alt="error" style={{ width: '300px', height: '300px', maxWidth: '100%' }} />
      <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>{error}</p>
    </div>
  );
}

export default function WeatherPage() {
  const { theme, toggleTheme } = useTheme();
  const [location, setLocation] = useState('');
  const [weatherData, setWeatherData] = useState(null);
  const [message, setMessage] = useState('Enter a city name or zip code to get current weather');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Add keyboard event listener for Enter key
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !loading && location.trim()) {
        handleSearch();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [location, loading]);

  const handleSearch = async () => {
    if (!location.trim()) return;
    
    setLoading(true);
    setError(null);
    setMessage(`Getting weather for "${location.trim()}"...`);

    const result = await getWeatherData(location.trim());
    
    if (result.success) {
      setWeatherData(result.data);
      setMessage('Success!');
    } else {
      setError(`Could not find weather data for "${location.trim()}". Please check the location and try again.`);
      setWeatherData(null);
      setMessage('Enter a city name or zip code to get current weather');
    }
    
    setLoading(false);
    setLocation('');
  };

  return (
    <>
      <ModernHeader theme={theme} toggleTheme={toggleTheme} />
      <main>
        <section className="my-section">
          <div className="my-container">
            <h2 className="my-section-title animate-fade-in-up">Weather Dashboard</h2>
            
            <SearchInterface 
              location={location}
              setLocation={setLocation}
              onSearch={handleSearch}
              loading={loading}
              message={message}
            />

            {loading && <LoadingState />}

            {error && !loading && <ErrorState error={error} />}

            {weatherData && !loading && !error && (
              <>
                <WeatherProfileCard weatherData={weatherData} />
                <WeatherTable weatherData={weatherData} />
              </>
            )}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}