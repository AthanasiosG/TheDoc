import discord, random, aiosqlite, aiofiles, asyncio, json, random
from discord import app_commands
from discord.ext import commands
from buttons import *
from database import *
from mini_games import *


class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @app_commands.command(name="all_commands", description="All available bot commands")
    async def all_commands(self, interaction: discord.Interaction):   
        cmd_list = [cmd.name for cmd in self.bot.tree.get_commands()]
        all_cmd = ""
        
        for cmd in cmd_list:
            all_cmd += "/" + cmd + "\n"
            
        await interaction.response.send_message(embed=discord.Embed(title="These are all available commands:", description=all_cmd, colour=6702))
   
   
    @app_commands.command(name="license", description="Terms of Use & Privacy Policy")
    async def license(self, interaction: discord.Interaction):
        text = (
            "📄 **Terms of Use for TheDoc**\n"
            "1. By using TheDoc, you agree to the terms of use and privacy policy.\n"
            "2. The use of TheDoc is voluntary and at your own risk.\n"
            "3. No guarantee is given for availability, error-free operation, or functionality.\n"
            "4. The bot may not be used for illegal, abusive, or harmful purposes.\n"
            "5. Usage can be terminated at any time by removing the bot.\n"
            "6. By using, you accept these terms. Changes may occur at any time.\n\n\n"
            "🔒 **Privacy at TheDoc**\n"
            "1. TheDoc stores technical data such as server ID, user ID, or emoji assignments for certain features (e.g., quiz, role assignment).\n"
            "2. No sensitive personal data is stored (e.g., name, IP, email).\n"
            "3. The data is used solely for the bot's functionality and is not shared with third parties.\n"
            "4. The bot is operated on a server in the EU."
        )

        embed = discord.Embed(description=text, color=discord.Color.green())
        embed.set_thumbnail(url="https://raw.githubusercontent.com/AthanasiosG/TheDoc/main/images/thedoc.png")
        await interaction.response.send_message(embed=embed)


    @app_commands.command(name="bot_info", description="Info about the bot")
    async def info_about_bot(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title="My name is TheDoc and I was programmed by Thanos.", colour=6702))


    @app_commands.command(name="server_owner", description="Shows who owns the server")
    async def server_owner(self, interaction: discord.Interaction):
        owner = interaction.guild.owner
        await interaction.response.send_message(embed=discord.Embed(title="The server belongs to " + str(owner) +"!", colour=6702))

    
    @app_commands.command(name="verify", description="Verification")
    async def verify(self, interaction: discord.Interaction):
        roles = await interaction.guild.fetch_roles()
        verified_role = discord.utils.get(roles, name="Verified") or discord.utils.get(roles, name="Verifiziert")       
        is_verified = False
        
        for role in interaction.user.roles:
            if role == verified_role:
                is_verified = True
                
        if is_verified:
            await interaction.response.send_message(embed=discord.Embed(title="You are already verified!", description="This message will be automatically deleted soon...", colour=6702), ephemeral=True, delete_after=8.0)
        else:
            rules = "Please follow the general Discord rules"
            embed = discord.Embed(title=rules, description="To accept the rules, click the green button. To decline, click the red button.",color=discord.Color.green())
            embed.set_thumbnail(url="https://kwiqreply.io/img/icon/verify.png")
            view = VerifyButtons()
            await interaction.response.send_message(embed=embed, view=view)
            sent_msg = await interaction.original_response()
            await set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "bot")


    @app_commands.command(name="clear", description="Deletes messages in the channel")
    @app_commands.checks.has_permissions(administrator=True)
    async def clear(self, interaction: discord.Interaction, amount: int):
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f"{len(deleted)} messages deleted.", ephemeral=True)


    @app_commands.command(name="kick", description="Kick a user")
    @app_commands.checks.has_permissions(administrator=True)
    async def kick(self, interaction: discord.Interaction, user: discord.User, reason: str):
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("INSERT INTO server_kicked VALUES (?)", (user.id,))
            await conn.commit()
            
        await interaction.guild.kick(user=user, reason=reason)
        await user.send(embed=discord.Embed(title="You have been kicked for the following reason:", description=reason, color=discord.Color.red()))
        msg = f"{user} was successfully kicked!"
        await interaction.user.send(embed=discord.Embed(title=msg, description="Reason: " + reason, color=discord.Color.red()))
        await interaction.response.defer(ephemeral=True)        
        await interaction.followup.send(f"Process completed. User kicked.", ephemeral=True)


    @app_commands.command(name="ban", description="Ban a user")
    @app_commands.checks.has_permissions(administrator=True)
    async def ban(self, interaction: discord.Interaction, user: discord.User, reason: str):
        await interaction.guild.ban(user=user, reason=reason)
        await user.send(embed=discord.Embed(title="You have been banned for the following reason:", description=reason, color=discord.Color.red()))
        msg = f"{user} was successfully banned!"
        await interaction.user.send(embed=discord.Embed(title=msg, description="Reason: " + reason, color=discord.Color.red()))
        await interaction.response.defer(ephemeral=True)        
        await interaction.followup.send(f"Process completed. User banned.", ephemeral=True)
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("INSERT INTO server_kicked VALUES (?)", (user.id,))
            await conn.commit()


    @app_commands.command(name="roles", description="All available roles")
    async def server_rollen(self, interaction: discord.Interaction):
        all_roles = [role.name for role in await interaction.guild.fetch_roles()]
        roles = ""
        
        for idx, role in enumerate(all_roles):
            roles += f"{idx+1}: " + role + "\n"
        await interaction.response.send_message(embed=discord.Embed(title="All roles", description=roles, colour=6702))          


    @app_commands.command(name="role_setup", description="Setup for roles -> roles that everyone can get")
    @app_commands.checks.has_permissions(administrator=True)
    async def role_setup(self, interaction: discord.Interaction):
        await interaction.user.send(embed=discord.Embed(title="Role setup", description="Assign roles with emojis. Essential for /choose_roles.\n\nIMPORTANT: Send the following message in exactly this format:\n\n!role_setup [role_name]:[emoji] [role_name]:[emoji]...\n'role_name' = actual name \n 'emoji' = desired emoji for the role\n\nExample: !role_setup VIP:💎 Member:🙄", colour=6702))
        await interaction.response.send_message(embed=discord.Embed(title="Check your DMs.",description="I have sent you instructions.", colour=6702), ephemeral=True, delete_after=8.0)
        
        
    @app_commands.command(name="choose_roles", description="Choose the roles you want")
    async def chose_role(self, interaction: discord.Interaction):
        view = await ChooseRole.create(interaction)
        role_emoji = ""
        
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM role_setup WHERE guild_id=?", (interaction.guild.id,))     
            for data in await cursor.fetchall():
                role_emoji += f"{data[1]}: {data[2]}\n"        
            server_found = False
            await cursor.execute("SELECT * FROM role_setup")  
            for data in await cursor.fetchall():
                if interaction.guild.id == data[0]:
                    server_found = True
            if server_found:
                await interaction.response.send_message(embed=discord.Embed(title=f"Choose your roles:", description=role_emoji, colour=6702), view=view, ephemeral=True)
                role_emoji = ""
            else:
                await interaction.response.send_message(embed=discord.Embed(title=f"No role setup done yet -> /role_setup", colour=6702), ephemeral=True, delete_after=10.0)


    @app_commands.command(name="support_setup", description="Setup to use the support system")
    @app_commands.checks.has_permissions(administrator=True)
    async def sup_setup(self, interaction: discord.Interaction, sup_ch_name: str, sup_team_ch_name: str, sup_role: str):        
        all_channels = await interaction.guild.fetch_channels()        
        all_roles = await interaction.guild.fetch_roles()
        await interaction.response.defer(ephemeral=True)

        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM sup_setup WHERE guild_id=?", (interaction.guild.id,))
            data = await cursor.fetchone()
            if data:
                channel_one = discord.utils.get(all_channels, name=data[1])
                channel_two = discord.utils.get(all_channels, name=data[2])
                if channel_one:
                    await channel_one.delete()
                if channel_two:
                    await channel_two.delete()
                await cursor.execute("DELETE FROM sup_setup WHERE guild_id=?", (interaction.guild.id,))
                await conn.commit()
            await interaction.guild.create_text_channel(name=sup_ch_name)
            support_team_channel = await interaction.guild.create_text_channel(name=sup_team_ch_name)
            await cursor.execute("INSERT INTO sup_setup VALUES (?,?,?,?)", (interaction.guild.id, sup_ch_name, sup_team_ch_name, sup_role))
            await conn.commit()

        support_role = discord.utils.get(interaction.guild.roles, name=sup_role)

        for role in all_roles:
            if role.name == support_role.name:
                await support_team_channel.set_permissions(target=role, read_messages=True, send_messages=True)      
            else:
                await support_team_channel.set_permissions(target=role, read_messages=False, send_messages=False)

        await interaction.followup.send("Setup saved!", ephemeral=True)
            
            
    @app_commands.command(name="support", description="Get help from support")
    async def support(self, interaction: discord.Interaction, reason: str = None):
        guild = interaction.guild
        view = SupportButtons(reason)
        all_channels = await guild.fetch_channels()

        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT guild_id FROM sup_setup WHERE guild_id=?", (interaction.guild.id,))
            if not await cursor.fetchall():
                await interaction.response.send_message(embed=discord.Embed(title="Error:", description="No setup has been done yet. Please run /support_setup.", colour=6702), ephemeral=True, delete_after=10.0)
            else:   
                await cursor.execute("SELECT * FROM sup_setup")
                for data in await cursor.fetchall():
                    if data[0] == interaction.guild.id:
                        sup_ch_name = data[1]
                sup_channel = discord.utils.get(all_channels, name=sup_ch_name)
                if interaction.channel == sup_channel:
                    await interaction.response.send_message(embed=discord.Embed(title="Support", description="Are you sure you want to open a ticket?", colour=6702), view=view, ephemeral=True, delete_after=15.0)
                else:
                    await interaction.response.send_message(embed=discord.Embed(title=f"Go to the {sup_channel.mention} channel to get help.", description="This message will be automatically deleted soon...", colour=6702), ephemeral=True, delete_after=8.0)
                    await interaction.original_response()
        
        
    @app_commands.command(name="close_ticket", description="For support members only")
    async def close_ticket(self, interaction: discord.Interaction):
        guild = interaction.guild
        all_roles = guild.roles
        sup_role = discord.utils.get(all_roles, name="Support")
        user = interaction.user
        view = CloseTicketButtons()
        user_sup_role = user.get_role(sup_role.id)

        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM sup_setup")
            for data in await cursor.fetchall():
                if data[0] == interaction.guild.id:
                    sup_role = discord.utils.get(all_roles, name=data[3])
                    
        if user_sup_role:
            await interaction.response.send_message(embed=discord.Embed(title="Close ticket?", description="This channel will be deleted. Continue?", colour=6702), view=view, ephemeral=True, delete_after=10.0)
        else:
            await interaction.response.send_message("❌ You do not have permission for this command.\n\nThis message will be automatically deleted soon...", ephemeral=True, delete_after=8.0)
             
                
    @app_commands.command(name="auto_vc_control_help", description="Help for Auto-Voice-Channel-Control")
    @app_commands.checks.has_permissions(administrator=True)
    async def auto_vc_control_help(self, interaction: discord.Interaction):
        await interaction.response.send_message(embed=discord.Embed(title="Auto-Voice-Channel-Control Help", description="The bot automatically creates a new voice channel when a user joins a voice channel. This ensures that a voice channel is always available. It will also be deleted when the last user leaves the channel. Channels are named starting with Talk0.", colour=6702))


    @app_commands.command(name="auto_vc_control", description="Enable or disable Auto-Voice-Channel-Control")
    @app_commands.checks.has_permissions(administrator=True)
    async def auto_vc_control(self, interaction: discord.Interaction):
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT active FROM auto_vc_control WHERE guild_id=?", (interaction.guild.id,))
            result = await cursor.fetchone()
            if result is None:
                await cursor.execute("INSERT INTO auto_vc_control (guild_id, active) VALUES (?, ?)", (interaction.guild.id, 1))
                await conn.commit()
                await interaction.response.send_message(embed=discord.Embed(title="Auto-Voice-Channel-Control enabled!", colour=6702), ephemeral=True, delete_after=8.0)
                return
            else:
                if result[0] == 1:
                    await cursor.execute("UPDATE auto_vc_control SET active=? WHERE guild_id=?", (0, interaction.guild.id))
                    await conn.commit()
                    await interaction.response.send_message(embed=discord.Embed(title="Auto-Voice-Channel-Control disabled!", colour=6702), ephemeral=True, delete_after=8.0)
                else:
                    await cursor.execute("UPDATE auto_vc_control SET active=? WHERE guild_id=?", (1, interaction.guild.id))
                    await conn.commit()
                    await interaction.response.send_message(embed=discord.Embed(title="Auto-Voice-Channel-Control enabled!", colour=6702), ephemeral=True, delete_after=8.0)
        
        
    @app_commands.command(name="blacklist", description="Shows the complete blacklist")
    async def blacklist(self, interaction: discord.Interaction):
        all_words = ""
        
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM blacklist")
            for data in await cursor.fetchall():
                if data[0] == interaction.guild.id:
                    all_words += f"{data[1]}\n"
            await interaction.response.send_message(embed=discord.Embed(title="All blocked words:", description=all_words, colour=6702), delete_after=15.0)
        
        
    @app_commands.command(name="blacklist_add", description="Add a word to the blacklist")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklist_add(self, interaction: discord.Interaction, word: str):
        await interaction.response.defer(ephemeral=True)
        
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM blacklist")
            word_found = False
            for data in await cursor.fetchall():
                if data[1] == word:
                    await interaction.followup.send("This word is already on the blacklist.")
                    word_found = True
                    break
            if not word_found:
                await cursor.execute("INSERT INTO blacklist VALUES (?,?)", (interaction.guild.id, word))
                await conn.commit()
                await interaction.followup.send(f"{word} has been added to the blacklist!", ephemeral=True)
                    
                    
    @app_commands.command(name="blacklist_remove", description="Remove a word from the blacklist")
    @app_commands.checks.has_permissions(administrator=True)
    async def blacklist_remove(self, interaction: discord.Interaction, word: str):
        await interaction.response.defer(ephemeral=True)
        
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT * FROM blacklist")
            for data in await cursor.fetchall():
                if data[0] == interaction.guild.id:
                    await cursor.execute("DELETE FROM blacklist WHERE word=? AND guild_id=?", (word, interaction.guild.id))
                    await conn.commit()
            await interaction.followup.send(f"{word} has been removed from the blacklist!", ephemeral=True)


    @app_commands.command(name="violation_limit_help", description="Explains what the violation_limit command does.")
    async def violation_limit_help(self, interaction: discord.Interaction):
        text = (
            "The /violation_limit command allows server administrators to set how many violations a user can have before being kicked. "
            "By default, the limit is 3. When a user sends a blacklisted word, it counts as a violation. "
            "If a user reaches the set limit, they will be kicked from the server. Warnings are sent for each violation before the limit is reached. "
            "Use /violation_limit <amount> to set a new limit for your server."
        )
        
        await interaction.response.send_message(embed=discord.Embed(title="Violation Limit Help", description=text, colour=6702))


    @app_commands.command(name="violation_limit", description="Set the violation limit for your server.")
    @app_commands.checks.has_permissions(administrator=True)
    async def violation_limit(self, interaction: discord.Interaction, amount: int):
        if amount < 1:
            await interaction.response.send_message("The violation limit must be at least 1.", ephemeral=True)
            return
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("INSERT OR REPLACE INTO violation_limit (guild_id, amount) VALUES (?, ?)", (interaction.guild.id, amount))
            await conn.commit()
        await interaction.response.send_message(f"Violation limit set to {amount} for this server.", ephemeral=True)   
        
                 
    @app_commands.command(name="coinflip", description="Heads or tails")
    async def coinflip(self, interaction: discord.Interaction):
        coin = random.choice(["Heads", "Tails"])
        coin = f"You flipped {coin}."
        await interaction.response.send_message(embed=discord.Embed(title=coin, colour=6702))


    @app_commands.command(name="to_do", description="Set a reminder in x minutes")
    async def to_do(self, interaction: discord.Interaction, todo: str, timer: int):
        timer *= 60
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(embed=discord.Embed(title="Reminder set!", description=f"You will be reminded in {timer//60} minute(s) about:\n{todo}", colour=6702))
        
        while timer > 0:
            await asyncio.sleep(1)
            timer -= 1
            
        await interaction.user.send(embed=discord.Embed(title="Reminder!", description=todo, colour=6702))
        
    @app_commands.command(name="tictactoe", description="The game TicTacToe")
    async def tictactoe(self, interaction: discord.Interaction):
        view = ChooseTicTacToeEnemy()
        await interaction.response.send_message(embed=discord.Embed(title="Against player or computer?", colour=6702), view=view, delete_after=8.0)
        sent_msg = await interaction.original_response()
        await set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "bot")
        
        
    @app_commands.command(name="hangman_vs_player", description="The game Hangman vs Player")
    async def hangman_player(self, interaction: discord.Interaction, word: str):
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT active FROM hangman WHERE user_id=?", (interaction.user.id,))
            row = await cursor.fetchone()
            if row and row[0] == 1:
                await deactivate_hangman(interaction.user.id)
            await cursor.execute("DELETE FROM hangman WHERE user_id=?", (interaction.user.id,))
            await conn.commit()
            await cursor.execute("INSERT INTO hangman (user_id, opponent_id, word, hg_word, failed_attempts, disabled_buttons, active) VALUES (?, ?, ?, ?, ?, ?, ?)", (interaction.user.id, None, word, "", 0, "", 1))
            await conn.commit()

        view = HangmanPlayerReady(interaction.user.id, word)
        await interaction.response.send_message(embed=discord.Embed(title=f"Waiting for an opponent! The first to click 'Ready' will play against {interaction.user}.", colour=6702), view=view)
        sent_msg = await interaction.original_response()
        await set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "bot")
        await set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "hangman")
        
        
    @app_commands.command(name="hangman_vs_computer", description="The game Hangman vs Computer")
    async def hangman_computer(self, interaction: discord.Interaction):
        async with aiofiles.open("json/hg_words.json", "r", encoding="UTF-8") as file:
            content = await file.read()
            data = json.loads(content)
            hg_words = data["words"]
            num = random.randint(0,100)
            word = hg_words[num]
                
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT active FROM hangman WHERE user_id=?", (interaction.user.id,))
            row = await cursor.fetchone()
            if row and row[0] == 1:
                await deactivate_hangman(interaction.user.id)
            await cursor.execute("DELETE FROM hangman WHERE user_id=?", (interaction.user.id,))
            await conn.commit()
            await cursor.execute("INSERT INTO hangman (user_id, opponent_id, word, hg_word, failed_attempts, disabled_buttons, active) VALUES (?, ?, ?, ?, ?, ?, ?)", (interaction.user.id, None, word, "", 0, "", 1))
            await conn.commit()
        view = HangmanComputerReady(interaction.user.id, word)
        await interaction.response.send_message(embed=discord.Embed(title="Start game?", description="Press **Ready** to start!", colour=6702), view=view)
        sent_msg = await interaction.original_response()
        await set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "bot")
        await set_bot_message(interaction.user.id, sent_msg.channel.id, sent_msg.id, "hangman")
        
        
    @app_commands.command(name="quiz", description="A quiz game")
    async def quiz(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        async with aiofiles.open("json/quiz.json", "r", encoding="UTF-8") as file:
            content = await file.read()
            data = json.loads(content)
            num = random.randint(1,1000)
            data = data[num]
            question = data["frage"]
            answer_choices = data["antwortmöglichkeiten"]
            answer = data["lösung"]
            difficulty = data["schwierigkeit"]
            view = Quiz(user_id, question, answer_choices, answer, difficulty)
            await interaction.response.send_message(embed=discord.Embed(title="Question: "+ question, description="Answer choices:", colour=6702), view=view)
            
    
    @app_commands.command(name="quiz_points", description="Shows the quiz points")
    async def quiz_points(self, interaction: discord.Interaction):       
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT points FROM quiz_points WHERE guild_id=? AND user_id=?", (interaction.guild.id, interaction.user.id))
            points = await cursor.fetchone()
            if points:
                points = points[0]
            else:
                points = None
        
        if points is not None:
            await interaction.response.send_message(embed=discord.Embed(title=f"You have {points} quiz points!", colour=6702))
        else:
            await interaction.response.send_message(embed=discord.Embed(title="You do not have any quiz points yet.", colour=6702), ephemeral=True)
            
    
    @app_commands.command(name="quiz_leaderboard", description="Shows the quiz leaderboard")
    async def quiz_leaderboard(self, interaction: discord.Interaction):
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT user_id, points FROM quiz_points WHERE guild_id=? ORDER BY points DESC LIMIT 10", (interaction.guild.id,))
            leaderboard = await cursor.fetchall()
        
        if not leaderboard:
            await interaction.response.send_message(embed=discord.Embed(title="There are no quiz points yet.", colour=6702), ephemeral=True)
            return
        
        leaderboard_text = ""
        
        for idx, (user_id, points) in enumerate(leaderboard, start=1):
            user = await interaction.guild.fetch_member(user_id)
            if user.name in leaderboard_text:
                continue
            leaderboard_text += f"{idx}. {user.name}: {points} points\n"
        await interaction.response.send_message(embed=discord.Embed(title="Quiz Leaderboard:", description=leaderboard_text, colour=6702))
        
    
    @app_commands.command(name="gamble_quiz_points", description="Gamble your quiz points")
    async def gamble_quiz_points(self, interaction: discord.Interaction, points: int):
        async with aiosqlite.connect("database.db") as conn:
            cursor = await conn.cursor()
            await cursor.execute("SELECT points FROM quiz_points WHERE guild_id=? AND user_id=?", (interaction.guild.id, interaction.user.id))
            current_points = await cursor.fetchone()
            if not current_points or current_points[0] < points:
                await interaction.response.send_message(embed=discord.Embed(title="You do not have enough quiz points to gamble.", colour=6702), ephemeral=True)
                return
            gamble_result = random.choice(["win", "lose"])
            if gamble_result == "win":
                new_points = current_points[0] + points
                await cursor.execute("UPDATE quiz_points SET points=? WHERE guild_id=? AND user_id=?", (new_points, interaction.guild.id, interaction.user.id))
                await conn.commit()
                await interaction.response.send_message(embed=discord.Embed(title=f"You won! You now have {new_points} quiz points.", colour=6702))
            else:
                new_points = current_points[0] - points
                await cursor.execute("UPDATE quiz_points SET points=? WHERE guild_id=? AND user_id=?", (new_points, interaction.guild.id, interaction.user.id))
                await conn.commit()
                await interaction.response.send_message(embed=discord.Embed(title=f"You lost! You now have {new_points} quiz points.", colour=6702))