import discord
import random
from discord import app_commands
from discord.ext import commands
from buttons import VerifyButtons, SupportButtons, CloseTicketButtons
from database import support_db, bot_msg_db


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
        sent_msg = await interaction.original_response()
        bot_msg_db[interaction.user.id] = (sent_msg.channel.id, sent_msg.id)

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
        await interaction.followup.send(f"Vorgang abgeschlossen. User gekickt.", ephemeral=True)


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


    @app_commands.command(name="support", description="Hilfe vom Support")
    async def support(self, interaction: discord.Interaction):
        guild = interaction.guild
        channel_create = False
        view = SupportButtons()
        all_channels = await guild.fetch_channels()
        for channel in all_channels:
            if channel.name != "support":
                channel_create = True
            else:
                channel_create = False
                break
        if channel_create:
            sup_channel = await guild.create_text_channel(name="support")
        else:
            sup_channel = discord.utils.get(all_channels, name="support")
        if interaction.channel == sup_channel:
            await interaction.response.send_message(embed=discord.Embed(title="Support:", description="Willst du sicher ein Ticket eröffnen?",
                                                                        colour=6702), view=view)
        else:
            await interaction.response.send_message(embed=discord.Embed(title=f"Geh in den {sup_channel.mention} channel um Hilfe zu bekommen.",
                                                                        description="Diese Nachricht wird in kürze automatisch gelöscht...", colour=6702),
                                                    ephemeral=True, delete_after=8.0)
        sent_msg = await interaction.original_response()
        support_db[interaction.user.id] = (sent_msg.channel.id, sent_msg.id)
        
    
    @app_commands.command(name="closeticket", description="Nur für Support-Mitglieder")
    async def close_ticket(self, interaction: discord.Interaction):
        guild = interaction.guild
        all_roles = guild.roles
        sup_role = discord.utils.get(all_roles, name="Support")
        user = interaction.user
        user_sup_role = user.get_role(sup_role.id)
        view = CloseTicketButtons()
        if user_sup_role:
            await interaction.response.send_message(embed=discord.Embed(title="Ticket sicher schließen?", description="Dieser Channel wird gelöscht. Fortfahren?", colour=6702),
                                                    view=view, delete_after=8.0)
            sent_msg = await interaction.original_response()
            bot_msg_db[interaction.user.id] = (sent_msg.channel.id, sent_msg.id)
        else:
            await interaction.response.send_message("❌ Du hast keine Berechtigung für diesen Command.\n\nDiese Nachricht wird in kürze automatisch gelöscht...", ephemeral=True, delete_after=8.0)
                