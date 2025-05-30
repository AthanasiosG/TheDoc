import discord, sqlite3, asyncio
from database import *
from mini_games import *


class VerifyButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)


    @discord.ui.button(style=discord.ButtonStyle.green, label="Accept", disabled=False)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        roles = await guild.fetch_roles()
        verified_role = discord.utils.get(roles, name="Verified") or discord.utils.get(roles, name="Verifiziert")
        
        if not verified_role:
            verified_role = await guild.create_role(name="Verified", color=discord.Color.green())
            
        await interaction.user.add_roles(verified_role)
        await interaction.response.send_message(embed=discord.Embed(title="Du bist nun verifiziert!", description="Diese Nachricht wird in kürze automatisch gelöscht...", colour=6702), ephemeral=True, delete_after=8.0)
        user_id = interaction.user.id
        
        if user_id in bot_msg_db:
            channel_id, message_id = bot_msg_db[user_id]
            channel = interaction.client.get_channel(channel_id)
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
                del bot_msg_db[user_id]
            except discord.NotFound:
                print("Nachricht schon gelöscht oder nicht gefunden.")
            except Exception as error:
                print(f"Fehler beim Löschen: {error}")    
        
        
    @discord.ui.button(style=discord.ButtonStyle.red, label="Deny", disabled=False)
    async def Deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=discord.Embed(title="Du musst akzeptieren oder du wirst gekickt.", description="Diese Nachricht wird in kürze automatisch gelöscht...", colour=6702), ephemeral=True, delete_after=8.0)
        


class SupportButtons(discord.ui.View):
    def __init__(self, reason, *, timeout=None):
        super().__init__(timeout=timeout)
        self.reason = reason


    @discord.ui.button(style=discord.ButtonStyle.green, label="Yes", disabled=False)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user_id = interaction.user.id
        all_channels = await guild.fetch_channels()
        
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sup_setup WHERE guild_id = ?", (interaction.guild.id,))
            data = cursor.fetchone()
            if data:
                sup_team_ch_name = data[2]
        
        view = SupportTeamButtons(user_id)
        support_role = discord.utils.get(guild.roles, name="Support")
        support_channel = discord.utils.get(all_channels, name=sup_team_ch_name)
        
        if self.reason is None:
            self.reason = "Keiner angegeben"
        
        msg = await support_channel.send(embed=discord.Embed(title="Ein Ticket wurde eröffnet", description="Grund: " + self.reason, colour=6702), content=support_role.mention, view=view)
        await interaction.response.send_message(embed=discord.Embed(title="Erfolg!", description="Ein Support-Mitarbeiter wird das Ticket in kürze bearbeiten...", colour=6702), ephemeral=True, delete_after=8.0)
        bot_msg_db[user_id] = (support_channel.id, msg.id)
        
        if user_id in support_db:
            try:
                del support_db[user_id]
            except discord.NotFound:
                print("Nachricht schon gelöscht oder nicht gefunden.")
            except Exception as error:
                print(f"Fehler beim Löschen: {error}")  


    @discord.ui.button(style=discord.ButtonStyle.red, label="Cancel", disabled=False)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        
        if user_id in support_db:
            try:
                del support_db[user_id]
            except Exception as e:
                print(f"Fehler beim Löschen: {e}")
                
        await interaction.response.send_message("Ticketanfrage abgebrochen.", ephemeral=True, delete_after=8.0)



class SupportTeamButtons(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id


    @discord.ui.button(style=discord.ButtonStyle.green, label="Open", disabled=False)
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = guild.get_member(self.user_id)
        sup_channel = await guild.create_text_channel(name=f"support-{user.name}")
        await sup_channel.set_permissions(user, read_messages=True, send_messages=True)

        for role in guild.roles:
            if not role.permissions.administrator:
                await sup_channel.set_permissions(role, read_messages=False)

        msg = await interaction.followup.send(embed=discord.Embed(title=f"Ticket geöffnet: {sup_channel.mention}", colour=6702), ephemeral=True)
        await sup_channel.send(embed=discord.Embed(title="Ticket wurde geöffnet", description="Sie sind jetzt mit einem Support-Mitarbeiter verbunden.", colour=6702), content=user.mention)

        try:
            channel_id, msg_id = bot_msg_db[self.user_id]
            channel = interaction.client.get_channel(channel_id)
            message = await channel.fetch_message(msg_id)
            await message.delete()
            del bot_msg_db[self.user_id]
        except Exception as e:
            print(f"Fehler beim Löschen: {e}")

        await asyncio.sleep(15)
        await msg.delete()


    @discord.ui.button(style=discord.ButtonStyle.red, label="Close", disabled=False)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=discord.Embed(title="Ticket geschlossen", colour=6702), ephemeral=True, delete_after=8.0)
        
        try:
            ch_id, msg_id = bot_msg_db[self.user_id]
            channel = interaction.client.get_channel(ch_id)
            msg = await channel.fetch_message(msg_id)
            await msg.delete()
            del bot_msg_db[self.user_id]
        except Exception as e:
            print(f"Fehler beim Löschen: {e}")
            
            

class CloseTicketButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        
        
    @discord.ui.button(style=discord.ButtonStyle.green, label="Ja", disabled=False)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        all_roles = guild.roles
        sup_role = discord.utils.get(all_roles, name="Support")
        user = interaction.user
        user_sup_role = user.get_role(sup_role.id)
        
        if user_sup_role:
            channel = interaction.channel
            if channel.name.startswith("support-"):
                await channel.delete()    
            else:
                await interaction.response.send_message("**Fehler**\nDieser Befehl kann nicht in diesem Channel benutzt werden.", ephemeral=True, delete_after=8.0)



class ChooseRole(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.guild_id = interaction.guild.id
        
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM role_setup WHERE guild_id = ?", (self.guild_id,))
            for data in cursor.fetchall():          
                if self.guild_id == data[0]:
                    role = data[1]
                    emoji = data[2]
                    button = discord.ui.Button(style=discord.ButtonStyle.primary, label=emoji, disabled=False)
                    button.callback = self.handle_button(role)
                    self.add_item(button)


    def handle_button(self, role_name):
        async def handle(interaction: discord.Interaction):
            guild = interaction.guild
            member = interaction.user
            role_to_get = discord.utils.get(guild.roles, name=role_name)
            
            if role_to_get not in member.roles:
                await member.add_roles(role_to_get)
                await interaction.response.send_message(embed=discord.Embed(title=f"Rolle **{role_name}** hinzugefügt!", colour=6702), ephemeral=True, delete_after=8.0)
            else:
                await member.remove_roles(role_to_get)
                await interaction.response.send_message(embed=discord.Embed(title=f"Rolle **{role_name}** entfernt!", colour=6702), ephemeral=True, delete_after=8.0)
                
        return handle
    


class ChooseTicTacToeEnemy(discord.ui.View):
    def __init__(self, *, timeout = None):
        super().__init__(timeout=timeout)
        
        
    @discord.ui.button(label="Player", style=discord.ButtonStyle.green, disabled=False)
    async def player(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TicTacToeReady()
        user_id = interaction.user.id
        
        if user_id in bot_msg_db:
            channel_id, message_id = bot_msg_db[user_id]
            channel = interaction.client.get_channel(channel_id)
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
                del bot_msg_db[user_id]
            except discord.NotFound:
                print("Nachricht schon gelöscht oder nicht gefunden.")
            except Exception as error:
                print(f"Fehler beim Löschen: {error}")    

        await interaction.response.send_message(embed=discord.Embed(title="Start Game", description="Drücke **Ready** um mitzuspielen! Die ersten zwei sind dabei.", color=discord.Color.green()), view=view)


    @discord.ui.button(label="Computer", style=discord.ButtonStyle.red, disabled=False)
    async def computer(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        board = [i for i in range(1, 10)]
        count = 0
        save_ttt_board(user_id, board, count, opponent_id=None)
        view = TicTacToeEnemyComputer(user_id)
        user_id = interaction.user.id
        
        if user_id in bot_msg_db:
            channel_id, message_id = bot_msg_db[user_id]
            channel = interaction.client.get_channel(channel_id)
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
                del bot_msg_db[user_id]
            except discord.NotFound:
                print("Nachricht schon gelöscht oder nicht gefunden.")
            except Exception as error:
                print(f"Fehler beim Löschen: {error}") 

        await interaction.response.send_message(embed=discord.Embed(title="Spiel läuft:", color=discord.Color.red()), view=view)



class TicTacToeReady(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        self.players = []


    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green, disabled=False)
    async def ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.players:
            await interaction.response.send_message("Du bist schon bereit!", ephemeral=True, delete_after=3.0)
            return
        
        self.players.append(interaction.user.id)
        
        if len(self.players) == 1:
            await interaction.response.send_message(f"{interaction.user.mention} ist bereit! Warte auf einen zweiten Spieler...", ephemeral=True, delete_after=3.0)
        elif len(self.players) == 2:
            user_id = self.players[0]
            opponent_id = self.players[1]
            board = [i for i in range(1, 10)]
            count = 0
            save_ttt_board(user_id, board, count, opponent_id)
            view = TicTacToeEnemyPlayer(user_id)
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(embed=discord.Embed(title="Spiel läuft:", color=discord.Color.green()),view=view)
            await interaction.response.send_message(f"Spiel startet zwischen <@{user_id}> (X) und <@{opponent_id}> (O)!", delete_after=3.0)
        else:
            await interaction.response.send_message("Es sind schon zwei Spieler bereit!", ephemeral=True, delete_after=5.0)



class TicTacToeEnemyPlayer(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        for i in range(9):
            button = discord.ui.Button(label=str(i+1), style=discord.ButtonStyle.secondary, row=i // 3, disabled=False)
            button.callback = self.handle_field(i)
            self.add_item(button)


    def handle_field(self, index):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id
            board, count, opponent_id = load_ttt_board(user_id)
            
            if board is None:
                await interaction.response.send_message("Das Spiel existiert nicht mehr.", ephemeral=True, delete_after=5.0)
                return

            if opponent_id is None and interaction.user.id != user_id:
                opponent_id = interaction.user.id
                save_ttt_board(user_id, board, count, opponent_id)

            if opponent_id is None:
                await interaction.response.send_message("Warte auf einen zweiten Spieler...", ephemeral=True, delete_after=3.0)
                return

            if interaction.user.id not in [user_id, opponent_id]:
                await interaction.response.send_message("Du bist kein Teilnehmer dieses Spiels.", ephemeral=True, delete_after=5.0)
                return

            if (count % 2 == 0 and interaction.user.id != user_id) or (count % 2 == 1 and interaction.user.id != opponent_id):
                await interaction.response.send_message("Du bist nicht am Zug.", ephemeral=True, delete_after=3.0)
                return

            board[index] = "X" if count % 2 == 0 else "O"
            count += 1
            save_ttt_board(user_id, board, count, opponent_id)

            if is_ttt_board_game_over(board):
                winner = get_ttt_winner(board)
                if winner == "Draw":
                    msg = f"{get_ttt_updated_board(board=board)}\n**Game over!**\nDraw!"
                    color = discord.Color.dark_gold()
                else:
                    msg = f"{get_ttt_updated_board(board=board)}\n**Game over!**\nWinner: **{winner}**"
                    color = discord.Color.green() if winner == "X" else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=msg, color=color), view=None)
                delete_ttt_board(user_id)
            else:
                view = TicTacToeEnemyPlayer(user_id)
                for i, item in enumerate(view.children):
                    if isinstance(board[i], str):
                        item.label = board[i]
                        item.disabled = True
                    else:
                        item.label = str(board[i])
                        item.disabled = False
                await interaction.response.edit_message(embed=discord.Embed(title="Spiel läuft:", color=discord.Color.green()), view=view)
        
        return move   



class TicTacToeEnemyComputer(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        for i in range(9):
            button = discord.ui.Button(label=str(i+1), style=discord.ButtonStyle.secondary, row=i // 3, disabled=False)
            button.callback = self.handle_field(i)
            self.add_item(button)


    def handle_field(self, index):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id  
            board, count, _ = load_ttt_board(user_id) 
            board[index] = "X"
            count += 1
            save_ttt_board(user_id, board, count)
            free_field = [i for i, j in enumerate(board) if not isinstance(j, str)]
            
            if free_field:
                bot_index = bot_ttt_num()
                while bot_index not in free_field:
                    bot_index = bot_ttt_num()
                board[bot_index] = "O"
                count += 1
                save_ttt_board(user_id, board, count)

            if is_ttt_board_game_over(board):
                winner = get_ttt_winner(board)
                if winner == "Draw":
                    msg = f"{get_ttt_updated_board(board=board)}\n**Game over!**\nDraw!"
                    color = discord.Color.dark_gold()
                else:
                    msg = f"{get_ttt_updated_board(board=board)}\n**Game over!**\nWinner: **{winner}**"
                    color = discord.Color.green() if winner == "X" else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=msg, color=color), view=None)
                delete_ttt_board(user_id)
                return
            else:
                view = TicTacToeEnemyComputer(user_id)
                for i, item in enumerate(view.children):
                    if isinstance(board[i], str):
                        item.label = board[i]
                        item.disabled = True
                    else:
                        item.label = str(board[i])
                        item.disabled = False
                await interaction.response.edit_message(embed=discord.Embed(title="Spiel läuft:", color=discord.Color.red()), view=view)
        
        return move
    
         
       
class HangmanPlayerReady(discord.ui.View):
    def __init__(self, user_id, word, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id 
        self.word = word
        self.opponent_id = None


    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green, disabled=False)
    async def ready_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if hg_msg_db.get(self.user_id) != interaction.message.id:
            await interaction.response.send_message("Dieses Game wurde abgebrochen.", ephemeral=True, delete_after=5.0)
            return
        
        if not is_hangman_active(self.user_id):
            await interaction.response.send_message("Dieses Spiel existiert nicht mehr.", ephemeral=True, delete_after=5.0)
            return

        if interaction.user.id == self.user_id:
            await interaction.response.send_message("Du bist der Spielleiter. Warte auf einen Gegner!", ephemeral=True, delete_after=3.0)
            return
        
        if self.opponent_id is not None:
            await interaction.response.send_message("Es wurde bereits ein Gegner gefunden!", ephemeral=True, delete_after=3.0)
            return
        
        self.opponent_id = interaction.user.id
        hg_word = ""
        
        for char in self.word:
            hg_word += "◻️ " if char != " " else "\n\n"

        save_hangman(self.user_id, self.opponent_id, self.word, hg_word, 0, set(), 1)
        view = HangmanEnemyPlayerAM(self.user_id)
        
        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=discord.Embed(title="Spiel läuft:", description=hg_word, color=discord.Color.green()), view=view)
        await interaction.response.send_message(f"Das Spiel startet! <@{self.opponent_id}> ist der Gegner.", delete_after=3.0)
        
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, disabled=False)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Nur der Spielleiter kann das Spiel abbrechen.", ephemeral=True, delete_after=5.0)
            return

        delete_hangman(self.user_id)
        
        if self.user_id in bot_msg_db:
            channel_id, message_id = bot_msg_db[self.user_id]
            channel = interaction.client.get_channel(channel_id)
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
                del bot_msg_db[self.user_id]
            except discord.NotFound:
                print("Nachricht schon gelöscht oder nicht gefunden.")
            except Exception as error:
                print(f"Fehler beim Löschen: {error}") 
        
        await interaction.response.send_message("Das Hangman-Spiel wurde abgebrochen.", ephemeral=True, delete_after=5.0)



class HangmanEnemyPlayerAM(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        disabled = get_disabled_buttons(user_id)
        for char in "abcdefghijklm":
            button = discord.ui.Button(label=char.upper(), style=discord.ButtonStyle.secondary, disabled=char.upper() in disabled)
            button.callback = self.handle_field(char)
            self.add_item(button)


    def handle_field(self, letter):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id
            
            if hg_msg_db.get(self.user_id) != interaction.message.id:
                await interaction.response.send_message("Dieses Game wurde abgebrochen.", ephemeral=True, delete_after=5.0)
                return
            
            if not is_hangman_active(self.user_id):
                await interaction.response.send_message("Dieses Spiel existiert nicht mehr.", ephemeral=True, delete_after=5.0)
                return

            opponent_id, word, hg_word, failed_attempts, disabled, _ = load_hangman(user_id)

            if interaction.user.id != opponent_id:
                await interaction.response.send_message("Du bist nicht der Spieler.", ephemeral=True, delete_after=5.0)
                return

            if is_hg_game_over(word, hg_word, failed_attempts):
                opponent = await interaction.guild.fetch_member(opponent_id)
                user = await interaction.guild.fetch_member(user_id)
                title = f"{opponent} hat gewonnen!" if "◻️" not in hg_word else f"{user} hat gewonnen!"
                color = discord.Color.green() if "◻️" not in hg_word else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=title, description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=color), view=None)
                if user_id in hg_msg_db:
                    del hg_msg_db[user_id]
                return

            disabled.add(letter.upper())
            set_disabled_buttons(user_id, disabled)

            if letter.upper() not in word.upper():
                failed_attempts += 1
                save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)
                if failed_attempts >= 6:
                    user = await interaction.guild.fetch_member(user_id)
                    await interaction.response.edit_message(embed=discord.Embed(title=f"{user} hat gewonnen!", description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=discord.Color.red()), view=None)
                    delete_hangman(user_id)
                    if user_id in hg_msg_db:
                        del hg_msg_db[user_id]
                    return

            new_hg_word = ""
            
            for char in word:
                if char == " ":
                    new_hg_word += "\n\n"
                elif char.upper() in disabled:
                    new_hg_word += char.upper() + " "
                else:
                    new_hg_word += "◻️ "

            hg_word = new_hg_word
            save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)

            if "◻️" not in hg_word:
                opponent = await interaction.guild.fetch_member(opponent_id)
                await interaction.response.edit_message(embed=discord.Embed(title=f"{opponent} hat gewonnen!", description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=discord.Color.green()), view=None)
                delete_hangman(user_id)
                if user_id in hg_msg_db:
                    del hg_msg_db[user_id]
            else:
                await interaction.response.edit_message(embed=discord.Embed(title=f"Spiel läuft: ({failed_attempts}/6 Fehlversuche)", description=hg_word, color=discord.Color.green()), view=HangmanEnemyPlayerAM(user_id))
        
        return move


    @discord.ui.button(label="→ N-Z", style=discord.ButtonStyle.primary, row=4)
    async def to_nz(self, interaction: discord.Interaction, button: discord.ui.Button):
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT opponent_id FROM hangman WHERE user_id=?", (self.user_id,))
            opponent_id = cursor.fetchone()[0]
            
        if opponent_id == interaction.user.id:
            await interaction.response.edit_message(view=HangmanEnemyPlayerNZ(self.user_id))
        else:
            await interaction.response.send_message("Du bist nicht der Spieler.", ephemeral=True, delete_after=5.0)



class HangmanEnemyPlayerNZ(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        disabled = get_disabled_buttons(user_id)
        for c in "nopqrstuvwxyz":
            button = discord.ui.Button(label=c.upper(), style=discord.ButtonStyle.secondary, disabled=c.upper() in disabled)
            button.callback = self.handle_field(c)
            self.add_item(button)


    def handle_field(self, letter):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id
            
            if hg_msg_db.get(user_id) != interaction.message.id:
                await interaction.response.send_message("Dieses Game wurde abgebrochen.", ephemeral=True, delete_after=5.0)
                return
            
            if not is_hangman_active(user_id):
                await interaction.response.send_message("Dieses Spiel existiert nicht mehr.", ephemeral=True, delete_after=5.0)
                return

            opponent_id, word, hg_word, failed_attempts, disabled, _ = load_hangman(user_id)

            if interaction.user.id != opponent_id:
                await interaction.response.send_message("Du bist nicht der Spieler.", ephemeral=True, delete_after=5.0)
                return

            if is_hg_game_over(word, hg_word, failed_attempts):
                opponent = await interaction.guild.fetch_member(opponent_id)
                user = await interaction.guild.fetch_member(user_id)
                title = f"{opponent} hat gewonnen!" if "◻️" not in hg_word else f"{user} hat gewonnen!"
                color = discord.Color.green() if "◻️" not in hg_word else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=title, description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=color), view=None)
                if user_id in hg_msg_db:
                    del hg_msg_db[user_id]
                return
            
            disabled.add(letter.upper())
            set_disabled_buttons(user_id, disabled)

            if letter.upper() not in word.upper():
                failed_attempts += 1
                save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)
                if failed_attempts >= 6:
                    user = await interaction.guild.fetch_member(user_id)
                    await interaction.response.edit_message(embed=discord.Embed(title=f"{user} hat gewonnen!", description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=discord.Color.red()), view=None)
                    delete_hangman(user_id)
                    if user_id in hg_msg_db:
                        del hg_msg_db[user_id]
                    return

            new_hg_word = ""
            for char in word:
                if char == " ":
                    new_hg_word += "\n\n"
                elif char.upper() in disabled:
                    new_hg_word += char.upper() + " "
                else:
                    new_hg_word += "◻️ "

            hg_word = new_hg_word
            save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)

            if "◻️" not in hg_word:
                opponent = await interaction.guild.fetch_member(opponent_id)
                await interaction.response.edit_message(embed=discord.Embed(title=f"{opponent} hat gewonnen!", description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=discord.Color.green()), view=None)
                delete_hangman(user_id)
                if user_id in hg_msg_db:
                    del hg_msg_db[user_id]
            else:
                await interaction.response.edit_message(embed=discord.Embed(title=f"Spiel läuft: ({failed_attempts}/6 Fehlversuche)", description=hg_word, color=discord.Color.green()), view=HangmanEnemyPlayerNZ(user_id))
                
        return move


    @discord.ui.button(label="← A-M", style=discord.ButtonStyle.primary, row=4)
    async def to_am(self, interaction: discord.Interaction, button: discord.ui.Button):
        with sqlite3.connect("database.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT opponent_id FROM hangman WHERE user_id=?", (self.user_id,))
            opponent_id = cursor.fetchone()[0]
            
        if opponent_id == interaction.user.id:
            await interaction.response.edit_message(view=HangmanEnemyPlayerAM(self.user_id))
        else:
            await interaction.response.send_message("Du bist nicht der Spieler.", ephemeral=True, delete_after=5.0)



class HangmanComputerReady(discord.ui.View):
    def __init__(self, user_id, word, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.word = word
        
    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green, disabled=False)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = self.user_id
        view = HangmanEnemyComputerAM(self.user_id)
        
        if interaction.user.id != user_id:
            await interaction.response.send_message("Du bist nicht der Spielleiter", ephemeral=True, delete_after=5.0)
            return    
            
        hg_word = ""
        
        for char in self.word:
            hg_word += "◻️ " if char != " " else "\n\n"

        save_hangman(self.user_id, None, self.word, hg_word, 0, set(), 1)
        
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=discord.Embed(title="Spiel läuft:", description=hg_word, color=discord.Color.green()), view=view)



class HangmanEnemyComputerAM(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        disabled = get_disabled_buttons(user_id)
        for char in "abcdefghijklm":
            button = discord.ui.Button(label=char.upper(), style=discord.ButtonStyle.secondary, disabled=char.upper() in disabled)
            button.callback = self.handle_field(char)
            self.add_item(button)


    def handle_field(self, letter):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id
            
            if hg_msg_db.get(user_id) != interaction.message.id:
                await interaction.response.send_message("Dieses Game wurde abgebrochen.", ephemeral=True, delete_after=5.0)
                return
            
            if not is_hangman_active(user_id):
                await interaction.response.send_message("Dieses Spiel existiert nicht mehr.", ephemeral=True, delete_after=5.0)
                return

            if interaction.user.id != user_id:
                await interaction.response.send_message("Du bist nicht der Spieler.", ephemeral=True, delete_after=5.0)
                return
            
            opponent_id, word, hg_word, failed_attempts, disabled, _ = load_hangman(user_id)

            if is_hg_game_over(word, hg_word, failed_attempts):
                user = await interaction.guild.fetch_member(user_id)
                title = f"{user} hat gewonnen!" if "◻️" not in hg_word else "TheDoc hat gewonnen!"
                color = discord.Color.green() if "◻️" not in hg_word else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=title, description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=color), view=None)
                if user_id in hg_msg_db:
                    del hg_msg_db[user_id]
                return

            disabled.add(letter.upper())
            set_disabled_buttons(user_id, disabled)

            if letter.upper() not in word.upper():
                failed_attempts += 1
                save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)
                if failed_attempts >= 6:
                    user = await interaction.guild.fetch_member(user_id)
                    await interaction.response.edit_message(embed=discord.Embed(title="TheDoc hat gewonnen!", description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=discord.Color.red()), view=None)
                    delete_hangman(user_id)
                    if user_id in hg_msg_db:
                        del hg_msg_db[user_id]
                    return

            new_hg_word = ""
            
            for char in word:
                if char == " ":
                    new_hg_word += "\n\n"
                elif char.upper() in disabled:
                    new_hg_word += char.upper() + " "
                else:
                    new_hg_word += "◻️ "

            hg_word = new_hg_word
            save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)

            if "◻️" not in hg_word:
                user = await interaction.guild.fetch_member(user_id)
                await interaction.response.edit_message(embed=discord.Embed(title=f"{user} hat gewonnen!", description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=discord.Color.green()), view=None)
                delete_hangman(user_id)
                if user_id in hg_msg_db:
                    del hg_msg_db[user_id]
            else:
                await interaction.response.edit_message(embed=discord.Embed(title=f"Spiel läuft: ({failed_attempts}/6 Fehlversuche)", description=hg_word, color=discord.Color.green()), view=HangmanEnemyComputerAM(user_id))
        
        return move
    
    
    @discord.ui.button(label="→ N-Z", style=discord.ButtonStyle.primary, row=4)
    async def to_nz(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id == interaction.user.id:
            await interaction.response.edit_message(view=HangmanEnemyComputerNZ(self.user_id))
        else:
            await interaction.response.send_message("Du bist nicht der Spieler.", ephemeral=True, delete_after=5.0)
    
    

class HangmanEnemyComputerNZ(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        disabled = get_disabled_buttons(user_id)
        for c in "nopqrstuvwxyz":
            button = discord.ui.Button(label=c.upper(), style=discord.ButtonStyle.secondary, disabled=c.upper() in disabled)
            button.callback = self.handle_field(c)
            self.add_item(button)


    def handle_field(self, letter):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id
            
            if hg_msg_db.get(user_id) != interaction.message.id:
                await interaction.response.send_message("Dieses Game wurde abgebrochen.", ephemeral=True, delete_after=5.0)
                return
            
            if not is_hangman_active(user_id):
                await interaction.response.send_message("Dieses Spiel existiert nicht mehr.", ephemeral=True, delete_after=5.0)
                return

            if interaction.user.id != user_id:
                await interaction.response.send_message("Du bist nicht der Spielleiter", ephemeral=True, delete_after=5.0)
                return
            
            opponent_id, word, hg_word, failed_attempts, disabled, _ = load_hangman(user_id)

            if is_hg_game_over(word, hg_word, failed_attempts):
                user = await interaction.guild.fetch_member(user_id)
                title = f"{user} hat gewonnen!" if "◻️" not in hg_word else "TheDoc hat gewonnen!"
                color = discord.Color.green() if "◻️" not in hg_word else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=title, description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=color), view=None)
                if user_id in hg_msg_db:
                    del hg_msg_db[user_id]
                return

            disabled.add(letter.upper())
            set_disabled_buttons(user_id, disabled)

            if letter.upper() not in word.upper():
                failed_attempts += 1
                save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)
                if failed_attempts >= 6:
                    user = await interaction.guild.fetch_member(user_id)
                    await interaction.response.edit_message(embed=discord.Embed(title="TheDoc hat gewonnen!", description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=discord.Color.red()), view=None)
                    delete_hangman(user_id)
                    if user_id in hg_msg_db:
                        del hg_msg_db[user_id]
                    return

            new_hg_word = ""
            
            for char in word:
                if char == " ":
                    new_hg_word += "\n\n"
                elif char.upper() in disabled:
                    new_hg_word += char.upper() + " "
                else:
                    new_hg_word += "◻️ "

            hg_word = new_hg_word
            save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)

            if "◻️" not in hg_word:
                user = await interaction.guild.fetch_member(user_id)
                await interaction.response.edit_message(embed=discord.Embed(title=f"{user} hat gewonnen!", description=f"Das Wort lautete: {word}\nFehlversuche: {failed_attempts}", color=discord.Color.green()), view=None)
                delete_hangman(user_id)
                if user_id in hg_msg_db:
                    del hg_msg_db[user_id]
            else:
                await interaction.response.edit_message(embed=discord.Embed(title=f"Spiel läuft: ({failed_attempts}/6 Fehlversuche)", description=hg_word, color=discord.Color.green()), view=HangmanEnemyComputerNZ(user_id))
        
        return move
    

    @discord.ui.button(label="← A-M", style=discord.ButtonStyle.primary, row=4)
    async def to_am(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id == interaction.user.id:
            await interaction.response.edit_message(view=HangmanEnemyComputerAM(self.user_id))
        else:
            await interaction.response.send_message("Du bist nicht der Spieler.", ephemeral=True, delete_after=5.0)