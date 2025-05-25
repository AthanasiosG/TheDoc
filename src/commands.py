import discord, random, sqlite3, asyncio
from discord import app_commands
from discord.ext import commands
from buttons import VerifyButtons, SupportButtons, CloseTicketButtons, ChoseRole, ChooseTicTacToeEnemy
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
        roles = await interaction.guild.fetch_roles()
        verified_role = discord.utils.get(roles, name="Verified") or discord.utils.get(roles, name="Verifiziert")       
        is_verified = False
        
        for role in interaction.user.roles:
            if role == verified_role:
                is_verified = True
                
        if is_verified:
            await interaction.response.send_message(embed=discord.Embed(title="Du bist bereits verifiziert!", description="Diese Nachricht wird in kürze automatisch gelöscht...", colour=6702), ephemeral=True, delete_after=8.0)
        else:
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
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO server_kicked VALUES (?)", (user.id,))
            conn.commit()
            
        await interaction.guild.kick(user=user, reason=reason)
        await user.send(embed=discord.Embed(title="Du wurdest aus folgendem Grund gekickt:", description=reason, color=discord.Color.red()))
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

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO server_kicked VALUES (?)", (user.id,))
            conn.commit()


    @app_commands.command(name="rollen", description="Alle verfügbaren rollen")
    async def server_rollen(self, interaction: discord.Interaction):
        all_roles = [role.name for role in await interaction.guild.fetch_roles()]
        roles = ""
        
        for idx, role in enumerate(all_roles):
            roles += f"{idx+1}: " + role + "\n"
            
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


    @app_commands.command(name="support_setup", description="Das Setup um das Supportsystem benutzen zu können")
    @app_commands.checks.has_permissions(administrator=True)
    async def sup_setup(self, interaction: discord.Interaction, sup_ch_name: str, sup_team_ch_name: str, sup_role: str):        
        all_channels = await interaction.guild.fetch_channels()        
        all_roles = await interaction.guild.fetch_roles()
        await interaction.response.defer(ephemeral=True)

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sup_setup WHERE guild_id=?", (interaction.guild.id,))
            data = cursor.fetchone()
            if data:
                channel_one = discord.utils.get(all_channels, name=data[1])
                channel_two = discord.utils.get(all_channels, name=data[2])
                if channel_one:
                    await channel_one.delete()
                if channel_two:
                    await channel_two.delete()
                cursor.execute("DELETE FROM sup_setup WHERE guild_id=?", (interaction.guild.id,))
                conn.commit()
            await interaction.guild.create_text_channel(name=sup_ch_name)
            support_team_channel = await interaction.guild.create_text_channel(name=sup_team_ch_name)
            cursor.execute("INSERT INTO sup_setup VALUES (?,?,?,?)", (interaction.guild.id, sup_ch_name, sup_team_ch_name, sup_role))
            conn.commit()

        support_role = discord.utils.get(interaction.guild.roles, name=sup_role)

        for role in all_roles:
            if role.name == support_role.name:
                await support_team_channel.set_permissions(target=role, read_messages=True, send_messages=True)      
            else:
                await support_team_channel.set_permissions(target=role, read_messages=False, send_messages=False)

        await interaction.followup.send("Setup gespeichert!", ephemeral=True)
            
            
    @app_commands.command(name="support", description="Hilfe vom Support")
    async def support(self, interaction: discord.Interaction, reason: str = None):
        guild = interaction.guild
        view = SupportButtons(reason)
        all_channels = await guild.fetch_channels()

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT guild_id FROM sup_setup WHERE guild_id=?", (interaction.guild.id,))
            if not cursor.fetchall():
                await interaction.response.send_message(embed=discord.Embed(title="Fehler:", description="Es wurde noch kein Setup gemacht. Führe dazu /support_setup aus.", colour=6702), ephemeral=True, delete_after=10.0)
            else:   
                cursor.execute("SELECT * FROM sup_setup")
                for data in cursor.fetchall():
                    if data[0] == interaction.guild.id:
                        sup_ch_name = data[1]
                sup_channel = discord.utils.get(all_channels, name=sup_ch_name)
                if interaction.channel == sup_channel:
                    await interaction.response.send_message(embed=discord.Embed(title="Support", description="Willst du sicher ein Ticket eröffnen?", colour=6702), view=view, ephemeral=True, delete_after=15.0)
                else:
                    await interaction.response.send_message(embed=discord.Embed(title=f"Geh in den {sup_channel.mention} channel um Hilfe zu bekommen.", description="Diese Nachricht wird in kürze automatisch gelöscht...", colour=6702), ephemeral=True, delete_after=8.0)
                sent_msg = await interaction.original_response()
                support_db[interaction.user.id] = (sent_msg.channel.id, sent_msg.id)
        
        
    @app_commands.command(name="closeticket", description="Nur für Support-Mitglieder")
    async def close_ticket(self, interaction: discord.Interaction):
        guild = interaction.guild
        all_roles = guild.roles
        sup_role = discord.utils.get(all_roles, name="Support")
        user = interaction.user
        view = CloseTicketButtons()
        user_sup_role = user.get_role(sup_role.id)

        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sup_setup")
            for data in cursor.fetchall():
                if data[0] == interaction.guild.id:
                    sup_role = discord.utils.get(all_roles, name=data[3])
                    
        if user_sup_role:
            await interaction.response.send_message(embed=discord.Embed(title="Ticket sicher schließen?", description="Dieser Channel wird gelöscht. Fortfahren?", colour=6702), view=view, ephemeral=True, delete_after=10.0)
        else:
            await interaction.response.send_message("❌ Du hast keine Berechtigung für diesen Command.\n\nDiese Nachricht wird in kürze automatisch gelöscht...", ephemeral=True, delete_after=8.0)
                
                
    @app_commands.command(name="rollensetup", description="Setup für Rollen -> Rollen die sich jeder holen kann")
    @app_commands.checks.has_permissions(administrator=True)
    async def role_setup(self, interaction: discord.Interaction):
        await interaction.user.send(embed=discord.Embed(title="Setup für Rollen", description="Zuordnung von Rolle mit Emoji. Essentiell für /rollenauswahl.\n\nWICHTIG: Folgende Nachricht in genau dem Format senden:\n\n!rollensetup [rollenname]:[emoji] [rollenname]:[emoji]...\n'rollenname' = Tatsächlicher Name \n 'emoji' = gewünschtes Emoji für die Rolle\n\nBeispiel: !rollensetup VIP:💎 Member:🙄", colour=6702))
        await interaction.response.send_message(embed=discord.Embed(title="Schau in deinen DMs.",description="Ich habe dir eine Anleitung geschickt.", colour=6702), ephemeral=True, delete_after=8.0)
        
        
    @app_commands.command(name="rollenauswahl", description="Wähle die Rollen, die du haben möchtest")
    async def chose_role(self, interaction: discord.Interaction):
        view = ChoseRole(interaction)
        role_emoji = ""
        
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM role_setup WHERE guild_id=?", (interaction.guild.id,))     
            for data in cursor.fetchall():
                role_emoji += f"{data[1]}: {data[2]}\n"        
            server_found = False
            cursor.execute("SELECT * FROM role_setup")  
            for data in cursor.fetchall():
                if interaction.guild.id == data[0]:
                    server_found = True
            if server_found:
                await interaction.response.send_message(embed=discord.Embed(title=f"Wähle deine Rollen:", description=role_emoji, colour=6702), view=view, ephemeral=True)
                role_emoji = ""
            else:
                await interaction.response.send_message(embed=discord.Embed(title=f"Noch kein Rollen-Setup gemacht -> /rollensetup", colour=6702), ephemeral=True, delete_after=10.0)
                
                
    @app_commands.command(name="to_do", description="Setzt Erinnerung in x Min")
    async def to_do(self, interaction: discord.Interaction, todo: str, timer: int):
        timer *= 60
        await interaction.response.defer(ephemeral=True)
        
        while timer > 0:
            await asyncio.sleep(1)
            timer -= 1
            
        await interaction.user.send(embed=discord.Embed(title="Erinnerung!", description=todo, colour=6702))
        
        
    @app_commands.command(name="blacklist", description="Zeigt die gesamt Blacklist an")
    async def blacklist(self, interaction: discord.Interaction):
        all_words = ""
        
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blacklist")
            for data in cursor.fetchall():
                if data[0] == interaction.guild.id:
                    all_words += f"{data[1]}\n"
            await interaction.response.send_message(embed=discord.Embed(title="Alle blockierten Wörter:", description=all_words, colour=6702), delete_after=15.0)
        
        
    @app_commands.command(name="blacklist_add", description="Fügt ein Wort zur Blacklist hinzu")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklist_add(self, interaction: discord.Interaction, word: str):
        await interaction.response.defer(ephemeral=True)
        
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blacklist")
            word_found = False
            for data in cursor.fetchall():
                if data[1] == word:
                    await interaction.followup.send("Dieses Wort ist schon auf der Blacklist.")
                    word_found = True
                    break
            if not word_found:
                cursor.execute("INSERT INTO blacklist VALUES (?,?)", (interaction.guild.id, word))
                conn.commit()
                await interaction.followup.send(f"{word} wurde zur Blacklist hinzugefügt!", ephemeral=True)
                    
                    
    @app_commands.command(name="blacklist_remove", description="Entfernt ein Wort aus der Blacklist")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklist_remove(self, interaction: discord.Interaction, word: str):
        await interaction.response.defer(ephemeral=True)
        
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM blacklist")
            for data in cursor.fetchall():
                if data[0] == interaction.guild.id:
                    cursor.execute("DELETE FROM blacklist WHERE word=? AND guild_id=?", (word, interaction.guild.id))
                    conn.commit()
            await interaction.followup.send(f"{word} wurde aus der Blacklist entfernt!", ephemeral=True)
            
            
    @app_commands.command(name="tictactoe", description="Das Spiel TicTacToe")
    async def tictactoe(self, interaction: discord.Interaction):
        view = ChooseTicTacToeEnemy()
        await interaction.response.send_message(embed=discord.Embed(title="Gegen Spieler oder gegen Computer?", colour=6702), view=view, delete_after=8.0)
        sent_msg = await interaction.original_response()
        bot_msg_db[interaction.user.id] = (sent_msg.channel.id, sent_msg.id)