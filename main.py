import discord
from discord.ext import commands
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
        await ctx.send("Channel not found.")
        return

    # Check if the command was a reply to a message with attachments
    if ctx.message.reference:
        replied_message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        attachments = replied_message.attachments
    else:
        attachments = ctx.message.attachments

    await send_attachments(channel, attachments)

    await ctx.send(f"Media 📺 saved 😋 successfully.")

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

    async def send_page(page):
        msg = await ctx.send(embed=embeds[page])
        await msg.add_reaction("◀️")
        await msg.add_reaction("▶️")
        await msg.add_reaction("✅")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["◀️", "▶️", "✅"]

        while True:
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
                if str(reaction.emoji) == "◀️":
                    if page > 0:
                        page -= 1
                        await msg.edit(embed=embeds[page])
                elif str(reaction.emoji) == "▶️":
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
        await msg.delete()  # Delete the embed message after interaction is complete

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
        if len(current_page) < 8:
            current_page.append(channel)
        if len(current_page) == 8 or idx == len(text_channels):
            pages.append(current_page)
            current_page = []

    current_page_index = 0

    async def send_page(page):
        embed = discord.Embed(title=f"Category Page {page+1}/{len(pages)}")
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
                    await msg.delete()  # Delete the current page message
                    break
                elif str(reaction.emoji) == "➡️" and page < len(pages) - 1:
                    await send_page(page + 1)
                    await msg.delete()  # Delete the current page message
                    break
                await msg.remove_reaction(reaction, user)
            except:
                break
        await msg.delete()  # Delete the embed message after interaction is complete

    await send_page(current_page_index)


# Dictionary to keep track of user channels in the target server
user_channels = {}

# IDs
source_server_id = 1248192277428310016  # Replace with your source server ID
target_server_id = 1250835568644853760  # Replace with your target server ID
source_channel_id = 1250850424202985512  # Replace with your source channel ID

@bot.command()
async def tm(ctx):
    if ctx.guild.id != source_server_id:
        await ctx.send("This command can only be used in the source server.")
        return

    source_channel = bot.get_channel(source_channel_id)
    target_server = bot.get_guild(target_server_id)

    if source_channel is None or target_server is None:
        await ctx.send("Source channel or target server not found.")
        return

    async for message in source_channel.history(limit=None):
        # Check if the message contains media
        if message.attachments:
            sender_name = message.author.name

            # Create or get the channel for the user
            if sender_name not in user_channels:
                channel = await target_server.create_text_channel(sender_name)
                user_channels[sender_name] = channel.id
            else:
                channel_id = user_channels[sender_name]
                channel = bot.get_channel(channel_id)

            # Repost the media in the user's channel
            for attachment in message.attachments:
                await channel.send(file=await attachment.to_file())

    await ctx.send("Media transfer complete.")

@bot.event
async def on_message(message):
    # Ignore messages from bots
    if message.author.bot:
        return

    # Check if the message is in the source channel
    if message.guild.id == source_server_id and message.channel.id == source_channel_id:
        # Check if the message contains media
        if message.attachments:
            # Get the target server and the name of the sender
            target_server = bot.get_guild(target_server_id)
            sender_name = message.author.name

            # Create or get the channel for the user
            if sender_name not in user_channels:
                channel = await target_server.create_text_channel(sender_name)
                user_channels[sender_name] = channel.id
            else:
                channel_id = user_channels[sender_name]
                channel = bot.get_channel(channel_id)

            # Repost the media in the user's channel
            for attachment in message.attachments:
                await channel.send(file=await attachment.to_file())

    # Process commands if any
    await bot.process_commands(message)
keep_alive()
bot.run(os.environ['Token'])
