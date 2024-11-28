import sqlite3,pytz,aiohttp,random,string
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

class Db:
    def __init__(self,db_path) -> None:
        self.db_path = db_path
        self.table_name = "NAMES"
        self.connector = sqlite3.connect(db_path)
        self.cursor = self.connector.cursor()

        self.cursor.execute(f"CREATE TABLE IF NOT EXISTS {self.table_name}(ID INTEGER PRIMARY KEY AUTOINCREMENT,USER TEXT, NAME TEXT, IMAGE TEXT, IMAGE_HASH, CREATED_AT DATE)")
        self.connector.commit()
    
    def __del__(self):
        self.close()

    #Return the id of the insert
    def insert(self,user:str,name:str,image:str,image_hash:str):
        current_time = datetime.now(pytz.timezone('Europe/Madrid')).strftime('%Y-%m-%d %H:%M:%S')
        self.cursor.execute(f"INSERT INTO {self.table_name}(user,name,image,created_at,image_hash) VALUES (?,?,?,?,?)",(user,name,image,current_time,image_hash))

        self.connector.commit()
        
        return self.cursor.lastrowid
    
    #Check if a user,name,image exists
    def exists(self,user:str,name:str,image:str) -> bool:
        select = self.cursor.execute(f"SELECT ID FROM {self.table_name} WHERE USER = ? AND NAME = ? AND IMAGE = ?",(user,name,image)).fetchone()
        if select == None:
            return False
        return True

    #Get the last info for a memeber
    #Returns a tuple with (user,name,image)
    def get_last_info(self,user:str):
        select = self.cursor.execute(f"SELECT USER,NAME,IMAGE,IMAGE_HASH FROM {self.table_name} WHERE USER = ? ORDER BY CREATED_AT DESC LIMIT 1",(user,)).fetchone()
        return select
    
    #Return a list with all user names
    def get_all_user_names(self,user:str) -> list:
        select = self.cursor.execute(f"SELECT NAME FROM {self.table_name} WHERE USER = ? ORDER BY CREATED_AT ASC",(user,)).fetchall()
        try:
            return [i[0] for i in select]
        except Exception:
            return []
    
    #Return the number of different names per user
    def get_names_per_user(self):
        select = self.cursor.execute(f"""
                                     SELECT USER,COUNT(*) AS COUNT
                                     FROM {self.table_name}
                                     GROUP BY USER
                                     ORDER BY COUNT DESC
                                     """).fetchall()
        return select
    def get_next_id(self):
        select = self.cursor.execute(f"SELECT SEQ FROM SQLITE_SEQUENCE WHERE NAME = 'NAMES'").fetchone()
        if select == None:
            return 1
        return select[0] + 1

    def fill_db(self):
        users = ["noah","pablo","mario","fran","adrian"]
        for i in users:
            for j in range(random.randint(1,15)):
                self.insert(i,str(i)+Utils.generate_random_string(random.randint(1,5)),"","")
        self.connector.commit()
        
    def close(self):
        self.connector.close()


class GoogleDriveSaver:
    def __init__(self,keyname_file:str) -> None:
        gauth = GoogleAuth()
        gauth.auth_method = 'service'
        gauth.credentials = ServiceAccountCredentials.from_json_keyfile_name(
            keyname_file, 
            scopes='https://www.googleapis.com/auth/drive'
        )

        # Initialize the drive instance
        self.drive = GoogleDrive(gauth)


    async def save_db(self,image_path:str,folder_id:str):
        file_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and title = '{image_path}'"}).GetList()

        if file_list:
            file_id = file_list[0]["id"]
            file = self.drive.CreateFile({'id':file_id})
            file.SetContentFile(image_path)
            file.Upload()
        else:
            await self.save_anything(image_path,image_path,folder_id)

        print("DB saved\n")


    async def save_image(self,name:str,image_path:str,folder_id:str):
        await self.save_anything(name,image_path,folder_id)
        print("Image saved\n")

    
    #Saves anything
    async def save_anything(self,name:str,image_path:str,folder_id:str):
        file = self.drive.CreateFile({'title': name, 'parents': [{'id': folder_id}]})
        file.SetContentFile(image_path)
        file.Upload()
        
    
    @staticmethod
    async def save_avatar_local(url,path):
        avatar_url = url  # Get the avatar URL
        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as response:
                if response.status == 200:
                    with open(path, 'wb') as f:
                        f.write(await response.read())  # Save the image to a file
                    return True
        return False


class Utils:
    @staticmethod
    def get_img_name(id:str|int,user:str,name:str) -> str:
        return str(id) + ";k;" + user + ";k;" + name + ".png"
    
    @staticmethod
    def get_data_from_img_name(name:str) -> list[str]:
        if name.endswith(".png"):
            name = name[:-4]
        return name.split(";k;")
    
    @staticmethod
    def generate_random_string(length):
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        return random_str
    
class NoLastNames(Exception):
    pass