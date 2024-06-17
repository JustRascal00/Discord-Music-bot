import discord
from discord.ext import commands
import asyncio
import os
from config import BOT_TOKEN
from controls import PlaybackControls
from music import YTDLSource, play_next
from commands import setup_commands

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

setup_commands(bot)

bot.run(BOT_TOKEN)
