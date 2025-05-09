import discord

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
        await interaction.response.send_message("Du bist nun verifiziert!\n\nDiese Nachricht wird in kürze automatisch gelöscht...", ephemeral=True, delete_after=8.0)
        
        
    @discord.ui.button(style=discord.ButtonStyle.red, label="Deny", disabled=False)
    async def Deny(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Du musst akzeptieren oder du wirst gekickt.\n\nDiese Nachricht wird in kürze automatisch gelöscht...", ephemeral=True, delete_after=8.0)
        

class SupportButtons(discord.ui.View):
    def __init__(self, *, timeout=None):
        super().__init__(timeout=timeout)


    @discord.ui.button(style=discord.ButtonStyle.grey, label="support", disabled=False)
    async def support(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        channel = await guild.create_text_channel(name=f"support für {interaction.user}")
    
    
    @discord.ui.button(style=discord.ButtonStyle.green, label="Open", disabled=False)
    async def open(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass 


    @discord.ui.button(style=discord.ButtonStyle.red, label="Close", disabled=False)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass 
    