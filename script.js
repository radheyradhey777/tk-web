// 1. "View" the link by selecting it with its ID
const myLink = document.getElementById('myLink');

// 2. Read its URL and log it to the console
console.log("The link's URL is:", myLink.href);

// 3. Change the link's URL to a Pterodactyl panel URL
myLink.href = 'https://gpanel.coramtix.in/';

// 4. Change the text of the link
myLink.textContent = 'Go to Pterodactyl Panel';
