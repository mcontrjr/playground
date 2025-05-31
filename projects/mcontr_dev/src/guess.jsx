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

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

// Theme hook
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

// Header Component
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

// Keypad Component
function GameKeypad({ guess, onKeypadPress, onClear, onBackspace, gameWon }) {
  return (
    <div className="keypad">
      {[1, 2, 3, 4, 5, 6, 7, 8, 9].map(num => (
        <button
          key={num}
          className="keypad-button"
          onClick={() => onKeypadPress(num.toString())}
          disabled={gameWon}
        >
          {num}
        </button>
      ))}
      <button
        className="keypad-button keypad-button-small"
        onClick={onClear}
        disabled={gameWon || !guess}
      >
        Clear
      </button>
      <button
        className="keypad-button"
        onClick={() => onKeypadPress('0')}
        disabled={gameWon}
      >
        0
      </button>
      <button
        className="keypad-button"
        onClick={onBackspace}
        disabled={gameWon || !guess}
      >
        ⌫
      </button>
    </div>
  );
}

// Game Interface Component
function GameInterface({ 
  message, 
  guess, 
  onKeypadPress, 
  onClear, 
  onBackspace, 
  onSubmitGuess, 
  onResetGame, 
  onClearHistory, 
  gameWon, 
  attempts, 
  gameHistory, 
  hasActiveGame 
}) {
  const isValidGuess = guess && Number(guess) >= 1 && Number(guess) <= 100;
  
  return (
    <div className={`game-main ${!hasActiveGame ? 'game-main-centered' : ''}`}>
      <div className="my-card animate-fade-in-up">
        <div className="my-card-body">
          <h3 className="text-center mb-3" style={{ color: 'var(--text-primary)' }}>
            Guessing Game
          </h3>
          
          <p className="mb-3" style={{ fontSize: '1.1rem', color: 'var(--text-secondary)' }}>
            {message}
          </p>
          
          <div className="guess-display">
            {guess || '?'}
          </div>

          <GameKeypad 
            guess={guess}
            onKeypadPress={onKeypadPress}
            onClear={onClear}
            onBackspace={onBackspace}
            gameWon={gameWon}
          />
        </div>
      </div>

      <div className="game-controls">
        <button 
          className="my-button"
          onClick={onSubmitGuess}
          disabled={gameWon || !isValidGuess}
          style={{ fontSize: '1.1rem', padding: '0.75rem 2rem', marginBottom: '1rem' }}
        >
          Submit Guess {guess && `(${guess})`}
        </button>
        {guess && !isValidGuess && (
          <p style={{ color: '#ef4444', fontSize: '0.9rem', marginBottom: '1rem', textAlign: 'center' }}>
            Warning: Number must be between 1-100
          </p>
        )}

        <div className="button-group">
          <button 
            className="my-button"
            onClick={onResetGame}
          >
            {gameWon ? 'New Game' : 'Reset Game'}
          </button>
          {gameHistory.length > 0 && (
            <button 
              className="my-button"
              onClick={onClearHistory}
            >
              Clear History
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Chart Component
function GameChart({ sessionAttempts, currentRound, theme }) {
  const [chartKey, setChartKey] = useState(0);
  
  const getThemeColors = () => {
    const computedStyle = getComputedStyle(document.documentElement);
    return {
      primary: computedStyle.getPropertyValue('--text-primary').trim(),
      secondary: computedStyle.getPropertyValue('--text-primary').trim(),
      border: computedStyle.getPropertyValue('--border').trim(),
    };
  };

  useEffect(() => {
    setChartKey(prev => prev + 1);
  }, [theme]);

  const colors = getThemeColors();

  const chartData = {
    labels: sessionAttempts.map((_, index) => `Attempt ${index + 1}`),
    datasets: [
      {
        label: 'Your Guess',
        data: sessionAttempts.map(attempt => attempt.guess),
        borderColor: colors.primary,
        backgroundColor: colors.primary,
        tension: 0.1,
        fill: false,
        pointBackgroundColor: colors.primary,
        pointBorderColor: colors.primary,
      }
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top',
        labels: {
          color: colors.primary
        }
      },
      title: {
        display: true,
        text: `Game ${currentRound} - Guess Progress`,
        color: colors.primary
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        grid: {
          color: colors.border,
        },
        ticks: {
          color: colors.secondary
        }
      },
      x: {
        grid: {
          color: colors.border,
        },
        ticks: {
          color: colors.secondary
        }
      }
    },
  };

  return (
    <div className="animate-fade-in-up" style={{ marginBottom: '2rem' }}>
      <h3 className="text-center mb-3" style={{ color: 'var(--text-primary)' }}>
        Current Game Progress
      </h3>
      <div className="my-card">
        <div className="my-card-body">
          <Line key={chartKey} data={chartData} options={chartOptions} />
        </div>
      </div>
    </div>
  );
}

// Game History Component
function GameHistory({ gameHistory }) {
  return (
    <div className="animate-fade-in-up">
      <h3 className="text-center mb-3" style={{ color: 'var(--text-primary)' }}>
        Game History
      </h3>
      <div className="custom-table-container">
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
  );
}

// Game Sidebar Component
function GameSidebar({ sessionAttempts, currentRound, theme, gameHistory }) {
  return (
    <div className="game-sidebar">
      {sessionAttempts.length > 0 && (
        <GameChart 
          sessionAttempts={sessionAttempts} 
          currentRound={currentRound} 
          theme={theme} 
        />
      )}
      
      {gameHistory.length > 0 && (
        <GameHistory gameHistory={gameHistory} />
      )}
    </div>
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
    if (guess.length < 3) {
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

  const hasActiveGame = sessionAttempts.length > 0;

  return (
    <>
      <ModernHeader theme={theme} toggleTheme={toggleTheme} />
      <main>
        <section className="my-section">
          <div className="my-container">
            {!hasActiveGame && (
              <h2 className="my-section-title animate-fade-in-up">Guessing Game</h2>
            )}
            
            <div className={`game-layout ${!hasActiveGame ? 'game-layout-centered' : ''}`}>
              {hasActiveGame && (
                <GameSidebar 
                  sessionAttempts={sessionAttempts}
                  currentRound={currentRound}
                  theme={theme}
                  gameHistory={gameHistory}
                />
              )}

              <GameInterface
                message={message}
                guess={guess}
                onKeypadPress={handleKeypadPress}
                onClear={handleClear}
                onBackspace={handleBackspace}
                onSubmitGuess={submitGuess}
                onResetGame={resetGame}
                onClearHistory={clearHistory}
                gameWon={gameWon}
                attempts={attempts}
                gameHistory={gameHistory}
                hasActiveGame={hasActiveGame}
              />
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  )
}