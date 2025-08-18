// Replace with your GitHub username and repository name
const REPO_OWNER = 'radheyradhey777';
const REPO_NAME = 'tk-web';

let adminToken = '';

// Admin Login function
function loginAdmin() {
    const tokenInput = document.getElementById('admin-token');
    adminToken = tokenInput.value;
    if (adminToken) {
        document.getElementById('token-login').style.display = 'none';
        document.getElementById('ticket-list').style.display = 'block';
        fetchTickets();
    } else {
        alert('Please enter a valid token.');
    }
}

// Function to submit a new ticket
document.getElementById('ticket-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const subject = document.getElementById('subject').value;
    const message = document.getElementById('message').value;

    const ticketData = {
        title: subject,
        body: message,
    };

    // Use a public API key or a serverless function for a real app.
    // For this simple example, we'll assume the admin is submitting it.
    // The admin's PAT is needed for any API call to create an issue.
    if (!adminToken) {
        alert('Please log in as an admin to submit a ticket.');
        return;
    }

    try {
        const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${adminToken}`, 
            },
            body: JSON.stringify(ticketData),
        });

        if (response.ok) {
            alert('Ticket submitted successfully!');
            document.getElementById('ticket-form').reset();
        } else {
            const error = await response.json();
            alert(`Error submitting ticket: ${error.message}`);
        }
    } catch (error) {
        console.error('Network error:', error);
        alert('An error occurred. Please try again.');
    }
});

// Function to fetch and display tickets for the admin
async function fetchTickets() {
    const ticketsContainer = document.getElementById('tickets-container');
    ticketsContainer.innerHTML = '<li>Loading tickets...</li>';

    try {
        const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues`, {
            headers: {
                'Authorization': `Bearer ${adminToken}`,
            }
        });

        if (response.ok) {
            const issues = await response.json();
            ticketsContainer.innerHTML = ''; // Clear previous tickets
            if (issues.length === 0) {
                ticketsContainer.innerHTML = '<li>No tickets found.</li>';
            } else {
                issues.forEach(issue => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <h4>${issue.title} (#${issue.number})</h4>
                        <p>${issue.body}</p>
                        <p>Status: <strong>${issue.state}</strong></p>
                        <button onclick="closeTicket(${issue.number})">Delete/Close Ticket</button>
                        <hr>
                    `;
                    ticketsContainer.appendChild(li);
                });
            }
        } else {
            ticketsContainer.innerHTML = '<li>Failed to load tickets. Check your token.</li>';
        }
    } catch (error) {
        ticketsContainer.innerHTML = '<li>Error fetching tickets.</li>';
    }
}

// Function to "delete" (close) a ticket
async function closeTicket(issueNumber) {
    if (!adminToken) {
        alert('You must be logged in as an admin to do this.');
        return;
    }

    const data = { state: 'closed' };

    try {
        const response = await fetch(`https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues/${issueNumber}`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${adminToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });

        if (response.ok) {
            alert('Ticket deleted (closed) successfully!');
            fetchTickets(); // Refresh the list
        } else {
            alert('Failed to delete ticket.');
        }
    } catch (error) {
        console.error('Error closing ticket:', error);
    }
}
