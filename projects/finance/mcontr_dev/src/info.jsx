import { useState, useEffect } from "react";
import error_img from './assets/error.svg';
import logo from './assets/info-logo.svg';
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


export default function InfoPage() {
    const { theme, toggleTheme } = useTheme();
    const apiUrl = 'http://localhost:8000';
    const [specs, setSpecs] = useState(null);
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        try {
            fetch(`${apiUrl}/system-info/`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                setSpecs(data);
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
                        <h2 className="my-section-title animate-fade-in-up">Platform Information</h2>
                        <div className="custom-table-container animate-fade-in-up">
                            <table className="custom-table">
                                <thead>
                                    <tr>
                                        <th>System</th>
                                        <th>Node</th>
                                        <th>Release</th>
                                        <th>Machine</th>
                                        <th>Processor</th>
                                        <th>Python Version</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr className="custom-table-row">
                                        <td>{specs.platform.system}</td>
                                        <td>{specs.platform.node}</td>
                                        <td>{specs.platform.release}</td>
                                        <td>{specs.platform.machine}</td>
                                        <td>{specs.platform.processor}</td>
                                        <td>{specs.platform.python_version}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <h2 className="my-section-title animate-fade-in-up" style={{ marginTop: '3rem' }}>CPU Information</h2>
                        <div className="custom-table-container animate-fade-in-up">
                            <table className="custom-table">
                                <thead>
                                    <tr>
                                        <th>Physical Cores</th>
                                        <th>Logical Cores</th>
                                        <th>CPU Usage (%)</th>
                                        <th>Current Frequency (MHz)</th>
                                        <th>Min Frequency (MHz)</th>
                                        <th>Max Frequency (MHz)</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr className="custom-table-row">
                                        <td>{specs.cpu.cpu_count}</td>
                                        <td>{specs.cpu.cpu_count_logical}</td>
                                        <td>{specs.cpu.cpu_percent.toFixed(1)}%</td>
                                        <td>{specs.cpu.cpu_freq ? specs.cpu.cpu_freq.current?.toFixed(0) : 'N/A'}</td>
                                        <td>{specs.cpu.cpu_freq ? specs.cpu.cpu_freq.min?.toFixed(0) : 'N/A'}</td>
                                        <td>{specs.cpu.cpu_freq ? specs.cpu.cpu_freq.max?.toFixed(0) : 'N/A'}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <h2 className="my-section-title animate-fade-in-up" style={{ marginTop: '3rem' }}>Memory Information</h2>
                        <div className="custom-table-container animate-fade-in-up">
                            <table className="custom-table">
                                <thead>
                                    <tr>
                                        <th>Total Memory</th>
                                        <th>Available Memory</th>
                                        <th>Used Memory</th>
                                        <th>Free Memory</th>
                                        <th>Usage Percentage</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr className="custom-table-row">
                                        <td>{(specs.memory.total / 1024 / 1024 / 1024).toFixed(2)} GB</td>
                                        <td>{(specs.memory.available / 1024 / 1024 / 1024).toFixed(2)} GB</td>
                                        <td>{(specs.memory.used / 1024 / 1024 / 1024).toFixed(2)} GB</td>
                                        <td>{(specs.memory.free / 1024 / 1024 / 1024).toFixed(2)} GB</td>
                                        <td>{specs.memory.percent.toFixed(1)}%</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <h2 className="my-section-title animate-fade-in-up" style={{ marginTop: '3rem' }}>Disk & Threads</h2>
                        <div className="custom-table-container animate-fade-in-up">
                            <table className="custom-table">
                                <thead>
                                    <tr>
                                        <th>Total Disk Space</th>
                                        <th>Used Disk Space</th>
                                        <th>Free Disk Space</th>
                                        <th>Disk Usage %</th>
                                        <th>Active Threads</th>
                                        <th>Current Thread</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr className="custom-table-row">
                                        <td>{(specs.disk.total / 1024 / 1024 / 1024).toFixed(2)} GB</td>
                                        <td>{(specs.disk.used / 1024 / 1024 / 1024).toFixed(2)} GB</td>
                                        <td>{(specs.disk.free / 1024 / 1024 / 1024).toFixed(2)} GB</td>
                                        <td>{specs.disk.percent.toFixed(1)}%</td>
                                        <td>{specs.threads.active_threads}</td>
                                        <td>{specs.threads.current_thread}</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>

                        <div style={{ marginTop: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                            <p>Last updated: {new Date(specs.timestamp).toLocaleString()}</p>
                        </div>
                    </div>
                </section>
            </main>
        </>
    );
}