const express = require('express');
const path = require('path');
const os = require('os'); // Use the os module to get system information

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

// Route for the guessing game
app.get('/guess', (req, res) => {
    // Random number between 1 and 100
    const randomNumber = Math.floor(Math.random() * 100) + 1;
    res.render('guess', { randomNumber });
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running at http://localhost:${PORT}`);
});
