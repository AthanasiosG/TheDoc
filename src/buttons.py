import discord, sqlite3, asyncio
from database import support_db, bot_msg_db
from mini_games import save_tictactoe_board, load_tictactoe_board, delete_tictactoe_board, is_board_game_over, get_updated_board, get_winner, bot_num


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


class ChoseRole(discord.ui.View):
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
        
        save_tictactoe_board(user_id, board, count, opponent_id=None)
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
            save_tictactoe_board(user_id, board, count, opponent_id)
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
            board, count, opponent_id = load_tictactoe_board(user_id)
            if board is None:
                await interaction.response.send_message("Das Spiel existiert nicht mehr.", ephemeral=True, delete_after=5.0)
                return

            if opponent_id is None and interaction.user.id != user_id:
                opponent_id = interaction.user.id
                save_tictactoe_board(user_id, board, count, opponent_id)

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
            save_tictactoe_board(user_id, board, count, opponent_id)

            if is_board_game_over(board):
                winner = get_winner(board)
                if winner == "Draw":
                    msg = f"{get_updated_board(board=board)}\n**Game over!**\nDraw!"
                else:
                    msg = f"{get_updated_board(board=board)}\n**Game over!**\nWinner: **{winner}**"
                await interaction.response.edit_message(embed=discord.Embed(title=msg, color=discord.Color.green()), view=None)
                delete_tictactoe_board(user_id)
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
            board, count, _ = load_tictactoe_board(user_id)  # Fix: unpack only needed values
            board[index] = "X"
            count += 1
            save_tictactoe_board(user_id, board, count)

            if is_board_game_over(board):
                winner = get_winner(board)
                if winner == "Draw":
                    msg = f"{get_updated_board(board=board)}\n**Game over!**\nDraw!"
                else:
                    msg = f"{get_updated_board(board=board)}\n**Game over!**\nWinner: **{winner}**"
                await interaction.response.edit_message(embed=discord.Embed(title=msg), view=None)
                delete_tictactoe_board(user_id)
                return

            free_field = [i for i, j in enumerate(board) if not isinstance(j, str)]
            
            if free_field:
                bot_index = bot_num()
                while bot_index not in free_field:
                    bot_index = bot_num()
                board[bot_index] = "O"
                count += 1
                save_tictactoe_board(user_id, board, count)

            if is_board_game_over(board):
                winner = get_winner(board)
                if winner == "Draw":
                    msg = f"{get_updated_board(board=board)}\n**Game over!**\nDraw!"
                else:
                    msg = f"{get_updated_board(board=board)}\n**Game over!**\nWinner: **{winner}**"
                await interaction.response.edit_message(embed=discord.Embed(title=msg, color=discord.Color.red()), view=None)
                delete_tictactoe_board(user_id)
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