import discord
import asyncio
import os
import json
import time
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)

message_queue = asyncio.Queue()

# IP cooldown logic
COOLDOWN_SECONDS = 3 * 24 * 60 * 60  # 3 days in seconds
IP_LOG_FILE = "ip_log.json"

def load_ip_data():
    try:
        with open(IP_LOG_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_ip_data(data):
    with open(IP_LOG_FILE, 'w') as f:
        json.dump(data, f)

def is_ip_blocked(ip):
    ip_data = load_ip_data()
    last_time = ip_data.get(ip, 0)
    return time.time() - last_time < COOLDOWN_SECONDS

def log_ip(ip):
    ip_data = load_ip_data()
    ip_data[ip] = time.time()
    save_ip_data(ip_data)

# This function will be used by the Flask app
def queue_message(content, ip=None):
    if ip:
        if is_ip_blocked(ip):
            print(f"⛔ Blocked IP tried to send ticket: {ip}")
            return False
        log_ip(ip)
    asyncio.run_coroutine_threadsafe(message_queue.put(content), client.loop)
    return True

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Invalid channel ID")
        return

    while True:
        message = await message_queue.get()
        try:
            embed = discord.Embed(
                title="📩 New Ticket Submitted",
                description=message,
                color=discord.Color.dark_blue()
            )
            await channel.send(embed=embed)
            print("✅ Ticket sent to Discord")
        except Exception as e:
            print(f"❌ Error sending to Discord: {e}")
        await asyncio.sleep(1)

def run_bot():
    client.run(TOKEN)
