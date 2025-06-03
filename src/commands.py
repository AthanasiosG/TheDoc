import discord, random, sqlite3, asyncio, json, random
from discord import app_commands
from discord.ext import commands
from buttons import *
from database import *
from mini_games import *


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
   
   
    @app_commands.command(name="lizenz", description="Nutzungsbedingungen & Datenschutzerklärung")
    async def license(self, interaction: discord.Interaction):
        text = (
            "📄 **Nutzungsbedingungen für TheDoc**\n"
            "1. Durch die Nutzung von TheDoc stimmst du den Nutzungsbedingungen sowie der Datenschutzerklärung zu.\n"
            "2. Die Nutzung von TheDoc erfolgt freiwillig und auf eigenes Risiko.\n"
            "3. Es wird keine Garantie auf Verfügbarkeit, Fehlerfreiheit oder Funktionalität gegeben.\n"
            "4. Der Bot darf nicht für illegale, missbräuchliche oder schädliche Zwecke verwendet werden.\n"
            "5. Die Nutzung kann jederzeit durch Entfernen des Bots beendet werden.\n"
            "6. Mit der Nutzung akzeptierst du diese Bedingungen. Änderungen können jederzeit erfolgen.\n\n\n"
            "🔒 **Datenschutz bei TheDoc**\n"
            "1. TheDoc speichert zur Funktion bestimmter Features (z.B. Quiz, Rollenvergabe) technische Daten wie Server-ID, User-ID oder Emoji-Zuordnungen.\n"
            "2. Es werden keine sensiblen personenbezogenen Daten gespeichert (z.B. Name, IP, E-Mail).\n"
            "3. Die Daten dienen ausschließlich zur Funktion des Bots und werden nicht an Dritte weitergegeben.\n"
            "4. Der Bot wird auf einem Server in der EU betrieben."
        )

        embed = discord.Embed(description=text, color=discord.Color.green())
        embed.set_thumbnail(url="https://raw.githubusercontent.com/AthanasiosG/TheDoc/main/images/thedoc.png")
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="bot_info", description="Info zum Bot")
    async def info_about_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title="Ich heiße TheDoc und wurde von Thanos programmiert.", colour=6702))


    @app_commands.command(name="server_owner", description="Gibt an wem der Server gehört")
    async def server_owner(self, interaction: discord.Interaction):
        owner = interaction.guild.owner
        await interaction.response.send_message(embed=discord.Embed(title="Der Server gehört " + str(owner) +"!", colour=6702))

    
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
            set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "bot")


    @app_commands.command(name="clear", description="Löscht Nachrichten im Channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"{len(deleted)} Nachrichten gelöscht.", ephemeral=True)


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


    @app_commands.command(name="rollensetup", description="Setup für Rollen -> Rollen die sich jeder holen kann")
    @app_commands.checks.has_permissions(administrator=True)
    async def role_setup(self, interaction: discord.Interaction):
        await interaction.user.send(embed=discord.Embed(title="Setup für Rollen", description="Zuordnung von Rolle mit Emoji. Essentiell für /rollenauswahl.\n\nWICHTIG: Folgende Nachricht in genau dem Format senden:\n\n!rollensetup [rollenname]:[emoji] [rollenname]:[emoji]...\n'rollenname' = Tatsächlicher Name \n 'emoji' = gewünschtes Emoji für die Rolle\n\nBeispiel: !rollensetup VIP:💎 Member:🙄", colour=6702))
        await interaction.response.send_message(embed=discord.Embed(title="Schau in deinen DMs.",description="Ich habe dir eine Anleitung geschickt.", colour=6702), ephemeral=True, delete_after=8.0)
        
        
    @app_commands.command(name="rollenauswahl", description="Wähle die Rollen, die du haben möchtest")
    async def chose_role(self, interaction: discord.Interaction):
        view = ChooseRole(interaction)
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
                    await interaction.original_response()
        
        
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
             
                
    @app_commands.command(name="auto_vc_control_help", description="Hilfe zum Auto-Voice-Channel-Control")
    @app_commands.checks.has_permissions(administrator=True)
    async def auto_vc_control_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title="Hilfe zum Auto-Voice-Channel-Control", description="Der Bot erstellt automatisch einen neuen Voice-Channel, wenn ein Benutzer einen Voice-Channel betritt. Es wird sozusagen immer geschaut, dass ein Voice-Channel zu jeder Zeit verfügbar ist. Er wird auch gelöscht, wenn der letzte Benutzer den Channel verlässt. Die Channel werden beginnend mit Talk0 benannt.", colour=6702))


    @app_commands.command(name="auto_vc_control", description="Aktiviere oder deaktiviere Auto-Voice-Channel-Control")
    @app_commands.checks.has_permissions(administrator=True)
    async def auto_vc_control(self, interaction: discord.Interaction):
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT active FROM auto_vc_control WHERE guild_id=?", (interaction.guild.id,))
            result = cursor.fetchone()
            if result is None:
                cursor.execute("INSERT INTO auto_vc_control (guild_id, active) VALUES (?, ?)", (interaction.guild.id, 1))
                conn.commit()
                await interaction.response.send_message(embed=discord.Embed(title="Auto-Voice-Channel-Control aktiviert", colour=6702), ephemeral=True, delete_after=8.0)
                return
            else:
                if result[0] == 1:
                    cursor.execute("UPDATE auto_vc_control SET active=? WHERE guild_id=?", (0, interaction.guild.id))
                    conn.commit()
                    await interaction.response.send_message(embed=discord.Embed(title="Auto-Voice-Channel-Control deaktiviert!", colour=6702), ephemeral=True, delete_after=8.0)
                else:
                    cursor.execute("UPDATE auto_vc_control SET active=? WHERE guild_id=?", (1, interaction.guild.id))
                    conn.commit()
                    await interaction.response.send_message(embed=discord.Embed(title="Auto-Voice-Channel-Control aktiviert!", colour=6702), ephemeral=True, delete_after=8.0)
        
        
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

            
    @app_commands.command(name="coinflip", description="Kopf oder Zahl")
    async def coinflip(self, interaction: discord.Interaction):
        coin = random.choice(["Kopf", "Zahl"])
        coin = f"Du hast {coin} geworfen."
        await interaction.response.send_message(embed=discord.Embed(title=coin, colour=6702))


    @app_commands.command(name="to_do", description="Setzt Erinnerung in x Min")
    async def to_do(self, interaction: discord.Interaction, todo: str, timer: int):
        timer *= 60
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="Erinnerung gesetzt!", description=f"Du wirst in {timer//60} Minute(n) an folgendes erinnert:\n{todo}", colour=6702))

        while timer > 0:
            await asyncio.sleep(1)
            timer -= 1
            
        await interaction.user.send(embed=discord.Embed(title="Erinnerung!", description=todo, colour=6702))
            
            
    @app_commands.command(name="tictactoe", description="Das Spiel TicTacToe")
    async def tictactoe(self, interaction: discord.Interaction):
        view = ChooseTicTacToeEnemy()
        await interaction.response.send_message(embed=discord.Embed(title="Gegen Spieler oder gegen Computer?", colour=6702), view=view, delete_after=8.0)
        sent_msg = await interaction.original_response()
        set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "bot")
        
        
    @app_commands.command(name="hangman_vs_player", description="Das Spiel Hangman")
    async def hangman_player(self, interaction: discord.Interaction, word: str):
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT active FROM hangman WHERE user_id=?", (interaction.user.id,))
            row = cursor.fetchone()
            if row and row[0] == 1:
                deactivate_hangman(interaction.user.id)
            cursor.execute("DELETE FROM hangman WHERE user_id=?", (interaction.user.id,))
            conn.commit()
            cursor.execute("INSERT INTO hangman (user_id, opponent_id, word, hg_word, failed_attempts, disabled_buttons, active) VALUES (?, ?, ?, ?, ?, ?, ?)", (interaction.user.id, None, word, "", 0, "", 1))
            conn.commit()

        view = HangmanPlayerReady(interaction.user.id, word)
        await interaction.response.send_message(embed=discord.Embed(title=f"Warte auf einen Gegner! Der erste, der auf 'Ready' klickt, spielt gegen {interaction.user}.", colour=6702), view=view)
        sent_msg = await interaction.original_response()
        set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "bot")
        set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "hangman")
        
        
    @app_commands.command(name="hangman_vs_computer", description="Das Spiel Hangman")
    async def hangman_computer(self, interaction: discord.Interaction):
        with open("json/hg_words.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
            hg_words = data["words"]
            num = random.randint(0,100)
            word = hg_words[num]
                
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT active FROM hangman WHERE user_id=?", (interaction.user.id,))
            row = cursor.fetchone()
            if row and row[0] == 1:
                deactivate_hangman(interaction.user.id)
            cursor.execute("DELETE FROM hangman WHERE user_id=?", (interaction.user.id,))
            conn.commit()
            cursor.execute("INSERT INTO hangman (user_id, opponent_id, word, hg_word, failed_attempts, disabled_buttons, active) VALUES (?, ?, ?, ?, ?, ?, ?)", (interaction.user.id, None, word, "", 0, "", 1))
            conn.commit()

        view = HangmanComputerReady(interaction.user.id, word)
        await interaction.response.send_message(embed=discord.Embed(title="Spiel starten?", description="Drücke **Ready** um loszulegen!", colour=6702), view=view)
        sent_msg = await interaction.original_response()
        set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "bot")
        set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "hangman")
        
        
    @app_commands.command(name="quiz", description="Ein Quiz-Spiel")
    async def quiz(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        with open("json/quiz.json", "r", encoding="UTF-8") as file:
            data = json.load(file)
            num = random.randint(1,1000)
            data = data[num]
            question = data["frage"]
            answer_choices = data["antwortmöglichkeiten"]
            answer = data["lösung"]
            difficulty = data["schwierigkeit"]
            view = Quiz(user_id, question, answer_choices, answer, difficulty)
            await interaction.response.send_message(embed=discord.Embed(title="Frage: "+ question, description="Antwortmöglichkeiten:", colour=6702), view=view)
            
    
    @app_commands.command(name="quiz_points", description="Zeigt die Quiz-Punkte an")
    async def quiz_points(self, interaction: discord.Interaction):       
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM quiz_points WHERE guild_id=? AND user_id=?", (interaction.guild.id, interaction.user.id))
            points = cursor.fetchone()
            if points:
                points = points[0]
            else:
                points = None
        
        if points is not None:
            await interaction.response.send_message(embed=discord.Embed(title=f"Du hast {points} Quiz-Punkte!", colour=6702))
        else:
            await interaction.response.send_message(embed=discord.Embed(title="Du hast noch keine Quiz-Punkte.", colour=6702), ephemeral=True)
            
    
    @app_commands.command(name="quiz_leaderboard", description="Zeigt die Quiz-Punkte der User an")
    async def quiz_leaderboard(self, interaction: discord.Interaction):
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, points FROM quiz_points WHERE guild_id=? ORDER BY points DESC LIMIT 10", (interaction.guild.id,))
            leaderboard = cursor.fetchall()
        
        if not leaderboard:
            await interaction.response.send_message(embed=discord.Embed(title="Es gibt noch keine Quiz-Punkte.", colour=6702), ephemeral=True)
            return
        
        leaderboard_text = ""
        
        for idx, (user_id, points) in enumerate(leaderboard, start=1):
            user = await interaction.guild.fetch_member(user_id)
            if user.name in leaderboard_text:
                continue
            leaderboard_text += f"{idx}. {user.name}: {points} Punkte\n"
        
        await interaction.response.send_message(embed=discord.Embed(title="Quiz-Leaderboard:", description=leaderboard_text, colour=6702))
        
    
    @app_commands.command(name="gamble_quiz_points", description="Gamble deine Quiz-Punkte")
    async def gamble_quiz_points(self, interaction: discord.Interaction, points: int):
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT points FROM quiz_points WHERE guild_id=? AND user_id=?", (interaction.guild.id, interaction.user.id))
            current_points = cursor.fetchone()
            if not current_points or current_points[0] < points:
                await interaction.response.send_message(embed=discord.Embed(title="Du hast nicht genug Quiz-Punkte zum Gamen.", colour=6702), ephemeral=True)
                return
            gamble_result = random.choice(["win", "lose"])
            if gamble_result == "win":
                new_points = current_points[0] + points
                cursor.execute("UPDATE quiz_points SET points=? WHERE guild_id=? AND user_id=?", (new_points, interaction.guild.id, interaction.user.id))
                conn.commit()
                await interaction.response.send_message(embed=discord.Embed(title=f"Du hast gewonnen! Du hast jetzt {new_points} Quiz-Punkte.", colour=6702))
            else:
                new_points = current_points[0] - points
                cursor.execute("UPDATE quiz_points SET points=? WHERE guild_id=? AND user_id=?", (new_points, interaction.guild.id, interaction.user.id))
                conn.commit()
                await interaction.response.send_message(embed=discord.Embed(title=f"Du hast verloren! Du hast jetzt {new_points} Quiz-Punkte.", colour=6702))

