import { useState, useEffect } from 'react';
import coolImg from './assets/man_with_dog.jpg';
import logo from './assets/logo.svg';
import light from './assets/light.svg';
import dark from './assets/dark.svg';
import Footer from './components/footer';

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
          <a href="/info" className="my-button ">
            Server Info
          </a>
          <ThemeToggle theme={theme} toggleTheme={toggleTheme} />
        </nav>
      </div>
    </header>
  );
}

// Hero Section Component
function HeroSection() {
  return (
    <section className="my-hero">
      <div className="my-container">
        <p className="my-hero-subtitle animate-fade-in-up">
          What started as a quick web app is evolving into something entirely different. 
          Built some things that are basic a** f*** and some things that are kinda useful?
          Regardless, here is a sick a** picture of a man and his dawg
        </p>
        <div className="text-center mt-4">
          <img src={coolImg} className="custom-img animate-fade-in-up" alt="Man with dog" />
        </div>
      </div>
    </section>
  );
}

// Modern Feature Card Component
function FeatureCard({ title, description, route, category = "feature" }) {
  const handleClick = () => {
    window.location.href = route;
  };

  return (
    <div 
      className="my-card my-card-interactive feature-card animate-fade-in-up" 
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
    >
      <div className="my-card-body">
        <h3 className="my-card-title">{title}</h3>
        <p>{description}</p>
      </div>
      <div className="my-card-footer">
        <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
          {category}
        </span>
        <span style={{ color: 'var(--accent)' }}>→</span>
      </div>
    </div>
  );
}

// Tool Card Component (slightly different styling for tools)
function ToolCard({ title, description, route, status = "available" }) {
  const handleClick = () => {
    window.location.href = route;
  };

  return (
    <div 
      className="my-card my-card-interactive animate-fade-in-up" 
      onClick={handleClick}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          handleClick();
        }
      }}
    >
      <div className="my-card-header">
        <div>
          <h3 className="my-card-title">{title}</h3>
          <span 
            className="text-sm" 
            style={{ 
              color: status === 'available' ? 'var(--accent)' : 'var(--text-muted)' 
            }}
          >
            {status}
          </span>
        </div>
      </div>
      <div className="my-card-body">
        <p>{description}</p>
      </div>
      <div className="my-card-footer">
        <span className="text-sm" style={{ color: 'var(--text-muted)' }}>
          Tool
        </span>
        <span style={{ color: 'var(--accent)' }}>→</span>
      </div>
    </div>
  );
}

// Playground Section
function PlaygroundSection() {
  const features = [
    {
      title: "Guessing Game",
      description: "Can you get it in 1 attempt? You got a 1% chance.",
      route: "/guess",
      category: "Game"
    },
    {
      title: "Weather Check",
      description: "Check weather with any zip code or city name.",
      route: "/weather",
      category: "Utility"
    },
    {
      title: "Image Generator",
      description: "Get random images from a single word!",
      route: "/random",
      category: "Creative"
    }
  ];

  return (
    <section className="my-section">
      <div className="my-container">
        <h2 className="my-section-title animate-fade-in-up">Playground</h2>
        <div className="my-grid my-grid-3">
          {features.map((feature, index) => (
            <FeatureCard
              key={index}
              title={feature.title}
              description={feature.description}
              route={feature.route}
              category={feature.category}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

// Tools Section
function ToolsSection() {
  const tools = [
    {
      title: "Statement Parser",
      description: "Upload your bank statements and get find out where your money is going.",
      route: "/finance"
    }
  ];

  return (
    <section className="my-section">
      <div className="my-container">
        <h2 className="my-section-title animate-fade-in-up">Tools</h2>
        <div className="my-grid my-grid-2 centered-grid">
          {tools.map((tool, index) => (
            <ToolCard
              key={index}
              title={tool.title}
              description={tool.description}
              route={tool.route}
              status={tool.status}
            />
          ))}
        </div>
      </div>
    </section>
  );
}


// Main App Component
export default function MainPage() {
  const { theme, toggleTheme } = useTheme();

  return (
    <>
      <ModernHeader theme={theme} toggleTheme={toggleTheme} />
      <main>
        <HeroSection />
        <PlaygroundSection />
        <ToolsSection />
      </main>
      <Footer />
    </>
  );
}