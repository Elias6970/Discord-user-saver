# bot.py
import os
import hashlib
import discord
from dotenv import load_dotenv
from utils import *

load_dotenv()
DISCORD_TOKEN = str(os.getenv('DISCORD_TOKEN'))
SERVER_ID = str(os.getenv('SERVER_ID'))
DB_PATH = str(os.getenv('DB_PATH'))
FOLDER_ID = str(os.getenv('FOLDER_ID'))
KEYNAME_FILE = str(os.getenv('KEYNAME_FILE'))

image_manager = ImageManager(KEYNAME_FILE) #Mange the google drive save images


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

    #need_img_save = True

    image_path = "to_check_avatar.png"
    correct_download = await ImageManager.save_avatar_local(member.avatar.url,image_path) #type:ignore
    image_hash = calculate_hash(image_path)

    try:
        last_user,last_name,last_image_path,last_image_hash = db.get_last_info(member.name) # Can throw error if the db is empty or the user doesn't exists

        if correct_download == False:
            return False
        if last_user == member.name and last_name == member.display_name and last_image_hash == image_hash:
            return False

        #This is only if you don't want to have repeated photos
        #if last_image_hash == image_hash:
            #image_path = last_image_path
            #need_img_save = False

    except TypeError as e:
        pass
    
    
    id = db.get_next_id()
    img_name = Utils.get_img_name(str(id),member.name,member.display_name)

    db.insert(member.name,member.display_name,img_name,image_hash)
    await image_manager.save_image(img_name,image_path,FOLDER_ID)

    os.remove(image_path)

    db.close()


@client.event
async def on_member_update(before:discord.Member,after:discord.Member):
    print("Changes detected")
    await insert_member(after)
    print()


@client.event
async def on_ready():
    print(f'Logged in as {client.user}!')
    

client.run(DISCORD_TOKEN)

