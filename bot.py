# Thanks to <a href="https://www.flaticon.com/free-icons/time" title="time icons">Time icons created by Freepik - Flaticon</a> for the hourglass icon
import os

import discord
import re
import asyncio
import pytz

from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)

user_time_offset_from_utc = 0
switched_on = True
alarm_running = False
task = None
seconds = None

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

async def ping_everyone(ctx):
    global switched_on 
    global alarm_running
    if (switched_on):
        alarm_running = False
        await ctx.send("@everyone")

async def sendError(ctx, errorCode: int, errorMessage: str):
    await ctx.send(f"Error [{errorCode}]: {errorMessage}")

async def setAlarm(ctx, seconds_to_sleep):
    global alarm_running
    global task
    global seconds

    seconds = seconds_to_sleep

    await countdown(ctx)
    print(f"Setting alarm for {seconds_to_sleep} seconds.")
    alarm_running = True
    task = asyncio.ensure_future(asyncio.sleep(seconds_to_sleep))
    await task

    while seconds > 0:
        seconds -= 1
        await asyncio.sleep(1)
    
    if not task.cancelled():
        await ping_everyone(ctx)

def inputToDateTime(time):
    datetime_object = datetime.strptime(f"{datetime.now(timezone.utc).date()} {time}:00", '%Y-%m-%d %H:%M:%S')
    return datetime_object

def validateTimeInput(input):
    return re.search("^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", input).group(0)

@bot.command()
async def time(ctx, command = None, time = None):
    global user_time_offset_from_utc
    if (command == time == None):
        local = datetime.now(timezone.utc)
        await ctx.send(f"Current UTC time: {str(local.time)}")
    elif (command.lower() == "set"):
        valid_time_found = validateTimeInput(time)
        if (valid_time_found):
            aware_timezone = inputToDateTime(valid_time_found).replace(tzinfo=timezone.utc)
            user_time_offset_from_utc = (aware_timezone - datetime.now(timezone.utc)).seconds
            if user_time_offset_from_utc > 43200:
                user_time_offset_from_utc = -(86400 - user_time_offset_from_utc)
        else:
            await sendError(ctx, 400, "Alarm not set. Please use the following 24-hour format and try again: \"/time set HH:MM\"")

@bot.command()
async def toggle(ctx):
    global switched_on
    switched_on = False if (switched_on) else True
    if (switched_on):
        await ctx.send("Alarm toggled on.")
    else:
        await ctx.send("Alarm toggled off.")

@bot.command()
async def alarm(ctx, command = None, time = None):
    global alarm_running
    global user_time_offset_from_utc
    global task
    if (command == time == None):
        alarm_running = False
        try:
            task.cancel()
            await ping_everyone(ctx)
        except:
            await ctx.send("No active alarm found to trigger.")
        
    else:
        if (command.lower() == "set" and not alarm_running):
            valid_time_found = validateTimeInput(time)
            if (valid_time_found != None):
                aware_time = inputToDateTime(valid_time_found).replace(tzinfo=timezone.utc)
                current_offset_time = datetime.now(timezone.utc) + timedelta(seconds=user_time_offset_from_utc)

                if aware_time < current_offset_time:
                    aware_time += timedelta(days=1)

                await setAlarm(ctx, (aware_time - current_offset_time).seconds)
            else:
                await sendError(ctx, 400, "Alarm not set. Please use the following 24-hour format and try again: \"/alarm set HH:MM\"")
        else:
            await sendError(ctx, 300, "Alarm not set. An alarm may already be in progress, please trigger it and retry.")

@bot.command()
async def countdown(ctx):
    print("In countdown :) ")
    global seconds
    if (seconds != None and seconds > 0):

        minutes, _ = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)

        hours_output = "hours" if hours > 1 else "hour" if hours == 1 else ""
        minutes_output = "minutes" if minutes > 1 else "minute" if minutes == 1 else ""
        
        output = "Alarm will trigger in "
        if (hours_output != ""):
            output += str(hours) + " " + hours_output
            if (minutes_output != ""):
                output += "and "
        if (minutes_output != ""):
            output += str(minutes) + " "+ minutes_output

        await ctx.send(output+".")
    else:
        await sendError(ctx, 300, "Alarm not set. Please set one and retry to see a countdown.")

bot.run(TOKEN)