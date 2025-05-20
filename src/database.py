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


conn = sqlite3.connect("to_do_list.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS to_do_list(
    user_id INTEGER NOT NULL,
    todo TEXT NULL,
    timer INTEGER NOT NULL
    )
""")

conn.commit()
conn.close()