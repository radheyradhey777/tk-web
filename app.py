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
                remaining_days = int((COOLDOWN_SECONDS - time_diff) // 86400) + 1
                return f"❌ You can only submit one ticket every 5 days. Try again in {remaining_days} day(s).", 429

        # --- Form Data Collection ---
        name = request.form.get("name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        product = request.form.get("product") # Now accepts any custom text
        payment = request.form.get("payment")
        upi = request.form.get("upi")
        description = request.form.get("description")

        # --- Discord Embed Creation ---
        embed = {
            "title": "📩 New Ticket Submitted",
            "description": f"A new support ticket has been received from **{name}**.",
            "color": 5814783,  # A nice blue color (hex #58b6ff)
            "fields": [
                {"name": "👤 Full Name", "value": name, "inline": True},
                {"name": "📧 Email", "value": f"||{email}||", "inline": True},
                {"name": "📱 Mobile Number", "value": f"||{mobile}||", "inline": True},
                {"name": "🛍️ Product Name", "value": product, "inline": False},
                {"name": "💳 Payment Method", "value": payment, "inline": True},
                {"name": "🏦 UPI ID", "value": f"||{upi}||" if upi else "N/A", "inline": True},
                {"name": "📝 Description", "value": description, "inline": False}
            ],
            "footer": {"text": f"IP Address: {user_ip}"},
            "timestamp": datetime.utcnow().isoformat()
        }

        payload = {
            "username": "Support Bot",
            "avatar_url": "https://i.imgur.com/fKL31aD.png",
            "embeds": [embed]
        }

        try:
            response = requests.post(WEBHOOK_URL, json=payload)
            response.raise_for_status()
        except Exception as e:
            print(f"Error sending to Discord: {e}")
            return "❌ There was an error submitting your ticket. Please try again later.", 500
        
        # --- Log IP and Redirect ---
        ip_log[user_ip] = current_time
        with open(IP_LOG_FILE, "w") as f:
            json.dump(ip_log, f)

        return redirect("/?success=1")

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

