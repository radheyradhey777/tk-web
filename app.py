from flask import Flask, render_template, request
import discord
from discord.ext import commands
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.messages = True
bot = commands.Bot(command_prefix="!", intents=intents)

app = Flask(__name__)
ip_submissions = {}

BLOCK_SECONDS = 3 * 24 * 60 * 60  # 3 days

@app.route("/", methods=["GET", "POST"])
def index():
    ip = request.remote_addr
    now = time.time()

    if ip in ip_submissions and now - ip_submissions[ip] < BLOCK_SECONDS:
        return "⛔ You have already submitted a ticket. Try again later."

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

        async def send():
            await bot.wait_until_ready()
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(embed=embed)

        bot.loop.create_task(send())

        ip_submissions[ip] = now
        return "✅ Ticket submitted successfully!"

    return render_template("index.html")

@bot.event
async def on_ready():
    print(f"✅ Discord bot logged in as {bot.user}")

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run(TOKEN)
