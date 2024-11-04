
async function getImage(){
    const userInput = document.getElementById('user').value.trim();
    try {
        const response = await axios.get(`http://localhost:3001/get-loremflickr?category=${encodeURIComponent(userInput)}`);
        const imageElement = document.getElementById('imageResult');
        imageElement.src = response.data.file;
    } catch (error) {
        console.error('Error fetching image response', error)
    }

    document.getElementById('user').value = '';
}

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('user').addEventListener('keypress', function(event) {
        if (event.key === 'Enter') {
            getImage(); // Call the generate function on 'Enter'
        }
    });
});