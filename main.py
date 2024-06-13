import discord
from discord.ext import commands
from discord_components import DiscordComponents, Button, ButtonStyle
import os
import aiohttp
import io
from keep_alive import keep_alive
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents)
DiscordComponents(bot)

guild_id = 1250740008588017765  # Replace with your specific guild ID
category_name_base = "Media Category"
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
async def search(ctx, *, search_term):
    guild = bot.get_guild(guild_id)
    if guild is None:
        await ctx.send("Guild not found.")
        return

    matched_channels = [channel for channel in guild.text_channels if search_term.lower() in channel.name.lower()]

    if not matched_channels:
        await ctx.send("No match found.")
        return

    embeds = []
    for channel in matched_channels:
        embed = discord.Embed(title="Media Found", description=channel.name)
        embed.set_footer(text=f"Media ID: {channel.id}")
        embeds.append(embed)

    current_page = 0

    async def send_page(page):
        embed = embeds[page]
        msg = await ctx.send(embed=embed, components=[[Button(style=ButtonStyle.green, label="⬅️"), Button(style=ButtonStyle.green, label="➡️"), Button(style=ButtonStyle.green, label="✅")]])

        while True:
            try:
                interaction = await bot.wait_for("button_click", timeout=60.0)
                if interaction.author == ctx.author:
                    if interaction.component.label == "⬅️":
                        if page > 0:
                            page -= 1
                            embed = embeds[page]
                            await interaction.respond(embed=embed)
                    elif interaction.component.label == "➡️":
                        if page < len(embeds) - 1:
                            page += 1
                            embed = embeds[page]
                            await interaction.respond(embed=embed)
                    elif interaction.component.label == "✅":
                        selected_channel = matched_channels[page]
                        async for message in selected_channel.history(limit=None):
                            for attachment in message.attachments:
                                await ctx.send(attachment.url)
                        break
            except asyncio.TimeoutError:
                await msg.edit(components=[])

    await send_page(current_page)

@bot.command()
async def show(ctx):
    # Define the server IDs from which you want to display channels
    server_ids = [1250835568644853760,1250740008588017765]  # Add more server IDs if needed
    
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
        if len(current_page) < 10:
            current_page.append(channel)
        if len(current_page) == 10 or idx == len(text_channels):
            pages.append(current_page)
            current_page = []

    current_page_index = 0

    
        

    async def send_page(page):
        embed = discord.Embed(title=f"Channels Page {page+1}/{len(pages)}")
        for i, channel in enumerate(pages[page], start=1):
            embed.add_field(name=f"{i}.", value=channel.name, inline=False)
        msg = await ctx.send(embed=embed, components=[[Button(style=ButtonStyle.green, label=f"{i+1}️⃣") for i in range(len(pages[page]))]])
        
        if page > 0:
            await msg.add_reaction("⬅️")
        if page < len(pages) - 1:
            await msg.add_reaction("➡️")

        while True:
            try:
                interaction = await bot.wait_for("button_click", timeout=60.0)
                if interaction.author == ctx.author:
                    if interaction.component.label.startswith("⬅️") and page > 0:
                        await send_page(page - 1)
                        break
                    elif interaction.component.label.startswith("➡️") and page < len(pages) - 1:
                        await send_page(page + 1)
                        break
                    elif interaction.component.label.startswith("✅"):
                        selected_index = int(interaction.component.label[0]) - 1
                        selected_channel = pages[page][selected_index]
                        async for message in selected_channel.history(limit=None):
                            for attachment in message.attachments:
                                await ctx.send(attachment.url)
                        break
            except asyncio.TimeoutError:
                await msg.edit(components=[])

    await send_page(current_page_index)
keep_alive()
bot.run(os.environ['Token'])
