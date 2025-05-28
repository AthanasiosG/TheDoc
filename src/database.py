import sqlite3 

support_db = {}
bot_msg_db = {}
hg_msg_db = {}

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS role_setup(
    guild_id INTEGER NOT NULL,
    role_name TEXT NOT NULL,
    emoji TEXT NOT NULL,
    PRIMARY KEY (guild_id, role_name)
    )
""")

cursor.execute("""CREATE TABLE IF NOT EXISTS violation(
    guild_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL
    )
""")

cursor.execute("""CREATE TABLE IF NOT EXISTS sup_setup(
    guild_id INTEGER NOT NULL,
    sup_ch_name TEXT NOT NULL,
    sup_team_ch_name TEXT NOT NULL,
    sup_role TEXT NOT NULL
    )
""")

cursor.execute("""CREATE TABLE IF NOT EXISTS blacklist(
    guild_id INTEGER NOT NULL,
    word TEXT NOT NULL
    )
""")

cursor.execute("""CREATE TABLE IF NOT EXISTS server_kicked(
    user_id INTEGER NOT NULL
    )
""")

cursor.execute("""CREATE TABLE IF NOT EXISTS tictactoe_board(
    user_id INTEGER NOT NULL,
    opponent_id INTEGER,
    board TEXT NOT NULL,
    count INTEGER NOT NULL,
    PRIMARY KEY (user_id)
    )
""")

cursor.execute("""CREATE TABLE IF NOT EXISTS hangman(
    user_id INTEGER NOT NULL,
    opponent_id INTEGER,
    word TEXT NOT NULL,
    hg_word TEXT,
    failed_attempts INTEGER NOT NULL,
    disabled_buttons TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (user_id)
    )
""")

conn.commit()
conn.close()