import { Box, Button, Typography, TextField, Table, TableBody, TableCell, Tabs, Tab, TableContainer, TableHead, TableRow, Paper, createTheme, ThemeProvider, Stack, CircularProgress } from "@mui/material";
import { TabPanel, TabContext } from '@mui/lab';
import { useState, useEffect } from "react";
import error_img from './assets/rainy.svg';
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
    const [location, setLocation] = useState('San Jose');
    const [message, setMessage] = useState('Enter Zip Code or City Name');
    const [error, setError] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchWeatherData();
    }, []);

    const fetchWeatherData = async () => {
        try {
            if (typeof location !== 'string' || location === '') {
                setMessage(`Not a valid location.`);
                return
            }
            const response = await fetch(`${apiUrl}/weather?location=${location}`); // Adjust endpoint as needed
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            const data = await response.json();
            if (data.response === null || data.response === undefined) {
                setMessage(`Could not find location \'${location}\'`)
                return
            }
            console.log(`Weather Data: ${JSON.stringify(data.response)}`)
            setWeatherData(data.response);
            console.log(`after setWeatherdata: ${JSON.stringify(data.response)}`)
            setLoading(false);
            setMessage('Enter Zip Code or City Name');
        } catch (error) {
            setError(`Error in fetchWeatherData: ${error.message}`);
        }
    };

    const handleFindLocation = async () => {
        try {
            console.log(`findLoc: ${location}`);
            fetchWeatherData();
            setLocation('');
            setMessage('Enter Zip Code or City Name');
        } catch (error) {
            setError(error.message);
        }
    };

    const handleKeyPress = (event) => {
        if (event.key === 'Enter') {
            console.log(`keyPress location: ${location}`);
            fetchWeatherData();
            setLocation('');
            setMessage('Enter Zip Code or City Name');
        }
    };

    const [value, setValue] = useState('1');

    const handleChange = (event, newValue) => {
        setValue(newValue);
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
                    <img src={error_img} alt="error" style={{ width: '350px', height: '350px' }} />
                    <Typography variant="body1">{error}</Typography>
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

                <Box sx={{ width: '100%', typography: 'body1' }}>
                    <TabContext value={value} sx={{backgroundColor: '#3789ad'}}>
                        <Box sx={{ borderBottom: 0, borderColor: 'divider' }}>
                            <Tabs onChange={handleChange} aria-label="lab API tabs example" sx={{margin: 0}} >
                                <Tab label="Metrics" value="1" sx={{backgroundColor: '#2b6c88'}} />
                                <Tab label="Forecast" value="2" sx={{backgroundColor: '#2b6c88'}} />
                                <Tab label="Historical" value="3" sx={{backgroundColor: '#2b6c88'}} />
                            </Tabs>
                        </Box>
                        <TabPanel value="1">
                            <TableContainer component={Paper} sx={{margin: 0}}>
                                <Table size="small">
                                    <TableHead>
                                        <TableRow sx={{backgroundColor: '#2b6c88'}}>
                                            <TableCell sx={{ textAlign: 'center' }}>Metric</TableCell>
                                            <TableCell sx={{ textAlign: 'center' }}>Value</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        <TableRow>
                                            <TableCell sx={{ textAlign: 'center' }}>Temperature (°C/°F)</TableCell>
                                            <TableCell sx={{ textAlign: 'center' }}>{weatherData.current.temp_c}°C / {weatherData.current.temp_f}°F</TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell sx={{ textAlign: 'center' }}>Humidity</TableCell>
                                            <TableCell sx={{ textAlign: 'center' }}>{weatherData.current.humidity}%</TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell sx={{ textAlign: 'center' }}>Wind</TableCell>
                                            <TableCell sx={{ textAlign: 'center' }}>{weatherData.current.wind_mph} mph / {weatherData.current.wind_kph} kph, {weatherData.current.wind_dir}</TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell sx={{ textAlign: 'center' }}>Pressure</TableCell>
                                            <TableCell sx={{ textAlign: 'center' }}>{weatherData.current.pressure_mb} mb / {weatherData.current.pressure_in} in</TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell sx={{ textAlign: 'center' }}>Visibility</TableCell>
                                            <TableCell sx={{ textAlign: 'center' }}>{weatherData.current.vis_km} km / {weatherData.current.vis_miles} miles</TableCell>
                                        </TableRow>
                                        <TableRow>
                                            <TableCell sx={{ textAlign: 'center' }}>UV Index</TableCell>
                                            <TableCell sx={{ textAlign: 'center' }}>{weatherData.current.uv}</TableCell>
                                        </TableRow>
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </TabPanel>
                        <TabPanel value="2">Item Two</TabPanel>
                        <TabPanel value="3">Item Three</TabPanel>
                    </TabContext>
                </Box>
                
            </Box>
            <Footer sx={{ margin: "50px" }} />
            
        </ThemeProvider>
    );
}