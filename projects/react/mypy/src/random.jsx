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

const apiUrl = import.meta.env.VITE_MYPY_API_URL;

function getRandomImg() {
    fetch(`${apiUrl}/get-loremflickr?category=random`)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        console.log(response.json().response)
        return response.json();
    })
    .then(data => setRandomImg(data.response))
    .catch(error => {
        console.error('error: ', error)
    });
}

export default function RandomPage() {
  const startMessage = 'Find something cool with 3 clicks.'
  const [randomImg, setRandomImg]  = useState(getRandomImg());
  const [guess, setGuess] = useState('');
  const [message, setMessage] = useState(startMessage);

  return (
    <>
      <ThemeProvider theme={theme}>
        <Head />
        <TextField
            id="random"
            label="Category"
            value={guess}
            type="input"
            variant="standard"
            color='white'
          />
        <p>{message}</p>
        <Button 
            variant="contained"
            sx={{color: '#cceeff'}}
            color='white'
          >
            Find
        </Button>
        <Footer sx={{ margin: "50px"}}/>
      </ThemeProvider>
    </>
  )
}

