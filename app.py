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
    user_ip = request.remote_addr

    if request.method == "POST":
        now = time.time()

        if user_ip in ip_cooldowns and now - ip_cooldowns[user_ip] < COOLDOWN_SECONDS:
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
                        {"name": "👤 Full Name", "value": full_name, "inline": True},
                        {"name": "📧 Email", "value": email, "inline": True},
                        {"name": "📱 Mobile Number", "value": mobile, "inline": True},
                        {"name": "📦 Product Name", "value": product, "inline": True},
                        {"name": "💳 Payment Method", "value": payment_method, "inline": True},
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

        ip_cooldowns[user_ip] = now
        return redirect("/success")

    return render_template("index.html")

@app.route("/success")
def success():
    return "✅ Submitted Successfully! We will contact you soon."

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
