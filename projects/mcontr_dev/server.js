// server.js
import express from 'express';
import cors from 'cors';
import os from 'os';
import axios from 'axios';

const app = express();
const PORT = process.env.SERVER_PORT;

app.use(cors());
app.use(express.json()); // To parse JSON requests


class Specs {
    constructor () {
        this.hostname = os.hostname();
        this.platform = os.platform();
        this.architecture = os.arch();
        this.cpu = os.cpus();
        this.totalMemory = `${(os.totalmem() / 1024 / 1024).toFixed(2)} MB`;
        this.freeMemory = `${(os.freemem() / 1024 / 1024).toFixed(2)} MB`;
        this.uptime = `${(os.uptime() / 3600).toFixed(2)} hours`;
    }
}

function serverSpecs(){
    const specs = new Specs()
    return specs;
}

app.get('/specs', (req, res) => {
  try {
    const specs = serverSpecs(); 
    res.json({ response : specs });   
  } catch(error) {
      console.error('Could not load. Error: ', error)
      res.json({ response: error }, 500);
  }
});

app.get('/get-loremflickr', async (req, res) => {
  const category = req.query.category || 'random';
  const imageUrl = `https://loremflickr.com/json/480/480/${encodeURIComponent(category)}`
  console.log('Submitting request for ', category);
  try {
      const resp = await axios.get(imageUrl);
      console.log('Received ', resp.status);
      res.json({ response: resp.data })
  } catch(error) {
      console.log('Error in request: ', error);
  }
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

app.get('/weather', async (req, res) => {
  const location = req.query.location || '95126';
  console.log(`User requested weather for: ${location}`);
  const weatherData = await getWeather(location);
  console.log('Data ', weatherData);
  res.json({response: weatherData}, 200)
})

app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});