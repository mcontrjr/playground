import { useState, useEffect } from 'react';
import coolImg from './assets/man_with_dog.jpg';
import Footer from '../components/footer';

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
      {theme === 'light' ? '🌙' : '☀️'}
    </button>
  );
}

// Modern Header Component
function ModernHeader({ theme, toggleTheme }) {
  return (
    <header className="my-header">
      <div className="my-header-content">
        <div className="my-logo-text">MyPy</div>
        <nav className="my-nav">
          <a href="/info" className="my-button my-button-secondary">
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
        <h1 className="my-hero-title animate-fade-in-up">MyPy</h1>
        <p className="my-hero-subtitle animate-fade-in-up">
          What started as a quick web app is evolving into something entirely different. 
          A collection of tools, features, and experiments that I find interesting — 
          some useful, some just for fun, and that's perfectly okay.
        </p>
        <div className="text-center mt-4">
          <img src={coolImg} className="custom-img animate-fade-in-up" alt="Man with dog" />
        </div>
      </div>
    </section>
  );
}

// Modern Feature Card Component
function FeatureCard({ title, description, route, icon, category = "feature" }) {
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
      <div className="my-card-header">
        <div className="my-card-icon">{icon}</div>
      </div>
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
function ToolCard({ title, description, route, icon, status = "available" }) {
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
        <div className="my-card-icon">{icon}</div>
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
      description: "Try to guess the number in just one attempt. It's definitely possible if you're lucky!",
      route: "/guess",
      icon: "🎯",
      category: "Game"
    },
    {
      title: "Weather Check",
      description: "Check local weather from the server and compare it with your own location data.",
      route: "/weather",
      icon: "🌤️",
      category: "Utility"
    },
    {
      title: "Image Generator",
      description: "Generate random images from who knows where. See if you get something cool!",
      route: "/random",
      icon: "🎨",
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
              icon={feature.icon}
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
      title: "Finance Parser",
      description: "Upload your financial data and get insights into where your money is going. Track expenses and analyze spending patterns.",
      route: "/finance",
      icon: "💰",
      status: "available"
    }
  ];

  return (
    <section className="my-section">
      <div className="my-container">
        <h2 className="my-section-title animate-fade-in-up">Tools</h2>
        <div className="my-grid my-grid-2">
          {tools.map((tool, index) => (
            <ToolCard
              key={index}
              title={tool.title}
              description={tool.description}
              route={tool.route}
              icon={tool.icon}
              status={tool.status}
            />
          ))}
        </div>
      </div>
    </section>
  );
}

// Stats or Info Section (optional enhancement)
function StatsSection() {
  const stats = [
    { label: "Projects", value: "4", icon: "📦" },
    { label: "Tools", value: "1", icon: "🔧" },
    { label: "Fun Factor", value: "∞", icon: "🚀" }
  ];

  return (
    <section className="my-section" style={{ background: 'var(--bg-secondary)' }}>
      <div className="my-container">
        <div className="my-grid my-grid-3">
          {stats.map((stat, index) => (
            <div key={index} className="my-card text-center animate-fade-in-up">
              <div className="my-card-body">
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>
                  {stat.icon}
                </div>
                <h3 style={{ fontSize: '2.5rem', fontWeight: '700', color: 'var(--accent)' }}>
                  {stat.value}
                </h3>
                <p style={{ margin: 0, color: 'var(--text-secondary)' }}>
                  {stat.label}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// About Section (redesigned)
function AboutSection() {
  return (
    <section className="my-section">
      <div className="my-container">
        <div className="my-grid my-grid-2" style={{ alignItems: 'center' }}>
          <div className="my-card animate-fade-in-up">
            <div className="my-card-header">
              <div className="my-card-icon">💭</div>
              <h2 className="my-card-title">What's This About?</h2>
            </div>
            <div className="my-card-body">
              <p>
                This project started with simple ambitions but has grown into something 
                much more interesting. It's become a digital playground where I experiment 
                with web technologies, build useful tools, and occasionally create something 
                just because it's fun.
              </p>
              <p>
                Each feature represents a different exploration — from practical utilities 
                to creative experiments. Some are genuinely useful, others are just for 
                entertainment, and that diversity is exactly what makes this project special.
              </p>
            </div>
          </div>
          <div className="text-center">
            <img 
              src={coolImg} 
              className="custom-img animate-fade-in-up" 
              alt="Man with his dog - representing the journey of development"
              style={{ maxWidth: '100%', height: 'auto' }}
            />
          </div>
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
        <AboutSection />
        <PlaygroundSection />
        <ToolsSection />
        <StatsSection />
      </main>
      <Footer />
    </>
  );
}