import discord
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
client = discord.Client(intents=intents)
message_queue = asyncio.Queue()

def queue_message(content):
    asyncio.run_coroutine_threadsafe(message_queue.put(content), client.loop)

@client.event
async def on_ready():
    print(f"✅ Bot logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Invalid channel ID")
        return

    while True:
        message = await message_queue.get()
        embed = discord.Embed(
            title="🎟️ New Ticket Submitted",
            description=message,
            color=discord.Color.blue()
        )
        await channel.send(embed=embed)
        await asyncio.sleep(1)

def run_bot():
    client.run(TOKEN)

# Start bot when imported
if __name__ != "__main__":
    import threading
    threading.Thread(target=run_bot).start()
