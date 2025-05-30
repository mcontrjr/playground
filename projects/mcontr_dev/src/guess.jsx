import { useState } from 'react'
import '../styles/stock.css'
import Footer from '../components/footer'
import {Button, TextField, createTheme, ThemeProvider} from '@mui/material'

// Create a custom theme for the app
const theme = createTheme({
  typography: {
      fontFamily: '"Roboto Mono", monospace',
      h2: {
          color: "#ffffff" // Custom color for h2
      },
      h3: {
          color: "#ffffff" // Custom color for h3
      },
      body1: {
          color: "#ffffff" // Custom default text color
      }
  },
  palette: {
      primary: {
          main: '#1c3e5c', // Main color for primary elements
      },
      secondary: {
          main: '#3789ad', // Main color for secondary elements
      },
  },
});

function Head() {
  return (
    <header>
      <h1>MyPy</h1>
      <nav>
        <a href="/" className='my-button'>Home</a>
      </nav>
    </header>
  )
}

function getRandomNum() {
    return Math.floor(Math.random() * 100)
}

export default function GuessPage() {
  const startMessage = 'Welcome to the Guessing Game'
  const [attempts, setAttempts] = useState(Number(0));
  const [randomNum, setRandomNum]  = useState(getRandomNum());
  const [guess, setGuess] = useState('');
  const [message, setMessage] = useState(startMessage);
  console.log(randomNum)

  const handleGuess = (e) => {
    setGuess(e.target.value)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
        setAttempts(attempts + 1)
        console.log('my guess: ', guess)
        compareGuess(guess)
        setGuess('')
    }
  }

  const compareGuess = (guess) => {
    if (Number(guess) === randomNum) {
        setMessage(`Can\'t believe it took you ${attempts} attempts`)
    } else if (guess < randomNum) {
        setMessage(`Your guess is too low. Try again! Your guess was ${guess}.`);
    } else {
        setMessage(`Your guess is too high. Try again! Your guess was ${guess}.`);
    }
  }

  const resetGame  = () => {
    setGuess('')
    setMessage(startMessage)
    setRandomNum(getRandomNum())
    setAttempts(0)
  }

  return (
    <>
      <ThemeProvider theme={theme}>
        <Head />
        <TextField
            id="guess"
            label="Your Guess"
            value={guess}
            type="number"
            variant="standard"
            color='white'
            onChange={handleGuess}
            onKeyDown={handleKeyPress}
          />
        <p>{message}</p>
        <Button 
            variant="contained"
            onClick={resetGame}
            sx={{color: '#cceeff'}}
            color='white'
          >
            Reset
        </Button>
        <Footer sx={{ margin: "50px"}}/>
      </ThemeProvider>
    </>
  )
}

