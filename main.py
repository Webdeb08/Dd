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

    await ctx.send("Media 📺 saved 😋 successfully.")

@bot.command()
async def addto(ctx, channel_id: int):
    guild = bot.get_guild(guild_id)
    if guild is None:
        await ctx.send("Guild not found.")
        return

    channel = guild.get_channel(channel_id)
    if channel is None:
        await ctx.send("Channel not found.")
        return

    # Check if the command was a reply to a message with attachments
    if ctx.message.reference:
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        attachments = replied_message.attachments
    else:
        attachments = ctx.message.attachments

    await send_attachments(channel, attachments)

    await ctx.send("Media 📺 saved 😋 successfully.")

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
    for channel in matched_channels:
        embed = discord.Embed(title="𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚 𝐦𝐬𝐠 𝐰𝐢𝐭𝐡 .𝐚𝐝𝐝𝐭𝐨 <𝐢𝐝> 𝐭𝐨 𝐚𝐝𝐝 𝐦𝐨𝐫𝐞 𝐜𝐨𝐧𝐭𝐞𝐧𝐭 𝐭𝐨 𝐭𝐡𝐢𝐬 𝐜𝐚𝐭𝐞𝐠𝐨𝐫𝐲", description=channel.name)
        embed.set_footer(text=f".addto {channel.id}")
        embeds.append(embed)

    current_page = 0

    class SearchView(View):
        def __init__(self, embeds, matched_channels, ctx):
            super().__init__()
            self.embeds = embeds
            self.current_page = 0
            self.matched_channels = matched_channels
            self.ctx = ctx

        async def update_message(self, interaction):
            await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
        async def previous(self, interaction: discord.Interaction, button: Button):
            if self.current_page > 0:
                self.current_page -= 1
                await self.update_message(interaction)
            else:
                await interaction.response.send_message("No pages left.", ephemeral=True)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
        async def next(self, interaction: discord.Interaction, button: Button):
            if self.current_page < len(self.embeds) - 1:
                self.current_page += 1
                await self.update_message(interaction)
            else:
                await interaction.response.send_message("No pages left.", ephemeral=True)

        @discord.ui.button(label="Select", style=discord.ButtonStyle.success)
        async def select(self, interaction: discord.Interaction, button: Button):
            selected_channel = self.matched_channels[self.current_page]
            async for message in selected_channel.history(limit=None):
                for attachment in message.attachments:
                    await self.ctx.send(attachment.url)
            await interaction.message.delete()

    view = SearchView(embeds, matched_channels, ctx)
    await ctx.send(embed=embeds[current_page], view=view)

@bot.command()
async def show(ctx):
    server_ids = [1250740008588017765]  # Add more server IDs if needed

    guild = bot.get_guild(guild_id)
    if guild is None:
        await ctx.send("Guild not found.")
        return

    text_channels = []
    for server_id in server_ids:
        server = bot.get_guild(server_id)
        if server:
            text_channels.extend(server.text_channels)

    if not text_channels:
        await ctx.send("No channels found.")
        return

    pages = []
    current_page = []

    for idx, channel in enumerate(text_channels, start=1):
        if len(current_page) < 8:
            current_page.append(channel)
        if len(current_page) == 8 or idx == len(text_channels):
            pages.append(current_page)
            current_page = []

    current_page_index = 0

    class ShowView(View):
        def __init__(self, pages, ctx):
            super().__init__()
            self.pages = pages
            self.current_page = 0
            self.ctx = ctx

            for i in range(8):
                button = Button(label=str(i + 1), style=discord.ButtonStyle.primary)
                button.callback = self.create_callback(i)
                self.add_item(button)

            if len(self.pages) > 1:
                previous_button = Button(label="Previous", style=discord.ButtonStyle.primary)
                previous_button.callback = self.previous
                self.add_item(previous_button)

                next_button = Button(label="Next", style=discord.ButtonStyle.primary)
                next_button.callback = self.next
                self.add_item(next_button)

        def create_callback(self, index):
            async def callback(interaction: discord.Interaction):
                if index < len(self.pages[self.current_page]):
                    selected_channel = self.pages[self.current_page][index]
                    async for message in selected_channel.history(limit=None):
                        for attachment in message.attachments:
                            await interaction.message.delete()
                            await self.ctx.send(attachment.url)

            return callback

        async def previous(self, interaction: discord.Interaction):
            if self.current_page > 0:
                self.current_page -= 1
                await self.update_message(interaction)
            else:
                await interaction.response.send_message("No pages left.", ephemeral=True)

        async def next(self, interaction: discord.Interaction):
            if self.current_page < len(self.pages) - 1:
                self.current_page += 1
                await self.update_message(interaction)
            else:
                await interaction.response.send_message("No pages left.", ephemeral=True)

        async def update_message(self, interaction):
            embed = discord.Embed(title=f"Channels Page {self.current_page + 1}/{len(self.pages)}")
            for i, channel in enumerate(self.pages[self.current_page], start=1):
                embed.add_field(name=f"{i}.", value=channel.name, inline=False)
            await interaction.response.edit_message(embed=embed, view=self)

    view = ShowView(pages, ctx)
    embed = discord.Embed(title=f"Channels Page {current_page_index + 1}/{len(pages)}")
    for i, channel in enumerate(pages[current_page_index], start=1):
        embed.add_field(name=f"{i}.", value=channel.name, inline=False)
    await ctx.send(embed=embed, view=view)

@bot.command()
async def s(ctx, source_channel_id: int, target_channel_id: int):
    source_channel = bot.get_channel(source_channel_id)
    target_channel = bot.get_channel(target_channel_id)

    if source_channel is None or target_channel is None:
        await ctx.send("Lagawele choliya ke hook raja ji")
        return

    async for message in source_channel.history(limit=None):
        for attachment in message.attachments:
            if attachment.url.lower().endswith(('jpg', 'jpeg', 'png', 'gif', 'mp4', 'mov', 'webm')):
                await target_channel.send(content=attachment.url)

    await ctx.send("Media transfer complete!")

keep_alive()
bot.run(os.environ['Token'])
