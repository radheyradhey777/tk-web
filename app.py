from flask import Flask, render_template, request, redirect
import os
import requests
import json
import time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
COOLDOWN_SECONDS = 5 * 24 * 60 * 60
IP_LOG_FILE = "ip_log.json"

# Load the IP log from a file if it exists
if os.path.exists(IP_LOG_FILE):
    with open(IP_LOG_FILE, "r") as f:
        ip_log = json.load(f)
else:
    ip_log = {}

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        # --- Spam and Cooldown Checks ---
        if request.form.get("honeypot"):
            return "❌ Spam detected.", 400

        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        current_time = time.time()

        if user_ip in ip_log:
            time_diff = current_time - ip_log[user_ip]
            if time_diff < COOLDOWN_SECONDS:
                remaining_days = int((COOLDOWN_SECONDS - time_diff) // 86400) + 1 # +1 to round up
                return f"❌ You can only submit one ticket every 5 days. Try again in {remaining_days} day(s).", 429

        # --- Form Data Collection ---
        name = request.form.get("name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        product = request.form.get("product")
        payment = request.form.get("payment")
        upi = request.form.get("upi")
        description = request.form.get("description")

        # ⭐️⭐️⭐️ START OF MODIFIED SECTION ⭐️⭐️⭐️

        # --- Product Validation ---
        # Only allow submissions for "Enhance" or "Premium" products.
        # This check is case-insensitive.
        allowed_products = ["enhance", "premium"]
        if not product or product.lower() not in allowed_products:
            return "❌ Invalid product selected. Please choose either Enhance or Premium.", 400

        # --- Discord Embed Creation ---
        # Create the embed object, a dictionary that follows Discord's API structure.
        embed = {
            "title": "📩 New Ticket Submitted",
            "description": f"A new support ticket has been received from **{name}**.",
            "color": 3447003,  # A nice blue color in decimal format
            "fields": [
                {
                    "name": "👤 Full Name",
                    "value": name,
                    "inline": True
                },
                {
                    "name": "📧 Email",
                    "value": f"||{email}||", # Use spoiler tags for privacy
                    "inline": True
                },
                {
                    "name": "📱 Mobile Number",
                    "value": f"||{mobile}||", # Use spoiler tags for privacy
                    "inline": True
                },
                {
                    "name": "🛍️ Product Name",
                    "value": product,
                    "inline": False # Set to False to take the full width
                },
                {
                    "name": "💳 Payment Method",
                    "value": payment,
                    "inline": True
                },
                {
                    "name": "🏦 UPI ID",
                    "value": f"||{upi}||" if upi else "N/A", # Handle empty UPI and use spoiler tags
                    "inline": True
                },
                {
                    "name": "📝 Description",
                    "value": description,
                    "inline": False
                }
            ],
            "footer": {
                "text": f"IP Address: {user_ip}"
            },
            "timestamp": datetime.utcnow().isoformat() # Adds a timestamp to the embed
        }

        # The main payload sent to Discord. It contains a list of embeds.
        payload = {
            "username": "Support Bot", # You can customize the bot's name
            "avatar_url": "https://i.imgur.com/fKL31aD.png", # You can customize the bot's avatar
            "embeds": [embed] # The 'embeds' key must be a list of embed objects
        }

        try:
            # Send the request to the webhook URL with the JSON payload
            response = requests.post(WEBHOOK_URL, json=payload)
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx)
        except Exception as e:
            # Log the error for debugging instead of showing it to the user
            print(f"Error sending to Discord: {e}")
            return "❌ There was an error submitting your ticket. Please try again later.", 500
        
        # ⭐️⭐️⭐️ END OF MODIFIED SECTION ⭐️⭐️⭐️

        # --- Log IP and Redirect ---
        ip_log[user_ip] = current_time
        with open(IP_LOG_FILE, "w") as f:
            json.dump(ip_log, f)

        return redirect("/?success=1")

    # Render the form template for GET requests
    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

