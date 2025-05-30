import { useState, useEffect } from 'react';
import '../styles/stock.css';
import notFound from './assets/not_found.svg';
import Footer from '../components/footer';
import logo from './assets/logo.svg';
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
          <img src={logo} alt="mypy-logo" />
          <div className="my-logo-text">MyPy</div>
        </div>
        <nav className="my-nav" style={{ gap: '0.5rem' }}>
          <a href="/" className="my-button my-button-secondary">
            Home
          </a>
          <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
        </nav>
      </div>
    </header>
  );
}


// Simplified image fetching with Pexels API
async function getImages(keyword) {
  try {
    const apiKey = import.meta.env.VITE_PEXELS_API_KEY;
    
    if (!keyword || keyword.trim() === '') {
      const response = await fetch('https://api.pexels.com/v1/curated?per_page=9', {
        headers: { 'Authorization': apiKey }
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      const data = await response.json();
      return { success: true, images: data.photos.map(photo => ({ id: photo.id, url: photo.src.medium })) };
    }
    
    const response = await fetch(`https://api.pexels.com/v1/search?query=${encodeURIComponent(keyword)}&per_page=9`, {
      headers: { 'Authorization': apiKey }
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
    const data = await response.json();
    if (data.photos.length === 0) return { success: false, error: 'No photos found' };
    
    return { success: true, images: data.photos.map(photo => ({ id: photo.id, url: photo.src.medium })) };
  } catch (error) {
    return getFallbackImages(keyword);
  }
}

// Simplified fallback
async function getFallbackImages(keyword) {
  const images = [];
  for (let i = 0; i < 9; i++) {
    const seed = keyword ? `${keyword}-${i}` : `random-${Date.now()}-${i}`;
    images.push({ id: `fallback-${i}`, url: `https://picsum.photos/seed/${seed}/400/400` });
  }
  return { success: true, images };
}


// Components
function ApiNotice() {
  return (
    <div className="my-card api-notice animate-fade-in-up">
      <div className="my-card-body">
        <p className="api-notice-text">
          <strong>Demo Mode:</strong> Currently using fallback API. For best keyword accuracy, 
          <a href="https://www.pexels.com/api/" target="_blank" rel="noopener noreferrer" className="api-notice-link">
            get a free Pexels API key
          </a> and update the code.
        </p>
      </div>
    </div>
  );
}

function SearchInterface({ keyword, setKeyword, onSearch, onClear, loading, message, hasSearched, hasImages }) {
  return (
    <div className="my-card animate-fade-in-up" style={{ maxWidth: '500px', margin: '0 auto 3rem auto' }}>
      <div className="my-card-body">
        <p className="mb-3" style={{ fontSize: '1.1rem', color: 'var(--text-secondary)' }}>
          {message}
        </p>
        
        <div className="photo-search-container">
          <input
            type="text"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Enter keyword (e.g., nature, city, animals)..."
            disabled={loading}
            className="photo-search-input"
          />
          <button 
            className="my-button my-button-secondary"
            onClick={onSearch}
            disabled={loading}
          >
            {loading ? 'Searching...' : 'Search Photos'}
          </button>
        </div>

        {(hasSearched || hasImages) && (
          <div className="photo-button-group">
            <button 
              className="my-button my-button-secondary"
              onClick={onClear}
              disabled={loading}
            >
              Clear Results
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function LoadingGrid() {
  return (
    <div className="photo-grid-loading">
      {[...Array(9)].map((_, index) => (
        <div key={index} className="photo-skeleton">
          <div className="photo-skeleton-spinner"></div>
        </div>
      ))}
    </div>
  );
}

function ImageGrid({ images }) {
  return (
    <>
      <div className="photo-grid">
        {images.map((image) => (
          <div 
            key={image.id} 
            className="photo-card animate-fade-in-up"
            onClick={() => window.open(image.url, '_blank')}
          >
            <img
              src={image.url}
              alt="Photo"
              className="photo-image"
              onError={(e) => {
                e.target.src = notFound;
                e.target.style.padding = '20px';
                e.target.style.objectFit = 'contain';
              }}
            />
          </div>
        ))}
      </div>
      
      <div className="photo-credits">
        <p><strong>Photo Credits:</strong></p>
        <p>Photos provided by <a href="https://www.pexels.com" target="_blank" rel="noopener noreferrer">Pexels</a> and <a href="https://picsum.photos" target="_blank" rel="noopener noreferrer">Lorem Picsum</a></p>
        <p>Click any photo to view full size</p>
      </div>
    </>
  );
}

function NoResults() {
  return (
    <div className="animate-fade-in-up text-center">
      <img src={notFound} alt="No results" style={{ width: '200px', height: '200px', maxWidth: '100%' }} />
      <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>No photos found. Try a different keyword!</p>
    </div>
  );
}

export default function RandomPage() {
  const { theme, toggleTheme } = useTheme();
  const [keyword, setKeyword] = useState('');
  const [images, setImages] = useState([]);
  const [message, setMessage] = useState('Enter a keyword to discover amazing photos!');
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !loading) handleSearch();
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [keyword, loading]);

  const handleSearch = async () => {
    setLoading(true);
    setHasSearched(true);
    setMessage(keyword.trim() === '' ? 'Generating random photos...' : `Searching for "${keyword.trim()}"...`);

    const result = await getImages(keyword.trim());
    
    if (result.success) {
      setImages(result.images);
      setMessage(keyword.trim() === '' ? 'Here are some random photos for you!' : `Found photos for "${keyword.trim()}"`); 
    } else {
      setImages([]);
      setMessage('Sorry, something went wrong. Please try again.');
    }
    setLoading(false);
  };

  const handleClear = () => {
    setImages([]);
    setKeyword('');
    setMessage('Enter a keyword to discover amazing photos!');
    setHasSearched(false);
  };

  return (
    <>
      <ModernHeader theme={theme} toggleTheme={toggleTheme} />
      <main>
        <section className="my-section">
          <div className="my-container">
            <h2 className="my-section-title animate-fade-in-up">Random Image Generator</h2>

            <SearchInterface 
              keyword={keyword}
              setKeyword={setKeyword}
              onSearch={handleSearch}
              onClear={handleClear}
              loading={loading}
              message={message}
              hasSearched={hasSearched}
              hasImages={images.length > 0}
            />

            {loading && (
              <div className="animate-fade-in-up">
                <h3 className="text-center mb-3" style={{ color: 'var(--text-primary)' }}>Loading Photos...</h3>
                <LoadingGrid />
              </div>
            )}

            {!loading && images.length > 0 && (
              <div className="animate-fade-in-up">
                <h3 className="text-center mb-3" style={{ color: 'var(--text-primary)' }}>Gallery</h3>
                <ImageGrid images={images} />
              </div>
            )}

            {!loading && hasSearched && images.length === 0 && <NoResults />}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}

