import sqlite3,pytz,aiohttp,random,string,hashlib
from datetime import datetime
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from oauth2client.service_account import ServiceAccountCredentials

#Wrapper for the db
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
    
    #Return a list with all user (id,name)
    def get_all_user_id_and_name(self,user:str) -> list:
        select = self.cursor.execute(f"SELECT ID,NAME FROM {self.table_name} WHERE USER = ? ORDER BY CREATED_AT ASC",(user,)).fetchall()
        try:
            return select
        except Exception:
            return []
    
    #Return the image name for an id
    def get_img_name(self,id):
        select = self.cursor.execute(f"SELECT IMAGE FROM {self.table_name} WHERE ID = ?",(id,)).fetchone()
        return select[0]
    
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



#Class for manage the interaction with google drive
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

    #Save the db if there is any change compare to the google drive version.
    async def save_db(self,db_path:str,folder_id:str):
        file_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and title = '{db_path}'"}).GetList()

        if file_list:
            if not await self.is_in_drive(db_path,folder_id):
                file_id = file_list[0]["id"]
                file = self.drive.CreateFile({'id':file_id})
                file.SetContentFile(db_path)
                file.Upload()
            return   #Exit if the file is exactly the same as in google drive
        else:
            await self.save_anything(db_path,db_path,folder_id)

        print("DB saved\n")


    async def save_image(self,name:str,image_path:str,folder_id:str):
        await self.save_anything(name,image_path,folder_id)
        print("Image saved")

    async def download_image(self,img_name:str,folder_id:str):
        await self.download_anything(img_name,folder_id)
        print("Image downloaded")
    
    #Saves anything
    async def save_anything(self,name:str,image_path:str,folder_id:str):
        file = self.drive.CreateFile({'title': name, 'parents': [{'id': folder_id}]})
        file.SetContentFile(image_path)
        file.Upload()
    
    #Download a file from google drive
    async def download_anything(self,file_name:str,folder_id:str):
        file_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and title='{file_name}' and trashed=false"}).GetList()

        if not file_list:
            raise FileNotFoundError

        # Assuming no duplicate names, take the first match
        file_to_download = file_list[0]
        file_to_download.GetContentFile(file_name)
    
    #Downloads the avatar from discord and saves it in the repo root folder
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


    #Check if the file exist in google drive. Not only the name. The same file.
    async def is_in_drive(self,file_path:str,folder_id:str):
        file_list = self.drive.ListFile({'q': f"'{folder_id}' in parents and title='{file_path}' and trashed=false"}).GetList()
        
        if file_list:
            local_file_md5 = Utils.calculate_hash(file_path)
            for i in file_list:
                if 'md5Checksum' in i and i['md5Checksum'] == local_file_md5:
                    return True
        
        return False


#Utility functions class
class Utils:
    splitter = ";k;" #String to split info in images names

    #Get the name for an image
    @staticmethod
    def get_img_name(id:str|int,user:str,name:str) -> str:
        return str(id) + Utils.splitter + user + Utils.splitter + name + ".png"
    
    #Get the information from the name of an image
    @staticmethod
    def get_data_from_img_name(name:str) -> list[str]:
        if name.endswith(".png"):
            name = name[:-4]
        return name.split(Utils.splitter)
    
    @staticmethod
    def generate_random_string(length):
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
        return random_str
    
    @staticmethod
    def calculate_hash(file_path):
        hasher = hashlib.md5()
        with open(file_path, 'rb') as f:
            buf = f.read()
            hasher.update(buf)
        return hasher.hexdigest()
    

#Error class
class NoLastNames(Exception):
    pass