const express = require('express');
const router = express.Router();
const axios = require('axios');
const { getWeather } = require('./weather');
const { serverSpecs } = require('./utils');
const os = require('os');


// Landing Page
router.get('/', (req, res) => {
    console.log('Loading landing page...')
    res.render('index');
});

// Server Info Page
router.get('/info', (req, res) => {
    console.log('Loading info page...');
    let specs;
    try {
        specs = serverSpecs();    
    } catch(error) {
        console.error('Could not load. Error: ', error)
    }
    res.render('info',  {title:  'Server Information',  specs});
});

// Guessing Game
router.get('/guess', (req, res) => {
    const randomNumber = Math.floor(Math.random() * 100) + 1;
    res.render('guess', { randomNumber });
});

// Loremflickr middle man
router.get('/get-loremflickr', async (req, res) => {
    const category = req.query.category || 'random';
    const imageUrl = `https://loremflickr.com/json/480/480/${encodeURIComponent(category)}`
    console.log('Submitting request for', category);

    try {
        const resp = await axios.get(imageUrl);
        console.log('Received ', resp.status);
        res.json(resp.data)
    } catch(error) {
        console.log('Error in request: ', error);
    }
});

// Random image from LoremFlickr
router.get('/random', (req, res) => {
    res.render('random', { title: 'Random Ass Pictures from IDK Where'});
});

// Weather
async function getWeather(city) {
    const WEATHER_TOKEN = process.env.WEATHER_TOKEN
    const url = `https://api.weatherapi.com/v1/current.json?key=${WEATHER_TOKEN}&q=${city}&aqi=no`;
    console.log('Sending request to ', url)
    try {
        const response = await axios.get(url);
        console.log('Received ', response.status);
        return response.data;
    } catch (error) {
        console.error('Error fetching weather data:', error);
    }
}

router.get('/weather', async (req, res) => {
    const location = req.query.location || '95126';
    console.log(`User requested weather for: ${location}`);
    const weatherData = await getWeather(location);
    console.log('Data ', weatherData);
    if (weatherData) {
        res.render('weather', { title: 'MyWeather', weatherData });
    } else {
        res.render('weather', { title: 'MyWeather', weatherData:  null })
    }
})

module.exports = router;