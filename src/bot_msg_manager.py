import discord, aiosqlite


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