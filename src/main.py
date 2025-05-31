import discord, os, sqlite3, database
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from commands import BasicCommands


intents = discord.Intents.all()
client = commands.Bot(command_prefix="=", intents=intents)

load_dotenv() 
TOKEN = os.getenv("DISCORD_TOKEN")


@client.event
async def on_ready():
    await client.add_cog(BasicCommands(client))    
    await client.tree.sync()


@client.event
async def on_guild_join(guild: discord.Guild):
    all_channels = await guild.fetch_channels()
    
    for channel in all_channels:
        if channel.name.lower() in ["willkommen", "welcome"]:
            await channel.send(embed=discord.Embed(title="Hallo! Ich bin TheDoc 😊", description="Mit /all_commands findet ihr alle verfügbaren Commands!", colour=6702))
            break
        elif channel.name.lower() in ["general", "chat", "allgemein"]:
            await channel.send(embed=discord.Embed(title="Hallo! Ich bin TheDoc 😊", description="Mit /all_commands findet ihr alle verfügbaren Commands!", colour=6702))
            break
        
        
@client.event
async def on_member_join(member):
    if not member.bot:
        guild = member.guild
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM server_kicked WHERE user_id=?", (member.id,))
        await member.send(embed=discord.Embed(title=f"Willkommen auf dem Server **{guild}**!", colour=6702)) 
              
    
@client.event
async def on_member_remove(member):
    guild = member.guild
    all_channels = await guild.fetch_channels()
    is_user_kicked = False
    
    with sqlite3.connect("database.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM server_kicked")
        for data in cursor.fetchall():
            if data[0] == member.id:
                is_user_kicked = True
                
    if not is_user_kicked:
        for channel in all_channels:
            if channel.name.lower() in ["willkommen", "welcome"] and isinstance(channel, discord.TextChannel):
                invite = await channel.create_invite(max_age=86400, max_uses=1, unique=True)
                await member.send(embed=discord.Embed(title=f"Du hast **{guild}** verlassen:", description="Falls das ausversehen war, dann kannst du über diesen Link erneut joinen!", colour=6702, url=invite))
                break
        
    
@client.event
async def on_voice_state_update(member, before, after):  
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
        await interaction.response.send_message("❌ Du hast keine Berechtigung für diesen Command.\n\nDiese Nachricht wird in kürze automatisch gelöscht...", ephemeral=True, delete_after=8.0)
    else:
        await interaction.response.send_message("Ein unbekannter Fehler ist aufgetreten.\n\nDiese Nachricht wird in kürze automatisch gelöscht...", ephemeral=True, delete_after=8.0)


@client.event
async def on_message(msg):
    if msg.author.bot:
        return
    
    if msg.content.startswith("!rollensetup") and msg.author.guild_permissions.administrator:
        msg_list = msg.content.split()
        msg_list.pop(0)
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM role_setup WHERE guild_id=?",(msg.guild.id,))
            for role_emoji_pair in msg_list:
                pair = ""
                for char in role_emoji_pair:
                    if char != ":":
                        pair += char
                    elif char == ":":
                        pair += " "
                role_name, emoji = pair.split()
                cursor.execute("INSERT OR IGNORE INTO role_setup VALUES (?, ?, ?)", (msg.guild.id, role_name, emoji))
                conn.commit()
        await msg.channel.send("Daten gespeichert.", delete_after=5.0)
        await msg.delete()
           
    if not msg.author.bot and msg.content:
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT word FROM blacklist WHERE guild_id=?", (msg.guild.id,))
            blacklisted_words = [data[0] for data in cursor.fetchall()]
            for content in msg.content.split():
                if content in blacklisted_words:
                    await msg.delete()
                    guild_id, user_id = msg.guild.id, msg.author.id
                    cursor.execute("INSERT INTO violation (guild_id, user_id) VALUES (?, ?)", (guild_id, user_id))
                    conn.commit()
                    cursor.execute("SELECT COUNT(*) FROM violation WHERE guild_id=? AND user_id=?", (guild_id, user_id))
                    violations = cursor.fetchone()[0]
                    user = await msg.guild.fetch_member(user_id)
                    if violations <= 2:
                        await user.send(embed=discord.Embed(title="VERWARNUNG!", description="Bei weiteren Verstößen wirst du vom Server gekickt!",colour=6702))
                    elif violations == 3:
                        cursor.execute("INSERT INTO server_kicked (user_id) VALUES (?)", (user.id,))
                        conn.commit()                             
                        await msg.guild.kick(user)
                        await user.send(embed=discord.Embed(title="GEKICKT!", description="Du wurdest aufgrund von zu vielen Verstößen gekickt!", color= discord.Color.red()))
                        cursor.execute("DELETE FROM violation WHERE guild_id=? AND user_id=?", (msg.guild.id, user.id))
                        conn.commit() 


client.run(TOKEN)