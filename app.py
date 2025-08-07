from flask import Flask, request, render_template
import requests
import os

app = Flask(__name__)

# Replace with your actual webhook
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

@app.route('/', methods=['GET', 'POST'])
def ticket_form():
    if request.method == 'POST':
        product = request.form.get('product_name')
        price = request.form.get('price')
        contact = request.form.get('contact_details')

        content = (
            "**📦 New Ticket Submitted**\n"
            f"**Product Name:** {product}\n"
            f"**Price:** {price}\n"
            f"**Contact Details:**\n```{contact}```"
        )

        data = {"content": content}

        # Send to Discord via webhook
        requests.post(DISCORD_WEBHOOK_URL, json=data)

        return "✅ Ticket submitted and sent to Discord!"
    return render_template('form.html')

if __name__ == '__main__':
    app.run()
