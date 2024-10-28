# bot.py
import os
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)

client.run(str(TOKEN))

def main():
    pass



if __name__ == "__main__":
    main()