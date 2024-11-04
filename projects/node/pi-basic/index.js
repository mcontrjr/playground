const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

// Middleware to serve static files
app.use(express.static('public'));

// Set up a simple route
app.get('/', (req, res) => {
    res.send('<h1>Welcome to My Web App!</h1>');
});

app.get('/about' , (req, res) => {
    res.send('<h1>About Page</h1>');
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server is running at http://localhost:${PORT}`);
});
