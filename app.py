from flask import Flask, render_template, request, redirect, request, abort
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
import threading
import time
import json

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
COOLDOWN_FILE = "cooldowns.json"
COOLDOWN_SECONDS = 3 * 24 * 60 * 60  # 3 days

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
app = Flask(__name__)

# Load cooldown data
if os.path.exists(COOLDOWN_FILE):
    with open(COOLDOWN_FILE, "r") as f:
        cooldowns = json.load(f)
else:
    cooldowns = {}

@bot.event
async def on_ready():
    print(f"Bot connected as {bot.user}")

@app.route("/", methods=["GET", "POST"])
def index():
    ip = request.remote_addr

    now = time.time()
    last_submission = cooldowns.get(ip, 0)

    if now - last_submission < COOLDOWN_SECONDS:
        return f"<h3>🚫 You already submitted a ticket from this IP. Try again after 3 days.</h3>"

    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        mobile = request.form["mobile"]
        payment = request.form["payment"]
        website = request.form["website"]

        embed = discord.Embed(title="🎟️ New Ticket Submitted", color=0x3498db)
        embed.add_field(name="👤 Name", value=name, inline=False)
        embed.add_field(name="📧 Email", value=email, inline=False)
        embed.add_field(name="📱 Mobile", value=mobile, inline=False)
        embed.add_field(name="💳 Payment Method", value=payment, inline=False)
        embed.add_field(name="🌐 Website", value=website, inline=False)

        async def send_embed():
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)

        bot.loop.create_task(send_embed())

        # Save the current submission time
        cooldowns[ip] = now
        with open(COOLDOWN_FILE, "w") as f:
            json.dump(cooldowns, f)

        return "<h3>✅ Ticket submitted successfully!</h3>"

    return render_template("index.html")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
