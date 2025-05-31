import { useState, useEffect } from 'react';
import '../styles/stock.css';
import notFound from './assets/not_found.svg';
import Footer from './components/footer';
import logo from './assets/random-logo.svg';
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


// Pexels API image fetching
async function getPexelsImages(keyword, page = 1) {
  try {
    const apiKey = import.meta.env.VITE_PEXELS_API_KEY;
    
    if (!keyword || keyword.trim() === '') {
      const response = await fetch(`https://api.pexels.com/v1/curated?per_page=9&page=${page}`, {
        headers: { 'Authorization': apiKey }
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      
      const data = await response.json();
      return { success: true, images: data.photos.map(photo => ({ id: photo.id, url: photo.src.medium })) };
    }
    
    const response = await fetch(`https://api.pexels.com/v1/search?query=${encodeURIComponent(keyword)}&per_page=9&page=${page}`, {
      headers: { 'Authorization': apiKey }
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
    const data = await response.json();
    if (data.photos.length === 0) return { success: false, error: 'No photos found' };
    
    return { success: true, images: data.photos.map(photo => ({ id: photo.id, url: photo.src.medium })) };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

// Lorem Picsum image fetching
async function getLoremPicsumImages(keyword, page = 1) {
  const images = [];
  const baseOffset = (page - 1) * 9;
  for (let i = 0; i < 9; i++) {
    const imageIndex = baseOffset + i;
    const seed = keyword ? `${keyword}-${imageIndex}` : `random-${Date.now()}-${imageIndex}`;
    images.push({ id: `picsum-${imageIndex}`, url: `https://picsum.photos/seed/${seed}/400/400` });
  }
  return { success: true, images };
}

// Flickr API image fetching
async function getFlickrImages(keyword, page = 1) {
  try {
    const apiKey = import.meta.env.VITE_FLICKR_API_KEY;
    
    if (!apiKey) {
      // Fallback to Lorem Flickr if no API key
      return getLoremFlickrImages(keyword, page);
    }
    
    let searchText = keyword && keyword.trim() !== '' ? keyword.trim() : 'nature';
    
    const response = await fetch(
      `https://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=${apiKey}&text=${encodeURIComponent(searchText)}&page=${page}&per_page=9&format=json&nojsoncallback=1&safe_search=1&content_type=1`
    );
    
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    
    const data = await response.json();
    if (data.photos.photo.length === 0) return { success: false, error: 'No photos found' };
    
    const images = data.photos.photo.map(photo => ({
      id: `flickr-${photo.id}`,
      url: `https://live.staticflickr.com/${photo.server}/${photo.id}_${photo.secret}_z.jpg`
    }));
    
    return { success: true, images };
  } catch (error) {
    return getLoremFlickrImages(keyword, page);
  }
}

// Lorem Flickr fallback (creative placeholder images)
async function getLoremFlickrImages(keyword, page = 1) {
  const images = [];
  const baseOffset = (page - 1) * 9;
  const categories = ['nature', 'city', 'abstract', 'people', 'technology', 'food', 'animals', 'architecture', 'art'];
  
  for (let i = 0; i < 9; i++) {
    const imageIndex = baseOffset + i;
    const category = keyword ? keyword : categories[imageIndex % categories.length];
    const seed = `flickr-${category}-${imageIndex}`;
    images.push({ 
      id: `lorem-flickr-${imageIndex}`, 
      url: `https://picsum.photos/seed/${seed}/400/400?random=${imageIndex}` 
    });
  }
  return { success: true, images };
}


// Components

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
            className="my-button"
            onClick={onSearch}
            disabled={loading}
          >
            {loading ? 'Searching...' : 'Search Photos'}
          </button>
        </div>

        {(hasSearched || hasImages) && (
          <div className="photo-button-group">
            <button 
              className="my-button"
              onClick={onClear}
              disabled={loading.pexels || loading.picsum || loading.flickr}
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

function TabulatedGallery({ pexelsImages, picsumImages, flickrImages, loading, activeTab, setActiveTab, keyword }) {
  const LoadingState = () => (
    <div className="gallery-loading-state">
      <div className="photo-skeleton-spinner"></div>
      <p className="gallery-loading-text">Loading photos...</p>
    </div>
  );

  const ErrorState = ({ engine }) => (
    <div className="gallery-error-state">
      <img src={notFound} alt="No results" className="gallery-error-image" />
      <p className="gallery-error-text">No photos found from {engine}. Try a different keyword!</p>
    </div>
  );

  const ImageGrid = ({ images, engine }) => (
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
    </>
  );

  return (
    <div className="gallery-tabs-container animate-fade-in-up">
      <div className="gallery-tabs-header">
        <button 
          className={`gallery-tab ${activeTab === 'pexels' ? 'active' : ''}`}
          onClick={() => setActiveTab('pexels')}
        >
          Pexels
        </button>
        <button 
          className={`gallery-tab ${activeTab === 'picsum' ? 'active' : ''}`}
          onClick={() => setActiveTab('picsum')}
        >
          Lorem Picsum
        </button>
        <button 
          className={`gallery-tab ${activeTab === 'flickr' ? 'active' : ''}`}
          onClick={() => setActiveTab('flickr')}
        >
          Flickr
        </button>
      </div>
      
      <div className="gallery-tab-content">
        <div className={`gallery-tab-pane ${activeTab === 'pexels' ? 'active' : ''}`}>
          <div className="gallery-engine-info">
            <h4 className="gallery-engine-title">Pexels Gallery</h4>
            <p className="gallery-engine-description">
              High-quality stock photos from professional photographers
            </p>
          </div>
          
          {loading.pexels ? (
            <LoadingState />
          ) : pexelsImages.length > 0 ? (
            <ImageGrid images={pexelsImages} engine="Pexels" />
          ) : (
            <ErrorState engine="Pexels" />
          )}
        </div>
        
        <div className={`gallery-tab-pane ${activeTab === 'picsum' ? 'active' : ''}`}>
          <div className="gallery-engine-info">
            <h4 className="gallery-engine-title">Lorem Picsum Gallery</h4>
            <p className="gallery-engine-description">
              Beautiful placeholder images with consistent quality and variety
            </p>
          </div>
          
          {loading.picsum ? (
            <LoadingState />
          ) : picsumImages.length > 0 ? (
            <ImageGrid images={picsumImages} engine="Lorem Picsum" />
          ) : (
            <ErrorState engine="Lorem Picsum" />
          )}
        </div>
        
        <div className={`gallery-tab-pane ${activeTab === 'flickr' ? 'active' : ''}`}>
          <div className="gallery-engine-info">
            <h4 className="gallery-engine-title">Flickr Gallery</h4>
            <p className="gallery-engine-description">
              Community-driven photos from photographers around the world
            </p>
          </div>
          
          {loading.flickr ? (
            <LoadingState />
          ) : flickrImages.length > 0 ? (
            <ImageGrid images={flickrImages} engine="Flickr" />
          ) : (
            <ErrorState engine="Flickr" />
          )}
        </div>
      </div>
      
      <div className="photo-credits">
        <p><strong>Photo Credits:</strong></p>
        <p>Photos provided by <a href="https://www.pexels.com" target="_blank" rel="noopener noreferrer">Pexels</a>, <a href="https://picsum.photos" target="_blank" rel="noopener noreferrer">Lorem Picsum</a>, and <a href="https://www.flickr.com" target="_blank" rel="noopener noreferrer">Flickr</a></p>
        <p>Click any photo to view full size</p>
      </div>
    </div>
  );
}


export default function RandomPage() {
  const { theme, toggleTheme } = useTheme();
  const [keyword, setKeyword] = useState('');
  const [pexelsImages, setPexelsImages] = useState([]);
  const [picsumImages, setPicsumImages] = useState([]);
  const [flickrImages, setFlickrImages] = useState([]);
  const [message, setMessage] = useState('Enter a keyword to discover amazing photos!');
  const [loading, setLoading] = useState({ pexels: false, picsum: false, flickr: false });
  const [hasSearched, setHasSearched] = useState(false);
  const [lastSearchedKeyword, setLastSearchedKeyword] = useState('');
  const [currentPage, setCurrentPage] = useState({ pexels: 1, picsum: 1, flickr: 1 });
  const [activeTab, setActiveTab] = useState('pexels');

  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !loading) handleSearch();
    };
    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [keyword, loading]);

  const handleSearch = async () => {
    setLoading({ pexels: true, picsum: true, flickr: true });
    setHasSearched(true);
    
    const searchKeyword = keyword.trim();
    let pexelsPage = 1;
    let picsumPage = 1;
    let flickrPage = 1;
    
    // If searching the same keyword as before, increment pages for different results
    if (searchKeyword === lastSearchedKeyword) {
      pexelsPage = currentPage.pexels + 1;
      picsumPage = currentPage.picsum + 1;
      flickrPage = currentPage.flickr + 1;
      setCurrentPage({ pexels: pexelsPage, picsum: picsumPage, flickr: flickrPage });
      setMessage(searchKeyword === '' ? `Loading more random photos...` : `Loading more photos for "${searchKeyword}"...`);
    } else {
      // New keyword, reset pages to 1
      setCurrentPage({ pexels: 1, picsum: 1, flickr: 1 });
      setLastSearchedKeyword(searchKeyword);
      setMessage(searchKeyword === '' ? 'Generating random photos...' : `Searching for "${searchKeyword}"...`);
    }

    // Search all three engines simultaneously
    const [pexelsResult, picsumResult, flickrResult] = await Promise.all([
      getPexelsImages(searchKeyword, pexelsPage),
      getLoremPicsumImages(searchKeyword, picsumPage),
      getFlickrImages(searchKeyword, flickrPage)
    ]);
    
    if (pexelsResult.success) {
      setPexelsImages(pexelsResult.images);
    } else {
      setPexelsImages([]);
    }
    
    if (picsumResult.success) {
      setPicsumImages(picsumResult.images);
    } else {
      setPicsumImages([]);
    }
    
    if (flickrResult.success) {
      setFlickrImages(flickrResult.images);
    } else {
      setFlickrImages([]);
    }
    
    setMessage(searchKeyword === '' ? 'Here are some photos for you!' : `Found photos for "${searchKeyword}"`);
    setLoading({ pexels: false, picsum: false, flickr: false });
  };

  const handleClear = () => {
    setPexelsImages([]);
    setPicsumImages([]);
    setFlickrImages([]);
    setKeyword('');
    setMessage('Enter a keyword to discover amazing photos!');
    setHasSearched(false);
    setLastSearchedKeyword('');
    setCurrentPage({ pexels: 1, picsum: 1, flickr: 1 });
  };

  return (
    <>
      <ModernHeader theme={theme} toggleTheme={toggleTheme} />
      <main>
        <section className="my-section">
          <div className="my-container">
            <h2 className="my-section-title animate-fade-in-up">Image Search</h2>

            <SearchInterface 
              keyword={keyword}
              setKeyword={setKeyword}
              onSearch={handleSearch}
              onClear={handleClear}
              loading={loading.pexels || loading.picsum || loading.flickr}
              message={message}
              hasSearched={hasSearched}
              hasImages={pexelsImages.length > 0 || picsumImages.length > 0 || flickrImages.length > 0}
            />

            {(hasSearched || pexelsImages.length > 0 || picsumImages.length > 0 || flickrImages.length > 0) && (
              <TabulatedGallery
                pexelsImages={pexelsImages}
                picsumImages={picsumImages}
                flickrImages={flickrImages}
                loading={loading}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
                keyword={keyword}
              />
            )}
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}

