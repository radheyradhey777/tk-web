from flask import Flask, render_template, request, redirect, make_response
import os
import requests
import json
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from a .env file
load_dotenv()

# --- FLASK APP INITIALIZATION ---
# By default, Flask looks for HTML files in a folder named 'templates'.
# Make sure your index.html file is inside a 'templates' folder.
app = Flask(__name__)


# --- CONFIGURATION ---
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
# Cooldown period set to 5 days (in seconds)
COOLDOWN_SECONDS = 5 * 24 * 60 * 60 
IP_LOG_FILE = "ip_log.json"

# --- IP LOG MANAGEMENT ---
def load_ip_log():
    """Loads the IP log from the JSON file."""
    if os.path.exists(IP_LOG_FILE):
        try:
            with open(IP_LOG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {} # Return empty dict if file is corrupted
    return {}

def save_ip_log(ip_log):
    """Saves the IP log to the JSON file."""
    with open(IP_LOG_FILE, "w") as f:
        json.dump(ip_log, f, indent=4)

# Load the log when the application starts
ip_log = load_ip_log()

@app.route("/", methods=["GET", "POST"])
def form():
    """Handles the form submission and renders the form page."""
    if request.method == "POST":
        # --- 1. SPAM AND COOLDOWN CHECKS ---
        
        # Check the honeypot field for simple bot detection
        if request.form.get("honeypot"):
            return "❌ Spam detected.", 400

        # Get the user's real IP address, even if behind a proxy
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        current_time = time.time()

        # Check if the user is on cooldown
        if user_ip in ip_log:
            time_diff = current_time - ip_log[user_ip]
            if time_diff < COOLDOWN_SECONDS:
                remaining_seconds = COOLDOWN_SECONDS - time_diff
                # Calculate remaining days, hours, and minutes for a more user-friendly message
                days = int(remaining_seconds // 86400)
                hours = int((remaining_seconds % 86400) // 3600)
                minutes = int((remaining_seconds % 3600) // 60)
                
                # Construct a clear message
                if days > 0:
                    remaining_time_str = f"{days} day(s)"
                elif hours > 0:
                    remaining_time_str = f"{hours} hour(s)"
                else:
                    remaining_time_str = f"{minutes} minute(s)"

                error_message = f"❌ You can only submit one order every 5 days. Please try again in about {remaining_time_str}."
                return make_response(error_message, 429)

        # --- 2. FORM DATA COLLECTION ---
        # Collect data from the form fields. .get() is safer as it returns None if key is missing.
        name = request.form.get("name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        product = request.form.get("product")
        payment = request.form.get("payment")

        # Basic validation to ensure required fields are not empty
        if not all([name, email, mobile, product, payment]):
             return "❌ Please fill out all required fields.", 400

        # --- 3. DISCORD EMBED CREATION ---
        # Create a rich embed for the Discord message
        embed = {
            "title": "📦 New Order Received",
            "description": f"A new order has been placed by **{name}**.",
            "color": 3447003,  # A nice green color (hex #3498db)
            "fields": [
                {"name": "👤 Full Name", "value": name, "inline": True},
                {"name": "📧 Email", "value": f"||{email}||", "inline": True},
                {"name": "📱 Mobile Number", "value": f"||{mobile}||", "inline": True},
                {"name": "🛍️ Product Name", "value": f"```{product}```", "inline": False},
                {"name": "💳 Payment Method", "value": payment, "inline": False},
            ],
            "footer": {"text": f"Submitted from IP: {user_ip}"},
            "timestamp": datetime.utcnow().isoformat()
        }

        # The main payload to send to the Discord Webhook
        payload = {
            "username": "Order Bot",
            "avatar_url": "https://i.imgur.com/fKL31aD.png", # A generic bot avatar
            "embeds": [embed]
        }

        # --- 4. SEND TO DISCORD AND FINALIZE ---
        try:
            # Send the data to your Discord webhook URL
            response = requests.post(WEBHOOK_URL, json=payload)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
        except requests.exceptions.RequestException as e:
            print(f"Error sending data to Discord: {e}")
            return "❌ There was a server error while submitting your order. Please try again later.", 500
        
        # If successful, log the user's IP and submission time
        ip_log[user_ip] = current_time
        save_ip_log(ip_log)

        # Redirect to the same page with a success query parameter
        return redirect("/?success=true")

    # For GET requests, render the HTML form from the 'templates' folder.
    return render_template("index.html")

if __name__ == "__main__":
    # Use the PORT environment variable if available (common for hosting platforms)
    port = int(os.environ.get("PORT", 5000))
    # Running on 0.0.0.0 makes it accessible from other devices on the network
    app.run(host="0.0.0.0", port=port)

