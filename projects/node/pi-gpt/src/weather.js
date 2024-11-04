const axios = require('axios');

// Function to get weather data
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

module.exports = { getWeather };
