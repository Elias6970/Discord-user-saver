# Discord bot that saves the past usernames and photos of a server in Google Drive


## What is it?
The bot detect any username or photo change and it saves them in google drive. The photos got a name with their id in the db, user and username to be human-reedable. Also, one time per day the sqlite3 db is uploaded to the google drive folder to save other information like the creation date.

---

## Installation

#### Windows

1. Create a [discord bot](https://discord.com/developers/applications) and add it to your server.
2. Create a python virtual enviroment and activate it. `python -m venv *venv_name*`
3. Activate the virtual enviroment. `.\*venv_name*\Scripts\activate`
4. Install the dependencies. `pip install -r requirements.txt`
5. Create a .env file in the root folder of the project with these variables: 
**- KEYNAME_FILE** = file (json) with credentials for the service account in the google drive api. You can get this file from the Api part of the [Google cloud console](https://console.cloud.google.com/apis/credentials).
**- DISCORD_TOKEN** = discord bot token got from developers discord portal.
**- SERVER_ID** = id of the discord server in which you want to use it.
**- DB_PATH** = local path where you want to save the database with the names, e.g. "names.db" will create the db in root repo folder.
**- FOLDER_ID** = folder id from google drive to save the images of the users. You need to share the folder with service account gmail.
6. Run the discord bot `python main.py`