from flask import Flask, render_template, request, redirect
import os
import requests
import json
import time
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
COOLDOWN_SECONDS = 5 * 24 * 60 * 60
IP_LOG_FILE = "ip_log.json"

if os.path.exists(IP_LOG_FILE):
    with open(IP_LOG_FILE, "r") as f:
        ip_log = json.load(f)
else:
    ip_log = {}

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        if request.form.get("honeypot"):
            return "❌ Spam detected.", 400

        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        current_time = time.time()

        if user_ip in ip_log:
            time_diff = current_time - ip_log[user_ip]
            if time_diff < COOLDOWN_SECONDS:
                remaining_days = int((COOLDOWN_SECONDS - time_diff) // 86400)
                return f"❌ You can only submit one ticket every 5 days. Try again in {remaining_days} day(s).", 429

        name = request.form.get("name")
        email = request.form.get("email")
        contact_method = request.form.get("contact")
        contact_value = request.form.get("contact_value")
        product = request.form.get("product")
        payment = request.form.get("payment")

        embed = {
            "title": "📩 New Ticket Submitted",
            "color": 0x000080,  # Navy Blue
            "fields": [
                {"name": "👤 Name", "value": name or "N/A", "inline": False},
                {"name": "📧 Email", "value": email or "N/A", "inline": False},
                {"name": f"🔗 Contact ({contact_method})", "value": contact_value or "N/A", "inline": False},
                {"name": "🛒 Product", "value": product or "N/A", "inline": False},
                {"name": "💳 Payment Method", "value": payment or "N/A", "inline": False},
                {"name": "🌐 IP Address", "value": user_ip, "inline": False}
            ]
        }

        try:
            response = requests.post(WEBHOOK_URL, json={"embeds": [embed]})

            if response.status_code == 429:
                try:
                    retry_after = response.json().get("retry_after", 2)
                except:
                    retry_after = 2
                time.sleep(retry_after)
                response = requests.post(WEBHOOK_URL, json={"embeds": [embed]})

            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            return f"❌ Error sending to Discord: {e}", 500
        except Exception as e:
            return f"❌ Unexpected error: {str(e)}", 500

        ip_log[user_ip] = current_time
        with open(IP_LOG_FILE, "w") as f:
            json.dump(ip_log, f)

        return redirect("/?success=1")

    return render_template("index.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
