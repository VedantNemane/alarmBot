# Thanks to <a href="https://www.flaticon.com/free-icons/time" title="time icons">Time icons created by Freepik - Flaticon</a> for the hourglass icon
import os

import discord
import re
from discord.ext import commands
from dotenv import load_dotenv

from datetime import datetime
import pytz

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

@bot.command()
async def alarm(ctx, command = None, time = None):
    if (command == time == None):
        await ctx.send("@everyone")
    else:    
        # Take time in 00:00 format
        if (command.lower() == "set"):
            valid_time_found = re.search("^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", time)
            if (valid_time_found != None):
                alarm_time_to_set = valid_time_found.group(0) if len(valid_time_found.group(0)) == 5 else "0"+valid_time_found.group(0)
                await ctx.send(f"I want to set an alarm at {alarm_time_to_set}")
            else:
                await sendError(ctx, 400, "Invalid time format. Please use the following format: \"/alarm set HH:MM\"")

@bot.command()
async def sendError(ctx, errorCode: int, errorMessage: str):
    await ctx.send(f"Error [{errorCode}]: {errorMessage}")

@bot.command()
async def timezone(ctx):
    local = datetime.now()
    await ctx.send(str(local))

bot.run(TOKEN)