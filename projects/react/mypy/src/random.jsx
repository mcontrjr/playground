import { useState } from 'react'
import '../styles/stock.css'
import notFound from './assets/not_found.svg';
import Footer from '../components/footer'
import {Button, TextField, createTheme, ThemeProvider, LinearProgress, Skeleton, Box, Paper} from '@mui/material'

const theme = createTheme({
  typography: {
      fontFamily: '"Roboto Mono", monospace',
      h2: {
          color: "#ffffff"
      },
      h3: {
          color: "#ffffff"
      },
      body1: {
          color: "#ffffff"
      }
  },
  palette: {
      primary: {
        main: '#1c3e5c',
      },
      secondary: {
        main: '#3789ad',
      },
      backgroundColor: {
        main: '#1c3e5c',
      },
      text: {
          primary: '#ffffff',
          secondary: '#ffffff',
      }
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

const apiUrl = 'http://localhost:5170';

async function getRandomImg( category ) {
  const apiUrl = 'http://localhost:5170';
  console.log(`API URL: ${apiUrl}`);
  console.log(`Category: ${category} -` );

  if (category.length === 0 ) {
    category = 'random';
    console.log(`Passed empty category, setting to random: ${category}`)
  }

  try {
    const resp = await fetch(`${apiUrl}/get-loremflickr?category=${category}`)
    return resp.json()
  } catch (error) {
    console.error('Error: ', error)
    return {}
  }
}


export default function RandomPage() {
  const startMessage = 'Find something cool with 3 clicks.';
  const [category, setCategory] = useState('');
  const [randomImg, setRandomImg] = useState('https://loremflickr.com/480/480/');
  const [message, setMessage] = useState(startMessage);
  const [loading, setLoading] = useState(false);

  const handleFind = async () => {
      setLoading(true);
      if (category === "") {
          setMessage(`Looking for something...`);
      } else {
          setMessage(`Looking for "${category}"`);
      }
      const newImg = await getRandomImg(category);
      console.log(`New random Image: ${JSON.stringify(newImg)}`);
      if (newImg.response.rawFileUrl != null) {
          setRandomImg(newImg.response.rawFileUrl);
          if (category === "") {
              setMessage(`Found Something`);
          } else {
              setMessage(`Found "${category}"`);
          }
      } else {
          setRandomImg(notFound)
          setMessage(`Could not find something "${category}"`);
      }
      setCategory('');
      setLoading(false);
  };

  const handleKeyPress = (event) => {
      if (event.key === 'Enter') {
        if (category === "") {
            setMessage(`Looking for something...`);
        } else {
            setMessage(`Looking for "${category}"`);
        }
        handleFind();
      }
  };

  return (
    <>
      <ThemeProvider theme={theme}>
        <Head />
        <Paper 
            elevation={3} 
            sx={{ padding: 3, textAlign: 'center', margin: '20px', backgroundColor: '#1c3e5c' }}
        >
            <TextField
                id="category"
                label="Category"
                onChange={(e) => setCategory(e.target.value)}
                onKeyUp={handleKeyPress}
                placeholder='Category'
                value={category}
                type="input"
                variant="outlined"
                color='white'
                sx={{ marginBottom: 2 }}
            />
            <p>{message}</p>
            <Button 
                variant="contained"
                sx={{ color: '#cceeff', marginBottom: 2 }}
                color='white'
                onClick={handleFind}
            >
                Find
            </Button>
            {loading ? (
              <div>
                  <LinearProgress sx={{ margin: '10px 0' }} />
                  <Box display="flex" justifyContent="center">
                      <Skeleton variant="rectangular" width={480} height={480} />
                  </Box>
              </div>
            ) : (
              <div>
                  <hr />
                  <img src={randomImg} alt="Random" style={{ width: '480px', height: '480px' }} />
              </div>
            )}
        </Paper>
        <Footer sx={{ margin: "50px" }} />
      </ThemeProvider>
    </>
  );
}

