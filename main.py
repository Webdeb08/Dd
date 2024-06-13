import discord
from discord.ext import commands
from discord.ui import Button, View
import os
import aiohttp
import io
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents)

guild_id = 1250740008588017765  # Replace with your specific guild ID
category_name_base = "Media"
max_channels_per_category = 50  # Discord's limit

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

async def send_attachments(channel, attachments):
    async with aiohttp.ClientSession() as session:
        for attachment in attachments:
            async with session.get(attachment.url) as response:
                if response.status == 200:
                    data = await response.read()
                    file = discord.File(io.BytesIO(data), filename=attachment.filename)
                    await channel.send(file=file)

@bot.command()
async def add(ctx, *, channel_name):
    guild = bot.get_guild(guild_id)
    if guild is None:
        await ctx.send("Guild not found.")
        return

    # Find or create a category to host the new channel
    existing_categories = [category for category in guild.categories if category.name.startswith(category_name_base)]
    category = next((cat for cat in existing_categories if len(cat.channels) < max_channels_per_category), None)

    if category is None:
        category_count = len(existing_categories) + 1
        category = await guild.create_category(f"{category_name_base} {category_count}")

    # Create the new text channel in the selected category
    new_channel = await category.create_text_channel(channel_name)

    # Check if the command was a reply to a message with attachments
    if ctx.message.reference:
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        attachments = replied_message.attachments
    else:
        attachments = ctx.message.attachments

    await send_attachments(new_channel, attachments)

    await ctx.send(f"Media 📺 saved 😋 successfully.")

@bot.command()
async def addto(ctx, channel_id: int):
    guild = bot.get_guild(guild_id)
    if guild is None:
        await ctx.send("Guild not found.")
        return

    channel = guild.get_channel(channel_id)
    if channel is None:
        await ctx.send("Media id not found.")
        return

    # Check if the command was a reply to a message with attachments
    if ctx.message.reference:
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        attachments = replied_message.attachments
    else:
        attachments = ctx.message.attachments

    await send_attachments(channel, attachments)

    await ctx.send(f"Media 📺 saved 😋 successfully.")

class ChannelButton(Button):
    def __init__(self, label, channel_id):
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        channel = bot.get_channel(self.channel_id)
        async for message in channel.history(limit=None):
            for attachment in message.attachments:
                await interaction.response.send_message(attachment.url)
        await interaction.message.delete()

class CopyIDButton(Button):
    def __init__(self, label, channel_id):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.channel_id = channel_id

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Copied ID: {self.channel_id}", ephemeral=True)

@bot.command()
async def search(ctx, *, search_term):
    guild = bot.get_guild(guild_id)
    if guild is None:
        await ctx.send("Guild not found.")
        return

    matched_channels = [channel for channel in guild.text_channels if search_term.lower() in channel.name.lower()]

    if not matched_channels:
        await ctx.send("No media found.")
        return

    embeds = []
    views = []

    for channel in matched_channels:
        embed = discord.Embed(title="Media Found", description=channel.name)
        embed.set_footer(text=f"Media ID: {channel.id}")
        embeds.append(embed)

        view = View()
        view.add_item(ChannelButton(label="Show Media", channel_id=channel.id))
        view.add_item(CopyIDButton(label="Copy ID", channel_id=channel.id))
        views.append(view)

    current_page = 0

    async def send_page(page):
        msg = await ctx.send(embed=embeds[page], view=views[page])

    await send_page(current_page)

class ShowPageView(View):
    def __init__(self, pages, author):
        super().__init__()
        self.pages = pages
        self.author = author
        self.current_page_index = 0
        self.update_buttons()

    def update_buttons(self):
        for i in range(10):
            if i < len(self.pages[self.current_page_index]):
                self.add_item(ChannelButton(label=f"{i + 1}", channel_id=self.pages[self.current_page_index][i].id))
            else:
                break

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def previous_page(self, button: Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            if self.current_page_index > 0:
                self.current_page_index -= 1
                self.update_buttons()
                await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.send_message("You cannot interact with this button.", ephemeral=True)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_page(self, button: Button, interaction: discord.Interaction):
        if interaction.user == self.author:
            if self.current_page_index < len(self.pages) - 1:
                self.current_page_index += 1
                self.update_buttons()
                await interaction.response.edit_message(embed=self.create_embed(), view=self)
        else:
            await interaction.response.send_message("You cannot interact with this button.", ephemeral=True)

    def create_embed(self):
        embed = discord.Embed(title=f"Category Page {self.current_page_index + 1}/{len(self.pages)}")
        for i, channel in enumerate(self.pages[self.current_page_index], start=1):
            embed.add_field(name=f"{i}.", value=channel.name, inline=False)
        return embed

@bot.command()
async def show(ctx):
    guild = bot.get_guild(guild_id)
    if guild is None:
        await ctx.send("Guild not found.")
        return

    text_channels = guild.text_channels

    if not text_channels:
        await ctx.send("No media found.")
        return

    pages = []
    current_page = []

    for idx, channel in enumerate(text_channels, start=1):
        if len(current_page) < 10:
            current_page.append(channel)
        if len(current_page) == 10 or idx == len(text_channels):
            pages.append(current_page)
            current_page = []

    view = ShowPageView(pages, ctx.author)
    embed = view.create_embed()
    await ctx.send(embed=embed, view=view)

keep_alive()
bot.run(os.environ['Token'])
