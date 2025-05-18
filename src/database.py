import sqlite3 

support_db = {}
bot_msg_db = {}


conn = sqlite3.connect("rolesystem.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS role_setup(
    guild_id INTEGER NOT NULL,
    role_name TEXT NOT NULL,
    emoji TEXT NOT NULL,
    PRIMARY KEY (guild_id, role_name)
    )
""")

conn.commit()
conn.close()