from flask import Flask, render_template, request, redirect, url_for, flash
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, TextAreaField, SelectField, HiddenField
from wtforms.validators import DataRequired, Email, Length, Optional
import os
import requests
import json
import time
from dotenv import load_dotenv
from datetime import datetime

# --- Configuration ---
load_dotenv()

app = Flask(__name__)
# ⭐️ SECRET_KEY is crucial for CSRF protection and session management.
#    It should be a long, random string.
app.config['SECRET_KEY'] = os.getenv("FLASK_SECRET_KEY", "a-default-fallback-secret-key-for-dev")
# ⭐️ Initialize CSRF protection for the app.
csrf = CSRFProtect(app)

# --- Constants & Global Variables ---
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
COOLDOWN_SECONDS = 5 * 24 * 60 * 60  # 5 days
IP_LOG_FILE = "ip_log.json"
MIN_SUBMISSION_TIME_SECONDS = 3 # ⭐️ Bots submit instantly. A human needs at least a few seconds.

# --- IP Log Loading ---
def load_ip_log():
    """Loads the IP log from a JSON file."""
    if os.path.exists(IP_LOG_FILE):
        try:
            with open(IP_LOG_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {} # Return empty dict if file is corrupted
    return {}

def save_ip_log(log_data):
    """Saves the IP log to a JSON file."""
    with open(IP_LOG_FILE, "w") as f:
        json.dump(log_data, f, indent=4)

ip_log = load_ip_log()

# --- Form Definition (Using Flask-WTF) ---
# ⭐️ Using a Form class provides validation, CSRF protection, and better organization.
class SupportForm(FlaskForm):
    name = StringField("Full Name", validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField("Email Address", validators=[DataRequired(), Email()])
    mobile = StringField("Mobile Number", validators=[DataRequired(), Length(min=10, max=15)])
    product = StringField("Product Name", validators=[DataRequired(), Length(min=2, max=100)])
    payment = SelectField("Payment Method", choices=[
        ('Credit Card', 'Credit Card'),
        ('Debit Card', 'Debit Card'),
        ('PayPal', 'PayPal'),
        ('UPI', 'UPI'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    upi = StringField("UPI ID", validators=[Optional(), Length(max=50)]) # Optional field
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10, max=1000)])

    # ⭐️ Security Honeypot: A field hidden by CSS that bots might fill out.
    honeypot = StringField()
    # ⭐️ Security Timestamp: To check how fast the form was submitted.
    submit_time = HiddenField()


# --- Routes ---
@app.route("/", methods=["GET", "POST"])
def form():
    support_form = SupportForm()
    
    if support_form.validate_on_submit():
        # validate_on_submit() checks if it's a POST request and if the form data is valid (including CSRF token)

        # --- Advanced Spam Checks ---
        # 1. Honeypot check
        if support_form.honeypot.data:
            # This field should be empty. If it has data, it's likely a bot.
            flash("Spam detected.", "error")
            return render_template("index.html", form=support_form)

        # 2. Time-based check
        try:
            start_time = float(support_form.submit_time.data)
            submission_duration = time.time() - start_time
            if submission_duration < MIN_SUBMISSION_TIME_SECONDS:
                # Form submitted too quickly, likely a bot.
                flash("Spam detected.", "error")
                return render_template("index.html", form=support_form)
        except (ValueError, TypeError):
            # Handle cases where timestamp is missing or invalid
            flash("Invalid form submission. Please try again.", "error")
            return render_template("index.html", form=support_form)

        # 3. IP Cooldown Check
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0].strip()
        current_time = time.time()
        if user_ip in ip_log:
            time_diff = current_time - ip_log[user_ip]
            if time_diff < COOLDOWN_SECONDS:
                remaining_days = int((COOLDOWN_SECONDS - time_diff) // 86400) + 1
                flash(f"You can only submit one ticket every 5 days. Try again in {remaining_days} day(s).", "error")
                return render_template("index.html", form=support_form, cooldown=True)

        # --- Process Valid Data and Send to Discord ---
        embed = {
            "title": "📩 New Ticket Submitted",
            "description": f"A new support ticket has been received from **{support_form.name.data}**.",
            "color": 3447003,
            "fields": [
                {"name": "👤 Full Name", "value": support_form.name.data, "inline": True},
                {"name": "📧 Email", "value": f"||{support_form.email.data}||", "inline": True},
                {"name": "📱 Mobile Number", "value": f"||{support_form.mobile.data}||", "inline": True},
                {"name": "🛍️ Product Name", "value": support_form.product.data, "inline": False},
                {"name": "💳 Payment Method", "value": support_form.payment.data, "inline": True},
                {"name": "🏦 UPI ID", "value": f"||{support_form.upi.data}||" if support_form.upi.data else "N/A", "inline": True},
                {"name": "📝 Description", "value": support_form.description.data, "inline": False}
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
            
            # Update IP log on successful submission
            ip_log[user_ip] = current_time
            save_ip_log(ip_log)
            
            flash("Your ticket has been submitted successfully!", "success")
            return redirect(url_for("form"))
        except Exception as e:
            flash(f"Error sending ticket: {e}", "error")

    # For GET requests or if form validation fails, render the template
    return render_template("index.html", form=support_form)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # Use debug=False in a production environment
    app.run(host="0.0.0.0", port=port, debug=True)

