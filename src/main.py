import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from commands import BasicCommands
from songs import all_songs


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
        if channel.name in ["general", "chat", "allgemein"]:
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
               
                
@client.event
async def on_message(msg):
    if msg.author.bot:
        return       
        
    if msg.content in [song.lower() for song in all_songs.keys()] or msg.content in [song for song in all_songs.keys()]:    
        song_name = ""
        
        for num, letter in enumerate(msg.content):
            if num == 1:
                song_name+= letter.upper()
            else:
                song_name+= letter
                
        for song, url in all_songs.items():
            if msg.channel.name in ["general", "chat", "allgemein"] and song_name == song and msg.author != msg.author.bot:
                await msg.reply(embed=discord.Embed(title=song[1::], url=url, colour=6702)) 
                    

@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message("❌ Du hast keine Berechtigung für diesen Command.\n\nDiese Nachricht wird in kürze automatisch gelöscht...", ephemeral=True, delete_after=8.0)
    else:
        await interaction.response.send_message("Ein unbekannter Fehler ist aufgetreten.\n\nDiese Nachricht wird in kürze automatisch gelöscht...", ephemeral=True, delete_after=8.0)
 
                    
client.run(TOKEN)