import discord
from discord.ext import commands
import os
import aiohttp
import io
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents)

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

    await ctx.send(f"Media saved 😋")

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
        msg = await ctx.send(embed=embeds[page])
        await msg.add_reaction("⬅️")
        await msg.add_reaction("➡️")
        await msg.add_reaction("✅")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["⬅️", "➡️", "✅"]

        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
                if str(reaction.emoji) == "⬅️":
                    if page > 0:
                        page -= 1
                        await msg.edit(embed=embeds[page])
                elif str(reaction.emoji) == "➡️":
                    if page < len(embeds) - 1:
                        page += 1
                        await msg.edit(embed=embeds[page])
                elif str(reaction.emoji) == "✅":
                    selected_channel = matched_channels[page]
                    async for message in selected_channel.history(limit=None):
                        for attachment in message.attachments:
                            await ctx.send(attachment.url)
                    break
                await msg.remove_reaction(reaction, user)
            except:
                break

    await send_page(current_page)

@bot.command()
async def show(ctx):
    guild = bot.get_guild(guild_id)
    if guild is None:
        await ctx.send("Guild not found.")
        return

    text_channels = guild.text_channels

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
        msg = await ctx.send(embed=embed)
        for i in range(1, len(pages[page]) + 1):
            await msg.add_reaction(f"{i}️⃣")
        if page > 0:
            await msg.add_reaction("⬅️")
        if page < len(pages) - 1:
            await msg.add_reaction("➡️")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in [f"{i}️⃣" for i in range(1, len(pages[page]) + 1)] + ["⬅️", "➡️"]

        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
                if str(reaction.emoji) in [f"{i}️⃣" for i in range(1, len(pages[page]) + 1)]:
                    selected_index = [f"{i}️⃣" for i in range(1, len(pages[page]) + 1)].index(str(reaction.emoji))
                    selected_channel = pages[page][selected_index]
                    async for message in selected_channel.history(limit=None):
                        for attachment in message.attachments:
                            await ctx.send(attachment.url)
                    break
                elif str(reaction.emoji) == "⬅️" and page > 0:
                    await send_page(page - 1)
                    break
                elif str(reaction.emoji) == "➡️" and page < len(pages) - 1:
                    await send_page(page + 1)
                    break
                await msg.remove_reaction(reaction, user)
            except:
                break

    await send_page(current_page_index)

bot.run(os.environ['Token'])
