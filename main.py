# bot.py
import os
import hashlib
import discord
import asyncio
from dotenv import load_dotenv
from utils import *

load_dotenv()
DISCORD_TOKEN = str(os.getenv('DISCORD_TOKEN'))
SERVER_ID = str(os.getenv('SERVER_ID'))
DB_PATH = str(os.getenv('DB_PATH'))

intents = discord.Intents.default()
intents.members = True

client = discord.Client(intents=intents)


def calculate_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()




async def insert_member(member:discord.Member):
    db = Db(DB_PATH)

    image_path = "to_check_avatar.png"
    print(member.avatar.url) #type:ignore
    correct_download = await ImageDownlader.save_avatar(member.avatar.url,image_path) #type:ignore
    image_hash = calculate_hash(image_path)

    try:
        print(member.name)
        last_user,last_name,last_image_path = db.get_last_info(member.name) # Can throw error if the db is empty or the user doesn't exists
        last_image_hash = calculate_hash(last_image_path)
        
            

        if correct_download == False:
            return False
        if last_user == member.name and last_name == member.display_name and last_image_hash == image_hash:
            return False

        if last_image_hash == image_hash:
            image_path = last_image_path

    except Exception as e:
        print(e,";",type(e))
    
    print(db.insert(member.name,member.display_name,image_path))
    db.close()


@client.event
async def on_member_update(before:discord.Member,after:discord.Member):
    print("Changes detected")
    await insert_member(after)
    #print(f"Before:{before.name}#{before.discriminator};{before.display_name},{before.display_avatar}")
    #print(f"After:{after.name}#{after.discriminator};{after.display_name},{after.display_avatar}")
    print("\n")


@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')
    #client.loop.create_task(fetch_and_print_members())  # Start the member fetching task

client.run(DISCORD_TOKEN)

