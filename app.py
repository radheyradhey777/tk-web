from flask import Flask, request, render_template
import requests
import os

app = Flask(__name__)
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        # Anti-spam honeypot check
        if request.form.get("bot_field"):
            return "❌ Spam detected."

        product = request.form.get('product_name')
        price = request.form.get('price')
        contact_type = request.form.get('contact_type')
        contact_value = request.form.get('contact_value')

        content = (
            "**📦 New Ticket Submitted**\n"
            f"**Product:** {product}\n"
            f"**Price:** {price}\n"
            f"**Contact ({contact_type}):** `{contact_value}`"
        )

        # Send to Discord
        try:
            requests.post(DISCORD_WEBHOOK_URL, json={"content": content})
        except:
            return "❌ Failed to send to Discord."

        return "✅ Ticket sent to Discord!"
    return render_template('form.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
