import discord, os, sqlite3
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from commands import BasicCommands


intents = discord.Intents.all()
client = commands.Bot(command_prefix="=", intents=intents)

load_dotenv() 
TOKEN = os.getenv("DISCORD_TOKEN")
blocked_words = os.getenv("BLOCKED_WORDS")

@client.event
async def on_ready():
    await client.add_cog(BasicCommands(client))    
    await client.tree.sync()


@client.event
async def on_guild_join(guild: discord.Guild):
    all_channels = await guild.fetch_channels()
    
    for channel in all_channels:
        if channel.name in ["Willkommen", "Welcome"]:
            await channel.send(embed=discord.Embed(title="Hallo! Ich bin TheDoc 😊", description="Mit /all_commands findet ihr alle verfügbaren Commands!", colour=6702))
            break
        elif channel.name in ["general", "chat", "allgemein"]:
            await channel.send(embed=discord.Embed(title="Hallo! Ich bin TheDoc 😊", description="Mit /all_commands findet ihr alle verfügbaren Commands!", colour=6702))
            break
        
        
@client.event
async def on_member_join(member):
    if not member.bot:
        await member.send(embed=discord.Embed(title="Willkommen auf dem Server", colour=6702))       
    
    
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
        with sqlite3.connect("rolesystem.db") as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE from role_setup WHERE guild_id=?",(msg.guild.id,))
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
           
    if msg.content and msg.content in blocked_words and not msg.author.bot:
        await msg.delete()
        with sqlite3.connect("auto_warn_system.db") as conn:
            cursor = conn.cursor()
            guild_id = msg.guild.id
            user_id = msg.author.id
            cursor.execute("INSERT INTO violation VALUES (?,?)", (guild_id, user_id))
            conn.commit()
            cursor.execute("SELECT * FROM violation WHERE guild_id=? AND user_id=?", (guild_id, user_id))
            all_violations = cursor.fetchall()
            if len(all_violations) > 0 and len(all_violations) <= 2:
                user = await msg.guild.fetch_member(user_id)
                await user.send(embed=discord.Embed(title="VERWARNUNG!", description="Bei weiteren Verstoßen wirst du vom Server gekickt!", colour=6702))
            elif len(all_violations) == 3:
                user = await msg.guild.fetch_member(user_id)
                await msg.guild.kick(user=user)
                await user.send(embed=discord.Embed(title="GEKICKT!", description="Du wurdest aufgrund von zu vielen Verstoßen gekickt!", colour=6702)) 
                cursor.execute("SELECT * FROM violation WHERE guild_id=? AND user_id=?", (guild_id, user_id))

                               
client.run(TOKEN)