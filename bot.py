import asyncio
import os
import re
from datetime import datetime, timedelta, timezone
from multiprocessing import Process

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='/', intents=intents)
bot.remove_command("help")

# Necessary as we'll just work from UTC and durations rather than working "to" a specific time
user_time_offset_from_utc = 0
# The final call in whether everyone is pinged
switched_on = True
# Check whether the alarm is running already so we don't trigger an alarm that doesn't exist
alarm_running = False
# The task to hold the timer for the actual alarm
task = None
# The duration we'll be counting down from
seconds = None

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

async def ping_everyone(ctx):
    global switched_on 
    global alarm_running

    if (switched_on and alarm_running):
        alarm_running = False
        await ctx.send("@everyone")
    elif (not switched_on):
        await ctx.send(":warning:  Alarm was toggled off. Please switch toggle to trigger.")
    elif (not alarm_running):
        await ctx.send(":information_source:  No active alarm found to trigger.")

async def startCountdown(ctx):
    global seconds
    for _ in range(seconds, 0, -1):
        await asyncio.sleep(1)
        seconds -= 1

async def setAlarm(ctx, seconds_to_sleep):
    global alarm_running
    global switched_on
    global task
    global seconds

    seconds = seconds_to_sleep
    alarm_running = True

    task = asyncio.ensure_future(asyncio.sleep(seconds_to_sleep))
    
    await countdown(ctx)
    await asyncio.gather(
        task,
        startCountdown(ctx)
    )
    
    if not task.cancelled():
        await ping_everyone(ctx)

    alarm_running = False
    switched_on = True

def inputToDateTime(time):
    datetime_object = datetime.strptime(f"{datetime.now(timezone.utc).date()} {time}:00", '%Y-%m-%d %H:%M:%S')
    return datetime_object

def validateTimeInput(input):
    try:
        x = re.search("^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$", input).group(0)
        return x
    except:
        return None

def returnUserTime():
    global user_time_offset_from_utc
    user_time = datetime.now(timezone.utc) + timedelta(seconds = user_time_offset_from_utc)
    return str(user_time.time())[0:5]

@bot.command()
async def time(ctx, command = None, time = None):
    global user_time_offset_from_utc
    global alarm_running
    if (not alarm_running):
        if (command == None and time == None):
            await ctx.send(f":information_source:  Your time is set to {returnUserTime()}")
        elif (command == None or time == None):
            await ctx.send(f":warning:  Time not set. Please use the following 24-hour format and try again: **/time set HH:MM**")
            await ctx.send(f":information_source:  Your time is set to {returnUserTime()}")
        elif (command.lower() == "set"):
            valid_time_found = validateTimeInput(time)
            if (valid_time_found):
                user_utc_time = inputToDateTime(valid_time_found).replace(tzinfo=timezone.utc)
                user_time_offset_from_utc = (user_utc_time - datetime.now(timezone.utc)).seconds
                # If the offset is more than 12 hours in the future, we need to set a negative offset
                if user_time_offset_from_utc > 43200:
                    user_time_offset_from_utc = -(86400 - user_time_offset_from_utc)
                await ctx.send(f":information_source:  Your time has been successfully updated to {valid_time_found}.")
            else:
                await ctx.send(f":warning:  Time not set. Please use the following 24-hour format and try again: **/time set HH:MM**")
    else:
        await ctx.send(f":warning:  An alarm is already in progress, please cancel it first to configure your time.")

@bot.command()
async def toggle(ctx):
    global switched_on
    switched_on = False if (switched_on) else True
    if (switched_on):
        await ctx.send(":information_source:  Alarm toggled on.")
    else:
        await ctx.send(":information_source:  Alarm toggled off.")

@bot.command()
async def alarm(ctx, command = None, time = None):
    global alarm_running
    global user_time_offset_from_utc
    global task
    if (command == time == None):
        try:
            task.cancel()
            await ping_everyone(ctx)
        except:
            await ctx.send(":information_source:  No active alarm found to trigger.")
    elif (command == None or time == None):
        await ctx.send(f":warning:  Alarm not set. Please use the following 24-hour format and try again: **/alarm set HH:MM**")
    else:
        if (command.lower() == "set" and not alarm_running):
            valid_time_found = validateTimeInput(time)
            if (valid_time_found != None):

                aware_time = inputToDateTime(valid_time_found).replace(tzinfo=timezone.utc)
                current_offset_time = datetime.now(timezone.utc) + timedelta(seconds=user_time_offset_from_utc)

                if aware_time < current_offset_time:
                    aware_time += timedelta(days=1)
                
                # We set an alarm by calculating the difference in seconds rather than waiting for a single "time"
                await setAlarm(ctx, (aware_time - current_offset_time).seconds)
            else:
                await ctx.send(f":warning:  Alarm not set. Please use the following 24-hour format and try again: **/alarm set HH:MM**")
        else:
            await ctx.send(f":warning:  Alarm not set. An alarm may already be in progress, please trigger it with **/alarm** and retry using **/alarm set HH:MM**")

@bot.command()
async def countdown(ctx):
    global seconds
    global alarm_running
    if (alarm_running):
        if (seconds != None and seconds > 0):
            minutes, sec = divmod(seconds, 60)
            hours, minutes = divmod(minutes, 60)

            hours_output = "hours" if hours > 1 else "hour" if hours == 1 else ""
            minutes_output = "minutes" if minutes > 1 else "minute" if minutes == 1 else ""
            seconds_output = "seconds" if sec > 1 else "second" if sec == 1 else ""
            
            output = "Alarm will trigger in "
            if (hours_output != ""):
                output += str(hours) + " " + hours_output
                if (minutes_output != "" and seconds_output == "") or (minutes_output == "" and seconds_output != ""):
                    output += " and "
                elif(minutes_output != "" and seconds_output != ""):
                    output += ", "
            if (minutes_output != ""):
                output += str(minutes) + " " + minutes_output
                if (seconds_output != ""):
                    output += " and "
            if (seconds_output != ""):
                output += str(sec) + " " + seconds_output

            await ctx.send(":information_source:  "+output+".")
        else:
            await ctx.send(f":warning:  Alarm not set. Please set one and retry to see a countdown.")
    else:
        await ctx.send(":information_source:  No alarm set or switched on. Please set an alarm and try again.")

@bot.command()
async def help(ctx):
    output = f"""
    :scroll: :scroll: **Command List** :scroll: :scroll:

    :bell:  **/alarm** ==> Trigger the alarm (if it's running), immediately

    :alarm_clock:  **/alarm set HH:MM** ==> Set an alarm given a 24 hour time, for example **/alarm set 10:00**

    :electric_plug:  **/toggle** ==> Switch the alarm on or off

    :stopwatch:  **/countdown** ==> See how long until the alarm goes off
    
    :clock:  **/time** ==> See your current time (according to the bot it's **{returnUserTime()}** where you are!)

    :world_map:  **/time set HH:MM** ==> Set your current time if :point_up_2: isn't correct! This defaults to UTC
    
    :question:  **/help** ==> See this message again

    Thanks to Time icons created by Freepik - Flaticon for the hourglass icon! 
    Find their icons here: https://www.flaticon.com/free-icons/time
    """

    await ctx.send(output)

bot.run(TOKEN)