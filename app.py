from flask import Flask, render_template, request, redirect, make_response
import os, requests, json, time
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = Flask(__name__)

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY")
COOLDOWN_SECONDS = 5 * 24 * 60 * 60
IP_LOG_FILE = "ip_log.json"

def load_ip_log():
    if os.path.exists(IP_LOG_FILE):
        try:
            with open(IP_LOG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_ip_log(ip_log):
    with open(IP_LOG_FILE, "w") as f:
        json.dump(ip_log, f, indent=4)

ip_log = load_ip_log()

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        # --- reCAPTCHA Verification ---
        recaptcha_response = request.form.get("g-recaptcha-response")
        if not recaptcha_response:
            return "❌ Please complete the reCAPTCHA.", 400
        
        verify_url = "https://www.google.com/recaptcha/api/siteverify"
        payload = {
            "secret": RECAPTCHA_SECRET_KEY,
            "response": recaptcha_response,
            "remoteip": request.remote_addr
        }
        r = requests.post(verify_url, data=payload)
        result = r.json()

        if not result.get("success"):
            return "❌ reCAPTCHA verification failed. Please try again.", 400

        # --- Spam cooldown ---
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        current_time = time.time()

        if user_ip in ip_log:
            time_diff = current_time - ip_log[user_ip]
            if time_diff < COOLDOWN_SECONDS:
                remaining_seconds = COOLDOWN_SECONDS - time_diff
                days = int(remaining_seconds // 86400)
                hours = int((remaining_seconds % 86400) // 3600)
                minutes = int((remaining_seconds % 3600) // 60)
                remaining_time_str = f"{days} day(s)" if days > 0 else f"{hours} hour(s)" if hours > 0 else f"{minutes} minute(s)"
                return make_response(f"❌ Please try again in {remaining_time_str}.", 429)

        # --- Collect form data ---
        name = request.form.get("name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        product = request.form.get("product")
        payment = request.form.get("payment")

        if not all([name, email, mobile, product, payment]):
            return "❌ Please fill out all required fields.", 400

        embed = {
            "title": "📦 New Order Received",
            "description": f"A new order has been placed by **{name}**.",
            "color": 3447003,
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

        payload = {
            "username": "Order Bot",
            "avatar_url": "https://i.imgur.com/fKL31aD.png",
            "embeds": [embed]
        }

        try:
            response = requests.post(WEBHOOK_URL, json=payload)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Error sending to Discord: {e}")
            return "❌ Server error while submitting your order.", 500

        ip_log[user_ip] = current_time
        save_ip_log(ip_log)
        return redirect("/?success=true")

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
