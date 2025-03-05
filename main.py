import os,discord,asyncio
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
bot = commands.Bot(command_prefix=";",intents=intents)





#Saves the db in google drive one time per day
async def save_db_hourly():
    while True:
        now = datetime.now()
        # Calculate time until the next 24-hour interval
        next_run = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        delay = (next_run - now).total_seconds()

        await asyncio.sleep(delay)
        await gDriveManager.save_db(DB_PATH,FOLDER_ID)
        print("Checked db updates")
        



async def insert_member(member:discord.Member):
    db = Db(DB_PATH)

    #need_img_save = True

    image_path = "to_check_avatar.png"
    correct_download = await GoogleDriveSaver.save_avatar_local(member.avatar.url,image_path) #type:ignore
    image_hash = Utils.calculate_hash(image_path)

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


#######################################
###------------COMMMANDS------------###
#######################################

#Command to send to a user all his names in a dm
@bot.command(name="yo",help="Envia todos tus nombres anteriores por dm")
async def get_last_names(ctx):
    print("Names command detected")
    standard_out = "## Todos tus nombres:\nid\tname\n"
    try:
        db = Db(DB_PATH)
        all_names = db.get_all_user_id_and_name(ctx.author.name)
        if all_names == []:
            raise NoLastNames
        message = standard_out + "\n".join([str(i[0])+"\t"+str(i[1]) for i in all_names])
        for chunk in [message[i:i+2000] for i in range(0, len(message), 2000)]:
            await ctx.author.send(chunk)
            
        await ctx.send("Te envio los nombre por privado!")  # Optional feedback in the server
    
    except discord.Forbidden:
        await ctx.send("I couldn't send you a DM. Please check your privacy settings!")
    
    except NoLastNames:
        await ctx.send("You don't have past names")

#Send a chart with who has had more different names
@bot.command(name="grafico",help="Grafico con nombres por usuario")
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
        plt.clf()
        
        #Send the photo
        file = discord.File(graph_file_name, filename=graph_file_name)
        await ctx.send(file=file)

        os.remove(graph_file_name) #Delete the graphic from the repo

    except discord.Forbidden:
        pass

#Send a message with the amount of names that every user have had
@bot.command(name="stats",help="Ranking: cantidad de nombres por usuario")
async def get_stats(ctx):
    db = Db(DB_PATH)
    info = db.get_names_per_user()

    position = 1
    returning_str = "## Nombres por usuario\n"
    
    for i in info:
        returning_str += str(position) + ". " + str(i[0]) + ": " + str(i[1]) + " nombres\n"
        position += 1
    
    await ctx.send(returning_str)

#Send the image with the gotten id
@bot.command(name="foto",help="Devuelve la foto con ese id. Se puede combinar con stats para saber los ids")
@commands.has_role(1312916494757396500) #Verge Esports
async def return_photo(ctx,message:str):
    db = Db(DB_PATH)

    try:
        image_name = db.get_img_name(message)
        
        await gDriveManager.download_image(image_name,FOLDER_ID)

        file = discord.File(image_name, filename=image_name)
        await ctx.author.send(image_name,file=file)

        os.remove(image_name)
        
        print("Image sent")
    
    except Exception:
        await ctx.author.send("Image not found")

#######################################
###-------------EVENTS--------------###
#######################################

@bot.event
async def on_member_update(before:discord.Member,after:discord.Member):
    print("Changes detected")
    await insert_member(after)


@bot.event
async def on_ready():
    asyncio.create_task(save_db_hourly())
    print(f'Logged in as {client.user}!')
    
    

#client.run(DISCORD_TOKEN)
bot.run(DISCORD_TOKEN)
