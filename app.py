from flask import Flask, render_template, request, redirect
import os, requests, json, time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

COOLDOWN_SECONDS = 5 * 24 * 60 * 60  # 5 days
IP_LOG_FILE = "ip_log.json"

# Load existing IP logs
if os.path.exists(IP_LOG_FILE):
    with open(IP_LOG_FILE, "r") as f:
        ip_log = json.load(f)
else:
    ip_log = {}

@app.route("/", methods=["GET", "POST"])
def form():
    if request.method == "POST":
        if request.form.get("honeypot"):  # Anti-spam honeypot
            return "Spam detected.", 400

        user_ip = request.remote_addr
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

        content = (
            f"📩 **New Ticket Submitted**\n\n"
            f"👤 **Name:** {name}\n"
            f"📧 **Email:** {email}\n"
            f"🔗 **Contact ({contact_method}):** {contact_value}\n"
            f"🛒 **Product:** {product}\n"
            f"💳 **Payment Method:** {payment}\n"
            f"🌐 **IP Address:** {user_ip}"
        )

        try:
            requests.post(WEBHOOK_URL, json={"content": content})
        except Exception as e:
            return f"Error sending to Discord: {e}", 500

        ip_log[user_ip] = current_time
        with open(IP_LOG_FILE, "w") as f:
            json.dump(ip_log, f)

        return redirect("/?success=1")

    return render_template("index.html")

# ✅ Render 24/7 hosting
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
