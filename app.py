from flask import Flask, request, render_template_string
import json, time, os
from dotenv import load_dotenv
from bot import queue_message

app = Flask(__name__)
load_dotenv()

COOLDOWN_SECONDS = 3 * 24 * 60 * 60  # 3 days
IP_LOG_FILE = "ip_log.json"

def get_ip():
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    return request.remote_addr

def is_spam(ip):
    try:
        with open(IP_LOG_FILE, 'r') as f:
            ip_data = json.load(f)
    except:
        ip_data = {}
    return time.time() - ip_data.get(ip, 0) < COOLDOWN_SECONDS

def log_ip(ip):
    try:
        with open(IP_LOG_FILE, 'r') as f:
            ip_data = json.load(f)
    except:
        ip_data = {}
    ip_data[ip] = time.time()
    with open(IP_LOG_FILE, 'w') as f:
        json.dump(ip_data, f)

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        ip = get_ip()
        if is_spam(ip):
            return "❌ You already submitted a ticket. Please wait 3 days."

        name = request.form.get("name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        payment = request.form.get("payment")
        website = request.form.get("website") or "Not provided"

        log_ip(ip)

        message = (
            f"**👤 Name:** {name}\n"
            f"📧 **Email:** {email}\n"
            f"📱 **Mobile:** {mobile}\n"
            f"💳 **Payment Method:** {payment}\n"
            f"🌐 **Website:** {website}\n"
            f"🌍 **IP:** {ip}"
        )

        queue_message(message)
        return "✅ Ticket submitted successfully!"

    return render_template_string(open("form.html").read())

if __name__ == "__main__":
    import bot
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
