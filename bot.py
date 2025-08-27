import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from keep_alive import keep_alive

# Load environment variables
load_dotenv()
TOKEN = os.getenv("TOKEN")
SUPPORT_ROLE_ID = os.getenv("SUPPORT_ROLE_ID")

# Bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} commands")
    except Exception as e:
        print(e)

# ---- Ticket View ----
class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Create a Ticket", style=discord.ButtonStyle.primary, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        user = interaction.user

        existing = discord.utils.get(guild.text_channels, name=f"ticket-{user.id}")
        if existing:
            await interaction.response.send_message("❗ You already have a ticket open.", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            guild.get_role(int(SUPPORT_ROLE_ID)): discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(f"ticket-{user.id}", overwrites=overwrites)
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

        await channel.send(f"👋 Hello {user.mention}! Please fill out the details of your Power Leveling order.")
        await channel.send(view=OrderView(user.id))

# ---- Order Modal ----
class OrderModal(discord.ui.Modal, title="Power Leveling Order"):
    level_range = discord.ui.TextInput(label="Level Range", placeholder="e.g., 1-200", required=True)
    characters = discord.ui.TextInput(label="Number of Characters", placeholder="e.g., 1", required=True)
    bonus = discord.ui.TextInput(label="Bonus (optional)", placeholder="e.g., Wisdom Set", required=False)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❗ Only the ticket owner can submit this form.", ephemeral=True)
            return

        embed = discord.Embed(title="✅ Order Confirmation", color=0x2ecc71)
        embed.add_field(name="Level Range", value=self.level_range.value, inline=False)
        embed.add_field(name="Number of Characters", value=self.characters.value, inline=False)
        embed.add_field(name="Bonus", value=self.bonus.value if self.bonus.value else "None", inline=False)

        await interaction.response.send_message("📦 Your order has been recorded:", embed=embed, view=CloseTicketView())

# ---- Order View ----
class OrderView(discord.ui.View):
    def __init__(self, user_id):
        super().__init__(timeout=None)
        self.user_id = user_id

    @discord.ui.button(label="📝 Fill Order Details", style=discord.ButtonStyle.success)
    async def open_modal(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(OrderModal(self.user_id))

# ---- Close Ticket ----
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="❌ Close Ticket", style=discord.ButtonStyle.danger)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Are you sure you want to close this ticket?", view=ConfirmCloseView(), ephemeral=True)

class ConfirmCloseView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="✅ Yes, close it", style=discord.ButtonStyle.danger)
    async def confirm_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.delete()

    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_close(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("❎ Ticket close canceled.", ephemeral=True)

# ---- Slash Command to Send Ticket Message ----
@bot.tree.command(name="sendticket", description="Send the ticket creation message")
async def sendticket(interaction: discord.Interaction):
    await interaction.response.send_message(
        "📩 **Welcome!**\nClick the button below to create a ticket and order your PL service.",
        view=TicketView()
    )

# Keep alive server
keep_alive()
bot.run(TOKEN)
