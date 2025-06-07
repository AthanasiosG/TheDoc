import discord, aiosqlite, asyncio
from database import *
from mini_games import *


class VerifyButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)


    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, disabled=False)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        roles = await guild.fetch_roles()
        verified_role = discord.utils.get(roles, name="Verified") or discord.utils.get(roles, name="Verifiziert")
        
        if not verified_role:
            verified_role = await guild.create_role(name="Verified", color=discord.Color.green())
            
        await interaction.user.add_roles(verified_role)
        await interaction.response.send_message(embed=discord.Embed(title="You are now verified!", description="This message will be automatically deleted soon...", colour=6702), ephemeral=True, delete_after=8.0)
        user_id = interaction.user.id
        
        msg_info = await get_bot_message(user_id, "bot")
        
        if msg_info:
            channel_id, message_id = msg_info
            channel = interaction.client.get_channel(channel_id)
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
                await delete_bot_message(user_id, "bot")
            except discord.NotFound:
                print("Message already deleted or not found.")
            except Exception as error:
                print(f"Error while deleting: {error}")    
        
        
    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red, disabled=False)
    async def Deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=discord.Embed(title="You must accept or you will be kicked.", description="This message will be automatically deleted soon...", colour=6702), ephemeral=True, delete_after=8.0)
        


class SupportButtons(discord.ui.View):
    def __init__(self, reason, *, timeout=None):
        super().__init__(timeout=timeout)
        self.reason = reason


    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, disabled=False)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user_id = interaction.user.id
        all_channels = await guild.fetch_channels()
        
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM sup_setup WHERE guild_id = ?", (interaction.guild.id,))
            data = await cursor.fetchone()
            if data:
                sup_team_ch_name = data[2]
        
        view = SupportTeamButtons(user_id)
        support_role = discord.utils.get(guild.roles, name="Support")
        support_channel = discord.utils.get(all_channels, name=sup_team_ch_name)
        
        if self.reason is None:
            self.reason = "None given"
        
        msg = await support_channel.send(embed=discord.Embed(title="A ticket has been opened", description="Reason: " + self.reason, colour=6702), content=support_role.mention, view=view)
        await set_bot_message(interaction.user.id, msg.channel.id, msg.id, "support")
        await interaction.response.edit_message(embed=discord.Embed(title="Success!", description="A support member will handle your ticket soon...", colour=6702),view=None, delete_after=8.0)
        
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, disabled=False)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(embed=discord.Embed(title="Ticket request cancelled.", colour=6702), view=None, delete_after=5.0)



class SupportTeamButtons(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id


    @discord.ui.button(label="Open", style=discord.ButtonStyle.green, disabled=False)
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        user = guild.get_member(self.user_id)
        sup_channel = await guild.create_text_channel(name=f"support-{user.name}")
        await sup_channel.set_permissions(user, read_messages=True, send_messages=True)
        msg_info = await get_bot_message(interaction.user.id, "support")
        
        if msg_info:
            channel_id, message_id = msg_info
            channel = interaction.client.get_channel(channel_id)
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
                await delete_bot_message(interaction.user.id, "support")
            except discord.NotFound:
                print("Support dialog message already deleted or not found.")
            except Exception as error:
                print(f"Error while deleting support dialog message: {error}")
                
        for role in guild.roles:
            if not role.permissions.administrator:
                await sup_channel.set_permissions(role, read_messages=False)

        msg = await interaction.followup.send(embed=discord.Embed(title=f"Ticket opened: {sup_channel.mention}", colour=6702), ephemeral=True)
        support_msg = await sup_channel.send(embed=discord.Embed(title="Ticket opened", description="You are now connected to a support member.", colour=6702), content=user.mention)
        await set_bot_message(self.user_id, sup_channel.id, support_msg.id, "support_ticket")

        try:
            msg_info = await get_bot_message(self.user_id, "support")
            if msg_info:
                channel_id, msg_id = msg_info
                channel = interaction.client.get_channel(channel_id)
                message = await channel.fetch_message(msg_id)
                await message.delete()
                await delete_bot_message(self.user_id, "support")
        except Exception as e:
            print(f"Error while deleting: {e}")

        await asyncio.sleep(15)
        await msg.delete()
        
        
    @discord.ui.button(label="Close", style=discord.ButtonStyle.red, disabled=False)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(embed=discord.Embed(title="Ticket closed", colour=6702), ephemeral=True, delete_after=8.0)
        
        try:
            msg_info = await get_bot_message(self.user_id, "support")
            if msg_info:
                ch_id, msg_id = msg_info
                channel = interaction.client.get_channel(ch_id)
                msg = await channel.fetch_message(msg_id)
                await msg.delete()
                await delete_bot_message(self.user_id, "support")
        except Exception as e:
            print(f"Error while deleting: {e}")
          
            

class CloseTicketButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        
        
    @discord.ui.button(label="Yes", style=discord.ButtonStyle.green, disabled=False)
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
                await interaction.response.send_message("**Error**\nThis command cannot be used in this channel.", ephemeral=True, delete_after=8.0)



class ChooseRole(discord.ui.View):
    def __init__(self, interaction: discord.Interaction):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.guild_id = interaction.guild.id
    
        
    @classmethod
    async def create(cls, interaction: discord.Interaction):
        instance = cls(interaction)
        await instance.setup()
        return instance
    
    
    async def setup(self):
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM role_setup WHERE guild_id = ?", (self.guild_id,))
            for data in await cursor.fetchall():          
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
                await interaction.response.send_message(embed=discord.Embed(title=f"Role **{role_name}** added!", colour=6702), ephemeral=True, delete_after=8.0)
            else:
                await member.remove_roles(role_to_get)
                await interaction.response.send_message(embed=discord.Embed(title=f"Role **{role_name}** removed!", colour=6702), ephemeral=True, delete_after=8.0)
                
        return handle
    


class ChooseTicTacToeEnemy(discord.ui.View):
    def __init__(self, *, timeout = None):
        super().__init__(timeout=timeout)
        
        
    @discord.ui.button(label="Player", style=discord.ButtonStyle.green, disabled=False)
    async def player(self, interaction: discord.Interaction, button: discord.ui.Button):
        view = TicTacToeReady()
        user_id = interaction.user.id
        msg_info = await get_bot_message(user_id, "bot")
        
        if msg_info:
            channel_id, message_id = msg_info
            channel = interaction.client.get_channel(channel_id)
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
                await delete_bot_message(user_id, "bot")
            except discord.NotFound:
                print("Message already deleted or not found.")
            except Exception as error:
                print(f"Error while deleting: {error}")    

        await interaction.response.send_message(embed=discord.Embed(title="Start Game", description="Press **Ready** to join! The first two will play.", color=discord.Color.green()), view=view)


    @discord.ui.button(label="Computer", style=discord.ButtonStyle.red, disabled=False)
    async def computer(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        board = [i for i in range(1, 10)]
        count = 0
        await save_ttt_board(user_id, board, count, opponent_id=None)
        view = TicTacToeEnemyComputer(user_id)
        msg_info = await get_bot_message(user_id, "bot")
        
        if msg_info:
            channel_id, message_id = msg_info
            channel = interaction.client.get_channel(channel_id)
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
                await delete_bot_message(user_id, "bot")
            except discord.NotFound:
                print("Message already deleted or not found.")
            except Exception as error:
                print(f"Error while deleting: {error}") 

        await interaction.response.send_message(embed=discord.Embed(title="Game running:", color=discord.Color.red()), view=view)



class TicTacToeReady(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)
        self.players = []


    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green, disabled=False)
    async def ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id in self.players:
            await interaction.response.send_message("You are already ready!", ephemeral=True, delete_after=3.0)
            return
        
        self.players.append(interaction.user.id)
        
        if len(self.players) == 1:
            await interaction.response.send_message(f"{interaction.user.mention} is ready! Waiting for a second player...", ephemeral=True, delete_after=3.0)
        elif len(self.players) == 2:
            user_id = self.players[0]
            opponent_id = self.players[1]
            board = [i for i in range(1, 10)]
            count = 0
            await save_ttt_board(user_id, board, count, opponent_id)
            view = TicTacToeEnemyPlayer(user_id)
            for item in self.children:
                item.disabled = True
            await interaction.message.edit(embed=discord.Embed(title="Game running:", color=discord.Color.green()),view=view)
            await interaction.response.send_message(f"Game starts between <@{user_id}> (X) and <@{opponent_id}> (O)!", delete_after=3.0)
        else:
            await interaction.response.send_message("There are already two players ready!", ephemeral=True, delete_after=5.0)



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
            board, count, opponent_id = await load_ttt_board(user_id)
            
            if board is None:
                await interaction.response.send_message("The game no longer exists.", ephemeral=True, delete_after=5.0)
                return

            if opponent_id is None and interaction.user.id != user_id:
                opponent_id = interaction.user.id
                await save_ttt_board(user_id, board, count, opponent_id)

            if opponent_id is None:
                await interaction.response.send_message("Waiting for a second player...", ephemeral=True, delete_after=3.0)
                return

            if interaction.user.id not in [user_id, opponent_id]:
                await interaction.response.send_message("You are not a participant in this game.", ephemeral=True, delete_after=5.0)
                return

            if (count % 2 == 0 and interaction.user.id != user_id) or (count % 2 == 1 and interaction.user.id != opponent_id):
                await interaction.response.send_message("It's not your turn.", ephemeral=True, delete_after=3.0)
                return

            board[index] = "X" if count % 2 == 0 else "O"
            count += 1
            await save_ttt_board(user_id, board, count, opponent_id)

            if is_ttt_board_game_over(board):
                winner = get_ttt_winner(board)
                if winner == "Draw":
                    msg = f"{get_ttt_updated_board(board=board)}\n**Game over!**\nDraw!"
                    color = discord.Color.dark_gold()
                else:
                    msg = f"{get_ttt_updated_board(board=board)}\n**Game over!**\nWinner: **{winner}**"
                    color = discord.Color.green() if winner == "X" else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=msg, color=color), view=None)
                await delete_ttt_board(user_id)
            else:
                view = TicTacToeEnemyPlayer(user_id)
                for i, item in enumerate(view.children):
                    if isinstance(board[i], str):
                        item.label = board[i]
                        item.disabled = True
                    else:
                        item.label = str(board[i])
                        item.disabled = False
                await interaction.response.edit_message(embed=discord.Embed(title="Game in progress:", color=discord.Color.green()), view=view)
        
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
            board, count, _ = await load_ttt_board(user_id) 
            board[index] = "X"
            count += 1
            await save_ttt_board(user_id, board, count)
            free_field = [i for i, j in enumerate(board) if not isinstance(j, str)]
            
            if free_field:
                bot_index = bot_ttt_num()
                while bot_index not in free_field:
                    bot_index = bot_ttt_num()
                board[bot_index] = "O"
                count += 1
                await save_ttt_board(user_id, board, count)

            if is_ttt_board_game_over(board):
                winner = get_ttt_winner(board)
                if winner == "Draw":
                    msg = f"{get_ttt_updated_board(board=board)}\n**Game over!**\nDraw!"
                    color = discord.Color.dark_gold()
                else:
                    msg = f"{get_ttt_updated_board(board=board)}\n**Game over!**\nWinner: **{winner}**"
                    color = discord.Color.green() if winner == "X" else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=msg, color=color), view=None)
                await delete_ttt_board(user_id)
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
                await interaction.response.edit_message(embed=discord.Embed(title="Game in progress:", color=discord.Color.red()), view=view)
        
        return move
    
         
       
class HangmanPlayerReady(discord.ui.View):
    def __init__(self, user_id, word, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id 
        self.word = word
        self.opponent_id = None


    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green, disabled=False)
    async def ready_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        msg_info = await get_bot_message(self.user_id, "hangman")
        if msg_info and msg_info[1] != interaction.message.id:
            await interaction.response.send_message("This game has been cancelled.", ephemeral=True, delete_after=5.0)
            return
        
        if not await is_hangman_active(self.user_id):
            await interaction.response.send_message("This game no longer exists.", ephemeral=True, delete_after=5.0)
            return

        if interaction.user.id == self.user_id:
            await interaction.response.send_message("You are the game master. Wait for an opponent!", ephemeral=True, delete_after=3.0)
            return
        
        if self.opponent_id is not None:
            await interaction.response.send_message("An opponent has already been found!", ephemeral=True, delete_after=3.0)
            return
        
        self.opponent_id = interaction.user.id
        hg_word = ""
        
        for char in self.word:
            hg_word += "◻️ " if char != " " else "\n\n"

        await save_hangman(self.user_id, self.opponent_id, self.word, hg_word, 0, set(), 1)
        view = await HangmanEnemyPlayerAM.create(self.user_id)
        
        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=discord.Embed(title="Game in progress:", description=hg_word, color=discord.Color.green()), view=view)
        await interaction.response.send_message(f"The game starts! <@{self.opponent_id}> is the opponent.", delete_after=3.0)
        
        
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, disabled=False)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("Only the game master can cancel the game.", ephemeral=True, delete_after=5.0)
            return

        await delete_hangman(self.user_id)
        msg_info = await get_bot_message(self.user_id, "hangman")
        
        if msg_info:
            channel_id, message_id = msg_info
            channel = interaction.client.get_channel(channel_id)
            try:
                message = await channel.fetch_message(message_id)
                await message.delete()
                await delete_bot_message(self.user_id, "hangman")
            except discord.NotFound:
                print("Message already deleted or not found.")
            except Exception as error:
                print(f"Error while deleting: {error}") 
        
        await interaction.response.send_message("The Hangman game has been cancelled.", ephemeral=True, delete_after=5.0)



class HangmanEnemyPlayerAM(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
    
        
    @classmethod
    async def create(cls, user_id):
        instance = cls(user_id)
        await instance.setup()
        return instance
    
        
    async def setup(self):
        disabled = await get_disabled_buttons(self.user_id)
        for char in "abcdefghijklm":
            button = discord.ui.Button(label=char.upper(), style=discord.ButtonStyle.secondary, disabled=char.upper() in disabled)
            button.callback = self.handle_field(char)
            self.add_item(button)


    def handle_field(self, letter):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id
            msg_info = await get_bot_message(user_id, "hangman")
            
            if msg_info and msg_info[1] != interaction.message.id:
                await interaction.response.send_message("This game has been cancelled.", ephemeral=True, delete_after=5.0)
                return
            
            if not await is_hangman_active(self.user_id):
                await interaction.response.send_message("This game no longer exists.", ephemeral=True, delete_after=5.0)
                return

            opponent_id, word, hg_word, failed_attempts, disabled, _ = await load_hangman(user_id)

            if interaction.user.id != opponent_id:
                await interaction.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)
                return

            if is_hg_game_over(word, hg_word, failed_attempts):
                opponent = await interaction.guild.fetch_member(opponent_id)
                user = await interaction.guild.fetch_member(user_id)
                title = f"{opponent} has won!" if "◻️" not in hg_word else f"{user} has won!"
                color = discord.Color.green() if "◻️" not in hg_word else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=title, description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=color), view=None)
                await delete_bot_message(user_id, "hangman")
                return

            disabled.add(letter.upper())
            await set_disabled_buttons(user_id, disabled)

            if letter.upper() not in word.upper():
                failed_attempts += 1
                await save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)
                if failed_attempts >= 6:
                    user = await interaction.guild.fetch_member(user_id)
                    await interaction.response.edit_message(embed=discord.Embed(title=f"{user} has won!", description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=discord.Color.red()), view=None)
                    await delete_hangman(user_id)
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
            await save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)

            if "◻️" not in hg_word:
                opponent = await interaction.guild.fetch_member(opponent_id)
                await interaction.response.edit_message(embed=discord.Embed(title=f"{opponent} has won!", description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=discord.Color.green()), view=None)
                await delete_hangman(user_id)
            else:
                await interaction.response.edit_message(embed=discord.Embed(title=f"Game in progress: ({failed_attempts}/6 failed attempts)", description=hg_word, color=discord.Color.green()), view=await HangmanEnemyPlayerAM.create(user_id))
        
        return move


    @discord.ui.button(label="→ N-Z", style=discord.ButtonStyle.primary, row=4)
    async def to_nz(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT opponent_id FROM hangman WHERE user_id=?", (self.user_id,))
            opponent_id = await cursor.fetchone()
            opponent_id = opponent_id[0]
            
        if opponent_id == interaction.user.id:
            await interaction.response.edit_message(view=await HangmanEnemyPlayerNZ.create(self.user_id))
        else:
            await interaction.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)



class HangmanEnemyPlayerNZ(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
     
        
    @classmethod
    async def create(cls, user_id):
        instance = cls(user_id)
        await instance.setup()
        return instance      
        
        
    async def setup(self):
        disabled = await get_disabled_buttons(self.user_id)
        for c in "nopqrstuvwxyz":
            button = discord.ui.Button(label=c.upper(), style=discord.ButtonStyle.secondary, disabled=c.upper() in disabled)
            button.callback = self.handle_field(c)
            self.add_item(button)


    def handle_field(self, letter):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id
            msg_info = await get_bot_message(user_id, "hangman")
            
            if msg_info and msg_info[1] != interaction.message.id:
                await interaction.response.send_message("This game has been cancelled.", ephemeral=True, delete_after=5.0)
                return
            
            if not await is_hangman_active(user_id):
                await interaction.response.send_message("This game no longer exists.", ephemeral=True, delete_after=5.0)
                return

            opponent_id, word, hg_word, failed_attempts, disabled, _ = await load_hangman(user_id)

            if interaction.user.id != opponent_id:
                await interaction.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)
                return

            if is_hg_game_over(word, hg_word, failed_attempts):
                opponent = await interaction.guild.fetch_member(opponent_id)
                user = await interaction.guild.fetch_member(user_id)
                title = f"{opponent} has won!" if "◻️" not in hg_word else f"{user} has won!"
                color = discord.Color.green() if "◻️" not in hg_word else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=title, description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=color), view=None)
                await delete_bot_message(user_id, "hangman")
                return
            
            disabled.add(letter.upper())
            await set_disabled_buttons(user_id, disabled)

            if letter.upper() not in word.upper():
                failed_attempts += 1
                await save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)
                if failed_attempts >= 6:
                    user = await interaction.guild.fetch_member(user_id)
                    await interaction.response.edit_message(embed=discord.Embed(title=f"{user} has won!", description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=discord.Color.red()), view=None)
                    await delete_hangman(user_id)
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
            await save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)

            if "◻️" not in hg_word:
                opponent = await interaction.guild.fetch_member(opponent_id)
                await interaction.response.edit_message(embed=discord.Embed(title=f"{opponent} has won!", description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=discord.Color.green()), view=None)
                await delete_bot_message(user_id, "hangman")
            else:
                await interaction.response.edit_message(embed=discord.Embed(title=f"Game in progress: ({failed_attempts}/6 failed attempts)", description=hg_word, color=discord.Color.green()), view=await HangmanEnemyPlayerNZ.create(user_id))
                
        return move


    @discord.ui.button(label="← A-M", style=discord.ButtonStyle.primary, row=4)
    async def to_am(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT opponent_id FROM hangman WHERE user_id=?", (self.user_id,))
            opponent_id = await cursor.fetchone()
            opponent_id = opponent_id[0]
            
        if opponent_id == interaction.user.id:
            await interaction.response.edit_message(view=await HangmanEnemyPlayerAM.create(self.user_id))
        else:
            await interaction.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)



class HangmanComputerReady(discord.ui.View):
    def __init__(self, user_id, word, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.word = word
        
        
    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green, disabled=False)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = self.user_id
        view = await HangmanEnemyComputerAM.create(self.user_id)
        
        if interaction.user.id != user_id:
            await interaction.response.send_message("You are not the game master", ephemeral=True, delete_after=5.0)
            return    
            
        hg_word = ""
        
        for char in self.word:
            hg_word += "◻️ " if char != " " else "\n\n"

        await save_hangman(self.user_id, None, self.word, hg_word, 0, set(), 1)
        
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(embed=discord.Embed(title="Game in progress:", description=hg_word, color=discord.Color.green()), view=view)



class HangmanEnemyComputerAM(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
    
    
    @classmethod
    async def create(cls, user_id: int):
        instance = cls(user_id)
        await instance.setup()
        return instance
    
            
    async def setup(self):
        disabled = await get_disabled_buttons(self.user_id)
        for char in "abcdefghijklm":
            button = discord.ui.Button(label=char.upper(), style=discord.ButtonStyle.secondary, disabled=char.upper() in disabled)
            button.callback = self.handle_field(char)
            self.add_item(button)


    def handle_field(self, letter):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id
            msg_info = await get_bot_message(user_id, "hangman")
            
            if msg_info and msg_info[1] != interaction.message.id:
                await interaction.response.send_message("This game has been cancelled.", ephemeral=True, delete_after=5.0)
                return
            
            if not await is_hangman_active(user_id):
                await interaction.response.send_message("This game no longer exists.", ephemeral=True, delete_after=5.0)
                return

            if interaction.user.id != user_id:
                await interaction.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)
                return
            
            opponent_id, word, hg_word, failed_attempts, disabled, _ = await load_hangman(user_id)

            if is_hg_game_over(word, hg_word, failed_attempts):
                user = await interaction.guild.fetch_member(user_id)
                title = f"{user} has won!" if "◻️" not in hg_word else "TheDoc has won!"
                color = discord.Color.green() if "◻️" not in hg_word else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=title, description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=color), view=None)
                await delete_bot_message(user_id, "hangman")
                return

            disabled.add(letter.upper())
            await set_disabled_buttons(user_id, disabled)

            if letter.upper() not in word.upper():
                failed_attempts += 1
                await save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)
                if failed_attempts >= 6:
                    user = await interaction.guild.fetch_member(user_id)
                    await interaction.response.edit_message(embed=discord.Embed(title="TheDoc has won!", description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=discord.Color.red()), view=None)
                    await delete_hangman(user_id)
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
            await save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)

            if "◻️" not in hg_word:
                user = await interaction.guild.fetch_member(user_id)
                await interaction.response.edit_message(embed=discord.Embed(title=f"{user} has won!", description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=discord.Color.green()), view=None)
                await delete_bot_message(user_id, "hangman")
            else:
                await interaction.response.edit_message(embed=discord.Embed(title=f"Game in progress: ({failed_attempts}/6 failed attempts)", description=hg_word, color=discord.Color.green()), view=await HangmanEnemyComputerAM.create(user_id))
        
        return move


    @discord.ui.button(label="→ N-Z", style=discord.ButtonStyle.primary, row=4)
    async def to_nz(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id == interaction.user.id:
            await interaction.response.edit_message(view=await HangmanEnemyComputerNZ.create(self.user_id))
        else:
            await interaction.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)
    
    

class HangmanEnemyComputerNZ(discord.ui.View):
    def __init__(self, user_id, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        
        
    @classmethod
    async def create(cls, user_id: int):
        instance = cls(user_id)
        await instance.setup()
        return instance
    
            
    async def setup(self):
        disabled = await get_disabled_buttons(self.user_id)
        for c in "nopqrstuvwxyz":
            button = discord.ui.Button(label=c.upper(), style=discord.ButtonStyle.secondary, disabled=c.upper() in disabled)
            button.callback = self.handle_field(c)
            self.add_item(button)


    def handle_field(self, letter):
        async def move(interaction: discord.Interaction):
            user_id = self.user_id
            msg_info = await get_bot_message(user_id, "hangman")
            
            if msg_info and msg_info[1] != interaction.message.id:
                await interaction.response.send_message("This game has been cancelled.", ephemeral=True, delete_after=5.0)
                return
            
            if not await is_hangman_active(user_id):
                await interaction.response.send_message("This game no longer exists.", ephemeral=True, delete_after=5.0)
                return

            if interaction.user.id != user_id:
                await interaction.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)
                return
            
            opponent_id, word, hg_word, failed_attempts, disabled, _ = await load_hangman(user_id)

            if is_hg_game_over(word, hg_word, failed_attempts):
                user = await interaction.guild.fetch_member(user_id)
                title = f"{user} has won!" if "◻️" not in hg_word else "TheDoc has won!"
                color = discord.Color.green() if "◻️" not in hg_word else discord.Color.red()
                await interaction.response.edit_message(embed=discord.Embed(title=title, description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=color), view=None)
                await delete_bot_message(user_id, "hangman")
                return

            disabled.add(letter.upper())
            await set_disabled_buttons(user_id, disabled)

            if letter.upper() not in word.upper():
                failed_attempts += 1
                await save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)
                if failed_attempts >= 6:
                    user = await interaction.guild.fetch_member(user_id)
                    await interaction.response.edit_message(embed=discord.Embed(title="TheDoc has won!", description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=discord.Color.red()), view=None)
                    await delete_hangman(user_id)
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
            await save_hangman(user_id, opponent_id, word, hg_word, failed_attempts, disabled, 1)

            if "◻️" not in hg_word:
                user = await interaction.guild.fetch_member(user_id)
                await interaction.response.edit_message(embed=discord.Embed(title=f"{user} has won!", description=f"The word was: {word}\nFailed attempts: {failed_attempts}", color=discord.Color.green()), view=None)
                await delete_bot_message(user_id, "hangman")
            else:
                await interaction.response.edit_message(embed=discord.Embed(title=f"Game in progress: ({failed_attempts}/6 failed attempts)", description=hg_word, color=discord.Color.green()), view=await HangmanEnemyComputerNZ.create(user_id))
        
        return move


    @discord.ui.button(label="← A-M", style=discord.ButtonStyle.primary, row=4)
    async def to_am(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.user_id == interaction.user.id:
            await interaction.response.edit_message(view=await HangmanEnemyComputerAM.create(self.user_id))
        else:
            await interaction.response.send_message("You are not the player.", ephemeral=True, delete_after=5.0)
            
            
            
class Quiz(discord.ui.View):
    def __init__(self, user_id, question, answer_choices, answer, difficulty, *, timeout=None):
        super().__init__(timeout=timeout)
        self.user_id = user_id
        self.question = question
        self.answer_choices = answer_choices
        self.answer = answer
        self.difficulty = difficulty
        for choice in answer_choices:
            button = discord.ui.Button(label=choice, style=discord.ButtonStyle.primary, disabled=False)
            button.callback = self.handle_field(choice)
            self.add_item(button)
            
            
    def handle_field(self, choice):
        async def move(interaction: discord.Interaction):
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("You are not the player.",ephemeral=True, delete_after=5.0)
                return
            
            if choice == self.answer:
                if self.difficulty == 1:
                    points = 2
                elif self.difficulty == 2:
                    points = 4
                elif self.difficulty == 3:
                    points = 6
                elif self.difficulty == 4:
                    points = 8
                elif self.difficulty == 5:
                    points = 10
                await interaction.response.edit_message(embed=discord.Embed(title="Correct!", description=f"Question: {self.question}\nThe answer **{self.answer}** is correct!\nYou have gained {points} points!", color=discord.Color.green()), view=None)
            else:
                if self.difficulty == 1:
                    points = -1
                elif self.difficulty == 2:
                    points = -2
                elif self.difficulty == 3:
                    points = -3
                elif self.difficulty == 4:
                    points = -4
                elif self.difficulty == 5:
                    points = -5

                async with aiosqlite.connect("database.db") as conn:
                    cursor = await conn.cursor()
                    await cursor.execute("SELECT points FROM quiz_points WHERE guild_id=? AND user_id=?", (interaction.guild.id, self.user_id))
                    row = await cursor.fetchone()
                    current_points = row[0] if row else 0
                    if current_points + points < 0:
                        points = -current_points
                await interaction.response.edit_message(embed=discord.Embed(title="Wrong!", description=f"Question: {self.question}\nThe correct answer is: **{self.answer}**\nYou have lost {points} points!", color=discord.Color.red()), view=None)

            async with aiosqlite.connect("database.db") as conn:
                cursor = await conn.cursor()
                await cursor.execute("INSERT OR IGNORE INTO quiz_points (guild_id, user_id, points) VALUES (?, ?, 0)", (interaction.guild.id, self.user_id))
                await cursor.execute("UPDATE quiz_points SET points=points+? WHERE guild_id=? AND user_id=?", (points, interaction.guild.id, self.user_id))
                await conn.commit()
                
        return move