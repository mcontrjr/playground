import { useState, useEffect } from "react";
import error_img from './assets/error.svg';
import logo from './assets/logo.svg';
import light from './assets/light.svg';
import dark from './assets/dark.svg';
import '../styles/stock.css';

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


export default function InfoPage() {
    const { theme, toggleTheme } = useTheme();
    const apiUrl = 'http://localhost:5170';
    const [specs, setSpecs] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        try {
            fetch(`${apiUrl}/specs`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                setSpecs(data.response);
                setLoading(false);
            })
            .catch(error => setError(error));
        } catch (e) {
            setError(e);
        }
        
    }, []);

    // console.log(`Error state: ${error}`)
    if (loading) return (
        <>
            <ModernHeader theme={theme} toggleTheme={toggleTheme} />
            <div className="my-container">
                <div style={{ textAlign: 'center', padding: '2rem' }}>
                    <div style={{ 
                        width: '40px', 
                        height: '40px', 
                        border: '4px solid var(--border)', 
                        borderTop: '4px solid var(--accent)', 
                        borderRadius: '50%', 
                        animation: 'spin 1s linear infinite',
                        margin: '0 auto'
                    }}></div>
                    <p style={{ marginTop: '1rem', color: 'var(--text-secondary)' }}>Loading server stats...</p>
                </div>
            </div>
        </>
    )

    if (error) return (
        <>
            <ModernHeader theme={theme} toggleTheme={toggleTheme} />
            <div className="my-container">
                <div style={{ textAlign: 'center' }}>
                    <img src={error_img} alt="error" style={{ width: '300px', height: '300px', maxWidth: '100%' }} />
                    <p style={{ color: 'var(--text-secondary)', marginTop: '1rem' }}>{error.message || error}</p>
                </div>
            </div>
        </>
    )

    return (
        <>
            <ModernHeader theme={theme} toggleTheme={toggleTheme} />
            <main>
                <section className="my-section">
                    <div className="my-container">
                        <h2 className="my-section-title animate-fade-in-up">Server Stats</h2>
                        <div className="custom-table-container animate-fade-in-up">
                            <table className="custom-table">
                                <thead>
                                    <tr>
                                        <th>Hostname</th>
                                        <th>Platform</th>
                                        <th>Architecture</th>
                                        <th>Total Memory</th>
                                        <th>Free Memory</th>
                                        <th>Uptime</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr className="custom-table-row">
                                        <td>{specs.hostname}</td>
                                        <td>{specs.platform}</td>
                                        <td>{specs.architecture}</td>
                                        <td>{specs.totalMemory}</td>
                                        <td>{specs.freeMemory}</td>
                                        <td>{specs.uptime}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <h2 className="my-section-title animate-fade-in-up" style={{ marginTop: '3rem' }}>CPU Info</h2>
                        <div className="custom-table-container animate-fade-in-up">
                            <table className="custom-table">
                                <thead>
                                    <tr>
                                        <th>Model</th>
                                        <th>Speed (MHz)</th>
                                        <th>User Time</th>
                                        <th>Idle Time</th>
                                        <th>System Time</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {specs.cpu.map((cpu, index) => (
                                        <tr key={index} className="custom-table-row">
                                            <td>{cpu.model}</td>
                                            <td>{cpu.speed}</td>
                                            <td>{cpu.times.user}</td>
                                            <td>{cpu.times.idle}</td>
                                            <td>{cpu.times.sys}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </section>
            </main>
        </>
    );
}