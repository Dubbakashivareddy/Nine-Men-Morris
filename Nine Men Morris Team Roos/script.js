// Your game logic goes here

function startNewGame() {
    // Implement logic to start a new game
}

function showAbout() {
    var modal = document.getElementById("aboutModal");
    modal.style.display = "block";
}

function closeAboutModal() {
    var modal = document.getElementById("aboutModal");
    modal.style.display = "none";
}

// Close the about modal if the user clicks outside of it
window.onclick = function(event) {
    var modal = document.getElementById("aboutModal");
    if (event.target == modal) {
        modal.style.display = "none";
    }
};
