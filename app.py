from flask import Flask, request, render_template
import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import asyncio
import time

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))

app = Flask(__name__)

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)
loop = asyncio.get_event_loop()

# 🔒 IP blocking storage
ip_submissions = {}
ip_blocked = {}
MAX_SUBMISSIONS = 3
BLOCK_DURATION = 3 * 24 * 60 * 60  # 3 days in seconds

@bot.event
async def on_ready():
    print(f"[Bot] Logged in as {bot.user}")

@app.route('/')
def home():
    return '''
    <h2>Submit Ticket</h2>
    <form method="POST" action="/submit">
        Your Name: <input name="name"><br>
        Email: <input name="email"><br>
        Mobile Number: <input name="mobile"><br>
        Payment Method:
            <select name="payment">
                <option>UPI</option>
                <option>GPay</option>
                <option>Paytm</option>
                <option>PhonePe</option>
                <option>Fampay</option>
            </select><br>
        Website/Service: <input name="website"><br>
        <input type="submit" value="Submit">
    </form>
    '''

@app.route('/submit', methods=['POST'])
def submit():
    ip = request.remote_addr

    # 🔒 Blocked IP check
    if ip in ip_blocked and time.time() < ip_blocked[ip]:
        return "⛔ Your IP is blocked for spamming. Try again later."

    # 🔒 Count submissions
    ip_submissions[ip] = ip_submissions.get(ip, 0) + 1
    if ip_submissions[ip] > MAX_SUBMISSIONS:
        ip_blocked[ip] = time.time() + BLOCK_DURATION
        return "🚫 You have been blocked for 3 days due to spamming."

    # Form data
    name = request.form['name']
    email = request.form['email']
    mobile = request.form['mobile']
    payment = request.form['payment']
    website = request.form['website']

    message = f"""**🎫 New Ticket Submitted**
> 👤 Name: {name}
> 📧 Email: {email}
> 📱 Mobile: {mobile}
> 💸 Payment: {payment}
> 🌐 Service: {website}
"""

    loop.create_task(send_discord_message(message))
    return "✅ Ticket submitted successfully!"

async def send_discord_message(msg):
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if channel:
        await channel.send(msg)
    else:
        print("[Bot] Channel not found")

def run_discord_bot():
    loop.create_task(bot.start(DISCORD_TOKEN))

run_discord_bot()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 5000)))
