import discord
import random
from discord import app_commands
from discord.ext import commands
from verify_buttons import VerifyButtons

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="all_commands", description="Alle verfügbaren Bot-Commands")
    async def all_commands(self, interaction: discord.Interaction):   
        cmd_list = [cmd.name for cmd in self.bot.tree.get_commands()]
        all_cmd = ""
        for cmd in cmd_list:
            all_cmd += "/" + cmd + "\n"
        await interaction.response.send_message(embed=discord.Embed(title="Das sind alle verfügbaren Commands:", description=all_cmd, colour=6702))

    
    @app_commands.command(name="verify", description="Verifizierung")
    async def verify(self, interaction: discord.Interaction):
        rules = "Haltet euch an die allgemeinen Discord Regeln"
        embed = discord.Embed(title=rules, description="Zum akzeptieren der Regeln den grünen Button anklicken, zum Ablehnen den roten Button anklicken",color=discord.Color.green())
        embed.set_thumbnail(url="https://kwiqreply.io/img/icon/verify.png")
        view = VerifyButtons()
        await interaction.response.send_message(embed=embed, view=view)
        

    @app_commands.command(name="bot_info", description="Info zum Bot")
    async def info_about_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title="Ich heiße TheDoc und wurde von Thanos programmiert.", colour=6702))


    @app_commands.command(name="server_owner", description="Gibt an wem der Server gehört")
    async def server_owner(self, interaction: discord.Interaction):
        owner = interaction.guild.owner
        await interaction.response.send_message(embed=discord.Embed(title="Der Server gehört " + str(owner) +"!", colour=6702))

        
    @app_commands.command(name="kick", description="Einen User kicken")
    @app_commands.checks.has_permissions(administrator=True)
    async def kick(self, interaction: discord.Interaction, user: discord.User, reason: str):
        await interaction.guild.kick(user=user, reason=reason)
        await user.send(embed=discord.Embed(title="Du wurdest aus folgendem Grund gebannt:", description=reason, color=discord.Color.red()))
        msg = f"{user} wurde erfolgreich gekickt!"
        await interaction.user.send(embed=discord.Embed(title=msg, description="Grund: " + reason, color=discord.Color.red()))
        await interaction.response.defer(ephemeral=True)        
        await interaction.followup.send(f"Vorgang abgeschlossen.", ephemeral=True)


    @app_commands.command(name="ban", description="Einen User bannen")
    @app_commands.checks.has_permissions(administrator=True)
    async def ban(self, interaction: discord.Interaction, user: discord.User, reason: str):
        await interaction.guild.ban(user=user, reason=reason)
        await user.send(embed=discord.Embed(title="Du wurdest aus folgendem Grund gebannt:", description=reason, color=discord.Color.red()))
        msg = f"{user} wurde erfolgreich gebannt!"
        await interaction.user.send(embed=discord.Embed(title=msg, description="Grund: " + reason, color=discord.Color.red()))
        await interaction.response.defer(ephemeral=True)        
        await interaction.followup.send(f"Vorgang abgeschlossen. User gebannt.", ephemeral=True)


    @app_commands.command(name="rollen", description="Alle verfügbaren rollen")
    async def server_rollen(self, interaction: discord.Interaction):
        all_roles = [role.name for role in await interaction.guild.fetch_roles()]
        roles = ""
        for i, role in enumerate(all_roles):
            roles += f"{i+1}: " + role + "\n"
        await interaction.response.send_message(embed=discord.Embed(title="Alle Rollen", description=roles, colour=6702))          


    @app_commands.command(name="clear", description="Löscht Nachrichten im Channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"{len(deleted)} Nachrichten gelöscht.", ephemeral=True)


    @app_commands.command(name="coinflip", description="Kopf oder Zahl")
    async def coinflip(self, interaction: discord.Interaction):
        coin = random.choice(["Kopf", "Zahl"])
        coin = f"Du hast {coin} geworfen."
        await interaction.response.send_message(embed=discord.Embed(title=coin, colour=6702))


    @app_commands.command(name="songs", description="Alle verfügbaren Songs")
    async def songs(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title="Folgende Songs sind verfügbar:",
                                                                    description="Fürs Aufrufen !+Songname benutzen:\n\nJust Danke\nPopular\nGive Me Everthing\nPoker Face\n",
                                                                    colour=6702))
