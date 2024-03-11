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

# Time offset from base UTC in seconds
bot_time_offset_from_utc = 0

user_time_offset_from_bot = 0

switched_on = True

alarm_running = False

timezones = {}

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

async def ping_everyone(ctx):
    global switched_on 
    if (switched_on):
        await ctx.send("@everyone")

@bot.command()
async def toggle(ctx):
    global switched_on
    switched_on = False if (switched_on) else True
    if (switched_on):
        await ctx.send("The alarm has been toggled on!")
    else:
        await ctx.send("The alarm has been toggled off!")

async def sendError(ctx, errorCode: int, errorMessage: str):
    await ctx.send(f"Error [{errorCode}]: {errorMessage}")

async def setAlarm(ctx, seconds_to_sleep):
    global alarm_running
    print(f"Setting alarm for {seconds_to_sleep} seconds.")
    alarm_running = True
    await asyncio.sleep(seconds_to_sleep)
    await ping_everyone(ctx)

def inputToDateTime(time):
    datetime_object = datetime.strptime(f"{datetime.now(timezone.utc).date()} {time}:00", '%Y-%m-%d %H:%M:%S')
    return datetime_object

def validateTimeInput(input):
    return re.search("^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", input).group(0)

# Currently broken, ignore
# def createMapToTimezones():
#     for tz in pytz.common_timezones:
#         try:
#             tz_obj = pytz.timezone(tz)
#             abbrev = str(tz_obj.localize(datetime.now()).tzname())
#             if (tz not in timezones):
#                 timezones[tz] = tz_obj.localize(datetime.now()).tzinfo
#         except:
#             pass
#     return

async def displayTimeZones(ctx):
    output = ""
    for (key, value) in timezones.items():
        output += f"\n{key}: {value}"
        if (len(output) > 1000):
            await ctx.send(output)
            output = ""
    await ctx.send(output)

    # timezone_list = pytz.all_timezones if (timezone != None) else pytz.common_timezones
    # output = ""
    # char_count = 0
    # for timeZone in pytz.all_timezones:
    #     output += (f"\n{timeZone}")
    #     char_count += len(str(timeZone))
    #     if (char_count > 1000):
    #         await ctx.send(output)
    #         output = ""
    #         char_count = 0
    # await ctx.send(output)


@bot.command()
async def time(ctx, command = None, time = None):
    if (command == time == None):
        local = datetime.now(timezone.utc)
        await ctx.send(f"Current bot time: {str(local.time)}")
    # elif (command.lower() == "display"):
    #     await displayTimeZones(ctx)
    elif (command.lower() == "set"):
        # set your current time here and the offset will automatically be calculated
        # current time must be also entered in 24 hour format!!
        valid_time_found = validateTimeInput(time)
        if (valid_time_found):
            aware_timezone = inputToDateTime(valid_time_found).replace(tzinfo=timezone.utc)
            user_time_offset_from_bot = (aware_timezone - datetime.now(timezone.utc)).seconds
            print(f"user time offset = {user_time_offset_from_bot}")
        else:
            sendError(ctx, 400, "Alarm not set. Please use the following 24-hour format and try again: \"/time set HH:MM\"")


@bot.command()
async def alarm(ctx, command = None, time = None):
    if (command == time == None):
        await ctx.send("@everyone")
    else:
        if (command.lower() == "set"):
            valid_time_found = validateTimeInput(time)
            if (valid_time_found != None):
                aware_time = inputToDateTime(valid_time_found).replace(tzinfo=timezone.utc)
                if aware_time < datetime.now(timezone.utc):
                    aware_time += timedelta(days=1)
                await setAlarm(ctx, (aware_time - datetime.now(timezone.utc)).seconds)
            else:
                sendError(ctx, 400, "Alarm not set. Please use the following 24-hour format and try again: \"/alarm set HH:MM\"")

bot.run(TOKEN)