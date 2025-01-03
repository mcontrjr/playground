import { Box, Button, Typography, TextField, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, createTheme, ThemeProvider, Stack, CircularProgress } from "@mui/material";
import { useState, useEffect } from "react";
import error_img from './assets/error.svg';
import Footer from '../components/footer'

const theme = createTheme({
    typography: {
        fontFamily: '"Roboto Mono", monospace',
        h2: {
            color: "#ffffff",
        },
        h3: {
            color: "#ffffff",
        },
        body1: {
            color: "#ffffff",
        }
    },
    palette: {
        primary: {
            main: '#1c3e5c',
        },
        secondary: {
            main: '#3789ad',
        },
    },
});

export default function WeatherPage() {
    const apiUrl = 'http://localhost:5170';
    const [weatherData, setWeatherData] = useState(null);
    const [location, setLocation] = useState('');
    const [message, setMessage] = useState('Enter Zip Code or City Name');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchWeatherData();
    }, []);

    const fetchWeatherData = async () => {
        try {
            const response = await fetch(`${apiUrl}/weather?location=95126`); // Adjust endpoint as needed
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            console.log(`Weather Data: ${JSON.stringify(data.response)}`)
            setWeatherData(data.response);
            console.log(`after setWeatherdata: ${JSON.stringify(data.response)}`)
            setLoading(false);
        } catch (error) {
            setError(error);
        }
    };

    const handleFindLocation = async (location) => {
        try {
            console.log(`findLoc: ${location}`)
            const response = await fetch(`${apiUrl}/weather?location=${location}`); // Adjust endpoint as needed
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            setWeatherData(data.response);
            setLoading(false);
        } catch (error) {
            setError(error);
        }
    }

    const handleKeyPress = (event) => {
        if (event.key === 'Enter') {
            handleFindLocation(location);
        }
    };

    if (loading) {
        return (
            <ThemeProvider theme={theme}>
                <Box className="my-container">
                    <CircularProgress color="secondary" />
                    <nav>
                        <a href="/" className='my-button'>Home</a>
                    </nav>
                </Box>
            </ThemeProvider>
        );
    }

    if (error) {
        return (
            <ThemeProvider theme={theme}>
                <Box className="my-container">
                    <img src={error_img} alt="error" style={{ width: '480px', height: '480px' }} />
                    <Typography variant="body1">{error.message}</Typography>
                    <nav>
                        <a href="/" className='my-button'>Home</a>
                    </nav>
                </Box>
            </ThemeProvider>
        );
    }

    return (
        <ThemeProvider theme={theme}>
            <Box className="my-container">
                <Typography variant="h2">Weather</Typography>
                <nav>
                    <a href="/" className='my-button'>Home</a>
                </nav>
                <p>{message}</p>

                <Stack 
                    direction="row" 
                    spacing={2} 
                    sx={{
                        justifyContent: "center",
                        alignItems: "center",
                        margin: 2
                    }}
                >
                    <TextField
                    id="location"
                    label="Location"
                    onChange={(e) => setLocation(e.target.value)}
                    onKeyUp={handleKeyPress}
                    value={location}
                    type="input"
                    variant="outlined"
                    color="white"
                    sx={{ margin: 2 }}
                    />
                    
                    <Button 
                        variant="contained"
                        sx={{ color: '#cceeff', margin: 2 }}
                        color='white'
                        onClick={handleFindLocation}
                    >
                        Get Weather
                    </Button>
                </Stack>

                <hr></hr>
                <Stack 
                    direction="row" 
                    spacing={2} 
                    sx={{
                        justifyContent: "center",
                        alignItems: "center",
                    }}
                >
                    <Typography variant="h3">{`${weatherData.location.name}`}</Typography>
                    <img src={weatherData.current.condition.icon} alt={weatherData.current.condition.text} />
                </Stack>

            

                <TableContainer component={Paper} sx={{margin: 2}}>
                    <Table>
                        <TableHead>
                            <TableRow sx={{backgroundColor: '#3789ad'}}>
                                <TableCell>Metric</TableCell>
                                <TableCell>Value</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            <TableRow>
                                <TableCell>Temperature (°C/°F)</TableCell>
                                <TableCell>{weatherData.current.temp_c}°C / {weatherData.current.temp_f}°F</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>Humidity</TableCell>
                                <TableCell>{weatherData.current.humidity}%</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>Wind</TableCell>
                                <TableCell>{weatherData.current.wind_mph} mph / {weatherData.current.wind_kph} kph, {weatherData.current.wind_dir}</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>Pressure</TableCell>
                                <TableCell>{weatherData.current.pressure_mb} mb / {weatherData.current.pressure_in} in</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>Visibility</TableCell>
                                <TableCell>{weatherData.current.vis_km} km / {weatherData.current.vis_miles} miles</TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>UV Index</TableCell>
                                <TableCell>{weatherData.current.uv}</TableCell>
                            </TableRow>
                        </TableBody>
                    </Table>
                </TableContainer>
                
            </Box>
            <Footer sx={{ margin: "50px" }} />
            
        </ThemeProvider>
    );
}