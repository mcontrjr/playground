
function checkWeather() {
    const userLoc = document.getElementById('weatherData').value;
    if (userLoc) {
        // Redirect to the '/weather' route with the user-provided location as a query param
        window.location.href = `/weather?location=${encodeURIComponent(userLoc)}`;
    } else {
        alert('Please enter a location.');
    }
}

document.addEventListener('DOMContentLoaded', function() {
    console.log('in event listener')
    document.getElementById('weatherData').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            checkWeather();
        }
    });
});
