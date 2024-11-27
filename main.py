# bot.py
import os,hashlib,discord,asyncio
import matplotlib.pyplot as plt
from discord.ext import commands
from datetime import timedelta
from dotenv import load_dotenv
from utils import *

load_dotenv(override=True)
DISCORD_TOKEN = str(os.getenv('DISCORD_TOKEN'))
SERVER_ID = str(os.getenv('SERVER_ID'))
DB_PATH = str(os.getenv('DB_PATH'))
FOLDER_ID = str(os.getenv('FOLDER_ID'))
KEYNAME_FILE = str(os.getenv('KEYNAME_FILE'))

gDriveManager = GoogleDriveSaver(KEYNAME_FILE) #Mange the google drive save images


intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)
bot = commands.Bot(command_prefix="!",intents=intents)


def calculate_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


#Saves the db in google drive one time per day
async def save_db_daily():
    while True:
        now = datetime.now()
        # Calculate time until the next 24-hour interval
        next_run = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        delay = (next_run - now).total_seconds()
        await asyncio.sleep(delay)
        await gDriveManager.save_db(DB_PATH,FOLDER_ID)
        



async def insert_member(member:discord.Member):
    db = Db(DB_PATH)

    #need_img_save = True

    image_path = "to_check_avatar.png"
    correct_download = await GoogleDriveSaver.save_avatar_local(member.avatar.url,image_path) #type:ignore
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
    await gDriveManager.save_image(img_name,image_path,FOLDER_ID)

    os.remove(image_path)

    db.close()

@bot.command(name="yo")
async def get_last_names(ctx):
    print("Names command detected")
    standard_out = "Todos tus nombres:\n\t"
    try:
        db = Db(DB_PATH)
        all_names = db.get_all_user_names(ctx.author.name)
        if all_names == []:
            raise NoLastNames
        
        await ctx.author.send(standard_out + "\n".join(all_names))
        await ctx.send("Te envio los nombre por privado!")  # Optional feedback in the server
    
    except discord.Forbidden:
        await ctx.send("I couldn't send you a DM. Please check your privacy settings!")
    
    except NoLastNames:
        await ctx.send("You don't have past names")

#Send a chart with who has more different names
@bot.command(name="grafico")
async def get_graphic_names(ctx):
    print("Graphic command")
    try:
        db = Db(DB_PATH)
        graph_file_name = "graph.png"
        info = db.get_names_per_user()

        values = list(map(lambda x: x[1],info))
        labels = list(map(lambda x: x[0],info))

        plt.pie(x=values,labels=labels,autopct='%1.1f%%', 
            startangle=180, pctdistance=0.85,
            wedgeprops={'edgecolor': 'black'},
            textprops={'fontsize': 9})
        plt.title("Nombres por usuario")
        plt.axis('equal')
        plt.savefig(graph_file_name)

        #Send the photo
        file = discord.File(graph_file_name, filename=graph_file_name)
        await ctx.send(file=file)

        os.remove(graph_file_name) #Delete the graphic from the repo

    except discord.Forbidden:
        pass

@bot.event
async def on_member_update(before:discord.Member,after:discord.Member):
    print("Changes detected")
    await insert_member(after)


@bot.event
async def on_ready():
    asyncio.create_task(save_db_daily())
    print(f'Logged in as {client.user}!')
    

#client.run(DISCORD_TOKEN)
bot.run(DISCORD_TOKEN)
