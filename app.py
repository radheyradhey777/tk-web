from flask import Flask, render_template, request, redirect
import os, requests, time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
COOLDOWN_SECONDS = 3 * 24 * 60 * 60  # 3 days
ip_cooldowns = {}

@app.route("/", methods=["GET", "POST"])
def index():
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Do NOT block localhost (127.0.0.1 or ::1)
    is_localhost = user_ip in ["127.0.0.1", "::1"]

    if request.method == "POST":
        now = time.time()

        if not is_localhost and user_ip in ip_cooldowns:
            if now - ip_cooldowns[user_ip] < COOLDOWN_SECONDS:
                return "❌ You already submitted. Try again after 3 days."

        # Form fields
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        product = request.form.get("product")
        payment_method = request.form.get("payment_method")
        upi = request.form.get("upi")
        description = request.form.get("description")

        embed = {
            "embeds": [
                {
                    "title": "📝 New Order / Ticket Submitted",
                    "color": 0x2ecc71,
                    "fields": [
                        {"name": "👤 Full Name", "value": full_name or "N/A", "inline": True},
                        {"name": "📧 Email", "value": email or "N/A", "inline": True},
                        {"name": "📱 Mobile Number", "value": mobile or "N/A", "inline": True},
                        {"name": "📦 Product Name", "value": product or "N/A", "inline": True},
                        {"name": "💳 Payment Method", "value": payment_method or "N/A", "inline": True},
                        {"name": "📲 UPI ID", "value": upi or "N/A", "inline": True},
                        {"name": "📝 Description", "value": description or "No description provided", "inline": False}
                    ]
                }
            ]
        }

        try:
            response = requests.post(WEBHOOK_URL, json=embed)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f"❌ Error sending to Discord: {e}"

        if not is_localhost:
            ip_cooldowns[user_ip] = now

        return redirect("/success")

    return render_template("index.html")

@app.route("/success")
def success():
    return "✅ Submitted Successfully! We will contact you soon."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
