import { useState, useEffect } from 'react';
import '../styles/stock.css';
import Footer from '../components/footer';
import logo from './assets/logo.svg';
import light from './assets/light.svg';
import dark from './assets/dark.svg';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

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

function getRandomNum() {
    return Math.floor(Math.random() * 100) + 1;
}

export default function GuessPage() {
  const { theme, toggleTheme } = useTheme();
  const startMessage = 'Guess a number between 1-100!'
  const [attempts, setAttempts] = useState(0);
  const [randomNum, setRandomNum] = useState(getRandomNum());
  const [guess, setGuess] = useState('');
  const [message, setMessage] = useState(startMessage);
  const [gameHistory, setGameHistory] = useState([]);
  const [currentRound, setCurrentRound] = useState(1);
  const [gameWon, setGameWon] = useState(false);
  const [sessionAttempts, setSessionAttempts] = useState([]);

  console.log('Target:', randomNum);

  // Add keyboard event listener
  useEffect(() => {
    const handleKeyPress = (e) => {
      if (e.key === 'Enter' && !gameWon && guess && Number(guess) >= 1 && Number(guess) <= 100) {
        submitGuess();
      }
    };

    window.addEventListener('keydown', handleKeyPress);
    return () => window.removeEventListener('keydown', handleKeyPress);
  }, [guess, gameWon]);

  const handleKeypadPress = (digit) => {
    if (guess.length < 3) { // Limit to 3 digits max (for numbers up to 100)
      setGuess(prev => prev + digit);
    }
  };

  const handleClear = () => {
    setGuess('');
  };

  const handleBackspace = () => {
    setGuess(prev => prev.slice(0, -1));
  };

  const submitGuess = () => {
    if (!guess || guess === '') return;
    
    const guessNum = Number(guess);
    
    // Check bounds without counting as attempt
    if (guessNum < 1 || guessNum > 100) {
      setMessage(`Please enter a number between 1 and 100! Your guess: ${guessNum}`);
      setGuess('');
      return;
    }
    
    const newAttempt = attempts + 1;
    setAttempts(newAttempt);
    
    const newAttemptData = {
      attempt: newAttempt,
      guess: guessNum,
      target: randomNum,
      difference: Math.abs(guessNum - randomNum)
    };
    
    setSessionAttempts(prev => [...prev, newAttemptData]);
    compareGuess(guessNum, newAttempt);
    setGuess('');
  }

  const compareGuess = (guess, attemptNum) => {
    if (guess === randomNum) {
      setMessage(`Amazing! You got it in ${attemptNum} ${attemptNum === 1 ? 'attempt' : 'attempts'}!`);
      setGameWon(true);
      setGameHistory(prev => [...prev, { round: currentRound, attempts: attemptNum, target: randomNum }]);
    } else if (guess < randomNum) {
      setMessage(`Too low! Your guess: ${guess}. Try higher!`);
    } else {
      setMessage(`Too high! Your guess: ${guess}. Try lower!`);
    }
  }

  const resetGame = () => {
    setGuess('');
    setMessage(startMessage);
    setRandomNum(getRandomNum());
    setAttempts(0);
    setGameWon(false);
    setCurrentRound(prev => prev + 1);
    setSessionAttempts([]);
  }

  const clearHistory = () => {
    setGameHistory([]);
    setCurrentRound(1);
  }

  // Chart data for current game attempts
  const chartData = {
    labels: sessionAttempts.map((_, index) => `Attempt ${index + 1}`),
    datasets: [
      {
        label: 'Your Guess',
        data: sessionAttempts.map(attempt => attempt.guess),
        borderColor: 'var(--accent)',
        backgroundColor: 'var(--accent)',
        tension: 0.1,
        fill: false,
      }
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: 'var(--text-primary)',
          font: {
            family: '"Roboto Mono", monospace'
          }
        }
      },
      title: {
        display: true,
        text: `Game ${currentRound} - Guess Progress`,
        color: 'var(--text-primary)',
        font: {
          family: '"Roboto Mono", monospace',
          size: 16
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        grid: {
          color: 'var(--border)',
        },
        ticks: {
          color: 'var(--text-secondary)',
          font: {
            family: '"Roboto Mono", monospace'
          }
        }
      },
      x: {
        grid: {
          color: 'var(--border)',
        },
        ticks: {
          color: 'var(--text-secondary)',
          font: {
            family: '"Roboto Mono", monospace'
          }
        }
      }
    },
  };

  return (
    <>
      <ModernHeader theme={theme} toggleTheme={toggleTheme} />
      <main>
        <section className="my-section">
          <div className="my-container">
            <h2 className="my-section-title animate-fade-in-up">Guessing Game</h2>
            
            {/* Game Interface */}
            <div className="my-card animate-fade-in-up" style={{ maxWidth: '500px', margin: '0 auto' }}>
              <div className="my-card-body">
                <p className="mb-3" style={{ fontSize: '1.1rem', color: 'var(--text-secondary)' }}>
                  {message}
                </p>
                
                {/* Display Current Guess */}
                <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
                  <div style={{
                    background: 'var(--bg-secondary)',
                    border: '2px solid var(--border)',
                    borderRadius: '8px',
                    padding: '1rem',
                    fontSize: '2rem',
                    fontWeight: 'bold',
                    color: 'var(--text-primary)',
                    minHeight: '60px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    maxWidth: '200px',
                    margin: '0 auto'
                  }}>
                    {guess || '?'}
                  </div>
                </div>

                {/* Custom Keypad */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(3, 1fr)',
                  gap: '0.75rem',
                  maxWidth: '240px',
                  margin: '0 auto 1.5rem auto'
                }}>
                  {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
                    <button
                      key={num}
                      className="my-button my-button-secondary"
                      onClick={() => handleKeypadPress(num.toString())}
                      disabled={gameWon}
                      style={{ 
                        fontSize: '1.2rem', 
                        padding: '1rem',
                        minHeight: '50px',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center'
                      }}
                    >
                      {num}
                    </button>
                  ))}
                  <button
                    className="my-button my-button-secondary"
                    onClick={handleClear}
                    disabled={gameWon || !guess}
                    style={{ 
                      fontSize: '0.9rem', 
                      padding: '1rem',
                      minHeight: '50px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    Clear
                  </button>
                  <button
                    className="my-button my-button-secondary"
                    onClick={() => handleKeypadPress('0')}
                    disabled={gameWon}
                    style={{ 
                      fontSize: '1.2rem', 
                      padding: '1rem',
                      minHeight: '50px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    0
                  </button>
                  <button
                    className="my-button my-button-secondary"
                    onClick={handleBackspace}
                    disabled={gameWon || !guess}
                    style={{ 
                      fontSize: '1rem', 
                      padding: '1rem',
                      minHeight: '50px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    ⌫
                  </button>
                </div>

                {/* Submit Button */}
                <div style={{ textAlign: 'center', marginBottom: '1rem' }}>
                  <button 
                    className="my-button my-button-secondary"
                    onClick={submitGuess}
                    disabled={gameWon || !guess}
                    style={{ fontSize: '1.1rem', padding: '0.75rem 2rem' }}
                  >
                    Submit Guess {guess && `(${guess})`}
                  </button>
                  {guess && (Number(guess) < 1 || Number(guess) > 100) && (
                    <p style={{ color: '#ef4444', fontSize: '0.9rem', marginTop: '0.5rem' }}>
                      Warning: Number must be between 1-100
                    </p>
                  )}
                </div>

                <div style={{ marginTop: '1.5rem', display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
                  <button 
                    className="my-button my-button-secondary"
                    onClick={resetGame}
                  >
                    {gameWon ? 'New Game' : 'Reset Game'}
                  </button>
                  {gameHistory.length > 0 && (
                    <button 
                      className="my-button my-button-secondary"
                      onClick={clearHistory}
                    >
                      Clear History
                    </button>
                  )}
                </div>

                <div style={{ marginTop: '1rem', textAlign: 'center' }}>
                  <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
                    Attempts this round: <strong>{attempts}</strong>
                  </p>
                </div>
              </div>
            </div>

            {/* Chart Section */}
            {sessionAttempts.length > 0 && (
              <div className="animate-fade-in-up" style={{ marginTop: '3rem' }}>
                <h3 className="text-center mb-3" style={{ color: 'var(--text-primary)' }}>
                  Current Game Progress
                </h3>
                <div className="my-card" style={{ maxWidth: '800px', margin: '0 auto' }}>
                  <div className="my-card-body">
                    <Line data={chartData} options={chartOptions} />
                  </div>
                </div>
              </div>
            )}

            {/* Game History */}
            {gameHistory.length > 0 && (
              <div className="animate-fade-in-up" style={{ marginTop: '3rem' }}>
                <h3 className="text-center mb-3" style={{ color: 'var(--text-primary)' }}>
                  Game History
                </h3>
                <div className="custom-table-container" style={{ maxWidth: '600px', margin: '0 auto' }}>
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Game</th>
                        <th>Target</th>
                        <th>Attempts</th>
                        <th>Performance</th>
                      </tr>
                    </thead>
                    <tbody>
                      {gameHistory.map((game, index) => (
                        <tr key={index} className="custom-table-row">
                          <td>{game.round}</td>
                          <td>{game.target}</td>
                          <td>{game.attempts}</td>
                          <td>
                            <span style={{ 
                              color: game.attempts === 1 ? '#22c55e' : 
                                     game.attempts <= 3 ? '#3b82f6' : 
                                     game.attempts <= 7 ? '#f59e0b' : '#ef4444'
                            }}>
                              {game.attempts === 1 ? 'Perfect!' :
                               game.attempts <= 3 ? 'Excellent' :
                               game.attempts <= 7 ? 'Good' : 'Keep practicing'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}

