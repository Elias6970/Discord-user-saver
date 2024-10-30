import sqlite3,pytz,hashlib,aiohttp,os
import discord
from datetime import datetime

class Db:
    def __init__(self,db_path) -> None:
        self.db_path = db_path
        self.table_name = "NAMES"
        self.connector = sqlite3.connect(db_path)
        self.cursor = self.connector.cursor()

        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name}(ID INTEGER PRIMARY KEY AUTOINCREMENT,USER TEXT, NAME TEXT, IMAGE TEXT, CREATED_AT DATE)")
        self.connector.commit()

    
    def insert(self,user:str,name:str,image:str) -> bool:
        current_time = datetime.now(pytz.timezone('Europe/Madrid')).strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(f"INSERT INTO {self.table_name}(user,name,image,created_at) VALUES (?,?,?,?)",(user,name,image,current_time))

        self.connector.commit()

        if self.cursor.rowcount > 0:
            return True
        return False
    
    #Check if a user,name,image exists
    def exists(self,user:str,name:str,image:str) -> bool:
        select = self.cursor.execute(f"SELECT ID FROM {self.table_name} WHERE USER = ? AND NAME = ? AND IMAGE = ?",(user,name,image)).fetchone()
        if select == None:
            return False
        return True

    #Get the last info for a memeber
    #Returns a tuple with (user,name,image)
    def get_last_info(self,user:str):
        select = self.cursor.execute(f"SELECT USER,NAME,IMAGE FROM {self.table_name} WHERE USER = ? ORDER BY CREATED_AT DESC LIMIT 1",(user,)).fetchone()
        return select
    

    def close(self):
        self.connector.commit()
        self.connector.close()


class ImageDownlader:
    @staticmethod
    async def save_avatar(url,path):
        avatar_url = url  # Get the avatar URL
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    with open(path, 'wb') as f:
                        f.write(await response.read())  # Save the image to a file
                    return True
        return False
    



