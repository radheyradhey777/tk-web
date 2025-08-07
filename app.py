from flask import Flask, request, render_template
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")  # Secure method

@app.route('/', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        product = request.form['product_name']
        price = request.form['price']
        contact = request.form['contact_details']

        content = (
            "**📦 New Ticket Submitted**\n"
            f"**Product Name:** {product}\n"
            f"**Price:** {price}\n"
            f"**Contact Details:**\n```{contact}```"
        )

        # Send to Discord
        requests.post(DISCORD_WEBHOOK_URL, json={"content": content})

        return "✅ Ticket submitted successfully!"
    return render_template('form.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)  # Required for Render
