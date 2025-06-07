import aiosqlite

class DatabaseManager:
    
    @staticmethod
    async def init_database():
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()

            await cursor.execute("""CREATE TABLE IF NOT EXISTS role_setup(
                guild_id INTEGER NOT NULL,
                role_name TEXT NOT NULL,
                emoji TEXT NOT NULL,
                PRIMARY KEY (guild_id, role_name)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS violation(
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS violation_limit(
                guild_id INTEGER NOT NULL,
                amount INTEGER NOT NULL DEFAULT 3,
                PRIMARY KEY (guild_id)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS sup_setup(
                guild_id INTEGER NOT NULL,
                sup_ch_name TEXT NOT NULL,
                sup_team_ch_name TEXT NOT NULL,
                sup_role TEXT NOT NULL
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS blacklist(
                guild_id INTEGER NOT NULL,
                word TEXT NOT NULL
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS server_kicked(
                user_id INTEGER NOT NULL
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS tictactoe_board(
                user_id INTEGER NOT NULL,
                opponent_id INTEGER,
                board TEXT NOT NULL,
                count INTEGER NOT NULL,
                PRIMARY KEY (user_id)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS hangman(
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

            await cursor.execute("""CREATE TABLE IF NOT EXISTS bot_messages(
                user_id INTEGER NOT NULL,
                channel_id INTEGER,
                message_id INTEGER,
                type TEXT,
                PRIMARY KEY (user_id, type)
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS quiz_points(
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                points INTEGER NOT NULL DEFAULT 0
                )
            """)

            await cursor.execute("""CREATE TABLE IF NOT EXISTS auto_vc_control(
                guild_id INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 0,
                primary key (guild_id)
                )
            """)

            await conn.commit()

async def set_bot_message(user_id, channel_id, message_id, msg_type="bot"):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("INSERT OR REPLACE INTO bot_messages (user_id, channel_id, message_id, type) VALUES (?, ?, ?, ?)", (user_id, channel_id, message_id, msg_type))
        await conn.commit()

async def get_bot_message(user_id, msg_type="bot"):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT channel_id, message_id FROM bot_messages WHERE user_id=? AND type=?", (user_id, msg_type))
        return await cursor.fetchone()

async def delete_bot_message(user_id, msg_type="bot"):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("DELETE FROM bot_messages WHERE user_id=? AND type=?", (user_id, msg_type))
        await conn.commit()