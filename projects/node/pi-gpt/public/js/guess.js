
var attempts = 0;

function restartGame() {
    let randomNumber = Math.floor(Math.random() * 100) + 1;
    document.getElementById('result').innerText = '';
    document.getElementById('guessInput').value = '';
}

function checkGuess() {
    const userGuess = parseInt(document.getElementById('guessInput').value);
    const altGuess = 420
    let message = "";

    if (userGuess < 1 || userGuess > 1000) {
        message = "Please guess a number between 1 and 100.";
    } else if (userGuess === randomNumber) {
        message = `Congratulations! You guessed it right in ${attempts} attempts!`;
    } else if (userGuess === altGuess) {
        message = `Cheeky bastard. The correct number was ${randomNumber}`;
    } else if (userGuess < randomNumber) {
        message = "Too low! Try again.";
    } else {
        message = "Too high! Try again.";
    }
    attempts += 1;

    document.getElementById('result').innerText = message;
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('guessInput').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            checkGuess();
        }
    });
});