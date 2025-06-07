import discord, os, aiosqlite
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from commands import BasicCommands
from database import DatabaseManager


intents = discord.Intents.all()
client = commands.Bot(command_prefix="=", intents=intents)

load_dotenv() 
TOKEN = os.getenv("BOT_TOKEN")


@client.event
async def on_ready():
    await DatabaseManager.init_database()
    await client.add_cog(BasicCommands(client))    
    await client.tree.sync()


@client.event
async def on_guild_join(guild: discord.Guild):
    all_channels = await guild.fetch_channels()
    
    for channel in all_channels:
        if channel.name.lower() in ["willkommen", "welcome"]:
            embed = discord.Embed(title="Hello! I am TheDoc 😊", description="By using TheDoc, you agree to the terms of use and privacy policy. More info with /license. Use /all_commands to see all available commands!", colour=6702)
            embed = embed.set_thumbnail(url="https://raw.githubusercontent.com/AthanasiosG/TheDoc/main/images/thedoc.png")
            await channel.send(embed=embed)
            async with aiosqlite.connect("database.db") as conn:
                cursor = await conn.cursor()
                await cursor.execute("INSERT OR IGNORE INTO auto_vc_control (guild_id, active) VALUES (?, ?)", (guild.id, 0))
            return
        elif channel.name.lower() in ["general", "chat", "allgemein"]:
            embed = discord.Embed(title="Hello! I am TheDoc 😊", description="By using TheDoc, you agree to the terms of use and privacy policy. More info with /license. Use /all_commands to see all available commands!", colour=6702)
            embed = embed.set_thumbnail(url="https://raw.githubusercontent.com/AthanasiosG/TheDoc/main/images/thedoc.png")
            await channel.send(embed=embed)
            async with aiosqlite.connect("database.db") as conn:
                cursor = await conn.cursor()
                await cursor.execute("INSERT OR IGNORE INTO auto_vc_control (guild_id, active) VALUES (?, ?)", (guild.id, 0))
            return
        
        
@client.event
async def on_member_join(member):
    if not member.bot:
        guild = member.guild
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM server_kicked WHERE user_id=?", (member.id,))
        try:
            await member.send(embed=discord.Embed(title=f"Welcome to the server **{guild}**!", colour=6702)) 
        except discord.Forbidden:
            print("User has DMs disabled.")
    
    
@client.event
async def on_member_remove(member):
    guild = member.guild
    all_channels = await guild.fetch_channels()
    is_user_kicked = False
    
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT user_id FROM server_kicked")
        for data in await cursor.fetchall():
            if data[0] == member.id:
                is_user_kicked = True
                
    if not is_user_kicked:
        for channel in all_channels:
            if channel.name.lower() in ["willkommen", "welcome"] and isinstance(channel, discord.TextChannel):
                invite = await channel.create_invite(max_age=86400, max_uses=1, unique=True)
                try:
                    await member.send(embed=discord.Embed(title=f"You have left **{guild}**:", description="If this was a mistake, you can rejoin using this link!", colour=6702, url=invite))
                    break
                except discord.Forbidden:
                    print("User has DMs disabled.")
        
    
@client.event
async def on_voice_state_update(member, before, after):
    async with aiosqlite.connect("database.db") as conn:
        cursor = await conn.cursor()
        await cursor.execute("SELECT active FROM auto_vc_control WHERE guild_id=?", (member.guild.id,))
        result = await cursor.fetchone()
        if result is None or result[0] == 0:
            return
          
    if before.channel is None and after.channel is not None:
        channel = after.channel 
        if len(channel.members) == 1:
            cloned_channel = await channel.clone(name="Talk")
            await cloned_channel.edit(name="Talk" + str(len(channel.guild.voice_channels)-1))      
    elif before.channel is not None and after.channel is None and len(before.channel.members) == 0:
        await before.channel.delete()
        channels = before.channel
        for i, channel in enumerate(channels.guild.voice_channels):
            await channel.edit(name="Talk" + str(i))    
                
                    
@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ You do not have permission for this command.\n\nThis message will be automatically deleted soon...", ephemeral=True, delete_after=8.0)
    else:
        await interaction.response.send_message("An unknown error has occurred.\n\nThis message will be automatically deleted soon...", ephemeral=True, delete_after=8.0)


@client.event
async def on_message(msg):
    if msg.author.bot:
        return
    
    if msg.content.startswith("!role_setup") and msg.author.guild_permissions.administrator:
        msg_list = msg.content.split()
        msg_list.pop(0)
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("DELETE FROM role_setup WHERE guild_id=?",(msg.guild.id,))
            for role_emoji_pair in msg_list:
                pair = ""
                for char in role_emoji_pair:
                    if char != ":":
                        pair += char
                    elif char == ":":
                        pair += " "
                role_name, emoji = pair.split()
                await cursor.execute("INSERT OR IGNORE INTO role_setup VALUES (?, ?, ?)", (msg.guild.id, role_name, emoji))
                await conn.commit()
        await msg.channel.send("Data saved.", delete_after=5.0)
        await msg.delete()
           
    if not msg.author.bot and msg.content:
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT word FROM blacklist WHERE guild_id=?", (msg.guild.id,))
            blacklisted_words = [data[0] for data in await cursor.fetchall()]
            await cursor.execute("SELECT amount FROM violation_limit WHERE guild_id=?", (msg.guild.id,))
            result = await cursor.fetchone()
            violation_limit = result[0] if result else 3
            for content in msg.content.split():
                if content in blacklisted_words:
                    await msg.delete()
                    guild_id, user_id = msg.guild.id, msg.author.id
                    await cursor.execute("INSERT INTO violation (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
                    await conn.commit()
                    await cursor.execute("SELECT COUNT(*) FROM violation WHERE guild_id=? AND user_id=?", (guild_id, user_id))
                    violations = await cursor.fetchone()
                    violations = violations[0]
                    user = await msg.guild.fetch_member(user_id)
                    try:
                        if violations < violation_limit:
                            await user.send(embed=discord.Embed(title="WARNING!", description=f"If you violate again, you will be kicked from the server at {violation_limit} violations!",colour=6702))
                        elif violations == violation_limit:
                            await cursor.execute("INSERT INTO server_kicked (user_id) VALUES (?)", (user.id,))
                            await conn.commit()                             
                            await msg.guild.kick(user)
                            await user.send(embed=discord.Embed(title="KICKED!", description="You have been kicked due to too many violations!", color= discord.Color.red()))
                            await cursor.execute("DELETE FROM violation WHERE guild_id=? AND user_id=?", (msg.guild.id, user.id))
                            await conn.commit() 
                    except discord.Forbidden:
                        print("User has DMs disabled.")


client.run(TOKEN)