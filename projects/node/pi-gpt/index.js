const express = require('express');
const path = require('path');
const os = require('os');
const axios = require('axios');
const { title } = require('process');
const { webcrypto } = require('crypto');

const app = express();
const PORT = process.env.PORT || 3000;

// Set the view engine to EJS
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Serve static files from the public directory
app.use(express.static(path.join(__dirname, 'public')));

// Route for landing page
app.get('/', (req, res) => {
    res.render('index');
});

// Route for server info page
app.get('/info', (req, res) => {
    const serverSpecs = {
        hostname: os.hostname(),
        platform: os.platform(),
        architecture: os.arch(),
        cpu: os.cpus(),
        totalMemory: `${(os.totalmem() / 1024 / 1024).toFixed(2)} MB`, // Convert bytes to MB
        freeMemory: `${(os.freemem() / 1024 / 1024).toFixed(2)} MB`,   // Convert bytes to MB
        uptime: `${(os.uptime() / 3600).toFixed(2)} hours`            // Convert seconds to hours
    };
    res.render('info', { title: 'Server Information', serverSpecs });
});

// Route for a cool pic
app.get('/cool', (req, res) => {
    res.render('cool', { title: 'Told you, just a cool pic' });
})

// Route for the guessing game
app.get('/guess', (req, res) => {
    // Random number between 1 and 100
    const randomNumber = Math.floor(Math.random() * 100) + 1;
    res.render('guess', { randomNumber });
});

// Function to get weather data
async function getWeather(city) {
    const WEATHER_TOKEN = process.env.WEATHER_TOKEN
    const url = `https://api.weatherapi.com/v1/current.json?key=${WEATHER_TOKEN}&q=${city}&aqi=no`;

    try {
        const response = await axios.get(url);
        return response.data;
    } catch (error) {
        console.error('Error fetching weather data:', error.response.data);
    }
}

app.get('/weather', async (req, res) => {;
    const myWeather = await getWeather('95128')
    res.render('weather', { title: 'MyWeather', myWeather })
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running at http://localhost:${PORT}`);
});
