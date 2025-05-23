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



conn = sqlite3.connect("auto_warn_system.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS violation(
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL
    )
""")

conn.commit()
conn.close()



conn = sqlite3.connect("supportsystem_setup.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS setup(
    guild_id INTEGER NOT NULL,
    sup_ch_name TEXT NOT NULL,
    sup_team_ch_name TEXT NOT NULL,
    sup_role TEXT NOT NULL
    )
""")

conn.commit()
conn.close()



conn = sqlite3.connect("blocked_words.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS blacklist(
    guild_id INTEGER NOT NULL,
    word TEXT NOT NULL
    )
""")

conn.commit()
conn.close()



conn = sqlite3.connect("kicked_user.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS server_kicked(
    user_id INTEGER NOT NULL
    )
""")

conn.commit()
conn.close()