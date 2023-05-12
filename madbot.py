import discord
from dateutil import tz
import datetime
import calendar
from discord.ext import tasks
import os
import re
from dotenv import load_dotenv

import gzip

load_dotenv()
TOKEN = os.getenv('TOKEN')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))
GUILD_ID = int(os.getenv('GUILD_ID'))
LOGS_PATH = os.getenv('LOGS_PATH')
LOG_FILE_NAME = os.getenv('LOG_FILE_NAME')

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

dateRE = re.compile("^(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?P<year>\d{4}$|'\d{2})|^TODAY$|^YESTERDAY$", re.IGNORECASE)

def fileNameGenerator(date):
    year = date.year
    month = date.month
    day = date.day
    dayNum = calendar.weekday(year, month, day)
    return f'{LOGS_PATH}/{year}/{months[month-1]}/{day}_{weekdays[dayNum]}_{LOG_FILE_NAME}'

@client.event
async def on_ready():
    await tree.sync(guild=discord.Object(id="632821056096436234"))
    print(f'Logged on as {client.user}')
    myloop.start()

# @client.event
# async def on_message(message):
#     # don't respond to ourselves
#     if message.author == client.user:
#         return

#     if message.content == '!ping':
#         await message.channel.send("I am alive.")

@tree.command(name = 'ping', description = "Ping the bot", guild = discord.Object(id=GUILD_ID))
async def pingBot(interaction: discord.Interaction):
    await interaction.response.send_message("Still alive.")

@tree.command(name = 'getlog', description = "Fetch a log file for a given date (DD/MM/YYYY, DD/YY/'YY or TODAY or YESTERDAY)", guild = discord.Object(id=GUILD_ID))
@discord.app_commands.describe(date="DD/MM/YYYY, DD/MM/'YY, TODAY, or YESTERDAY")
async def getLog(interaction: discord.Interaction, date: str):
    # ^(?P<day>\d{1,2})/(?P<month>\d{1,2})/(?<year>\d{4}$|'\d{2})|^TODAY$|^YESTERDAY$
    # print(date)
    if type(date) is not str:
        await interaction.response.send_message("Server recieved something odd.")
        return
    
    match = dateRE.search(date.strip().lower())
    if match is None:
        await interaction.response.send_message(
            "Could not extract a proper date from input. Proper inputs follow these layouts:```\nDD/MM/YYYY\nDD/MM/'YY\nTODAY\t\t#for today's current log\nYESTERDAY\t#for yesterday's compressed log```"
            )
        return

    if match.group(0) == 'today':
        logfile = f'{LOGS_PATH}/{LOG_FILE_NAME}'
        if os.path.isfile(logfile):
            content = "Current logs for today."
            file = discord.File(logfile, LOG_FILE_NAME)
            await interaction.response.send_message(content=content, file=file)
        else:
            await interaction.response.send_message(f"Strange... There should be a log file at the path below, but it does not appear to be there.```{logfile}```")
        return
    
    if match.group(0) == 'yesterday':
        logfile = fileNameGenerator(datetime.date.today() - datetime.timedelta(days=1))
        ziplogfile = f'{logfile}.gz'
        if os.path.isfile(ziplogfile):
            content = "Yesterday's log files."
            fileName = re.search("/([^/]+)$", logfile)
            try:
                with gzip.open(ziplogfile, 'rb') as f:
                    file = discord.File(f, fileName.group(1))
                    await interaction.response.send_message(content=content, file=file)
                    return
            except:
                await interaction.response.send_message(f'An error occurred when opening yesterday\'s file at the path below.```{ziplogfile}```.')
        else:
            await interaction.response.send_message(f'Failed to locate yesterday\'s file at the path below.```{ziplogfile}```')
        return

    day = match.group("day")
    if len(day) == 1:
        day = f'0{day}'
    month = match.group("month")
    if len(month) == 1:
        month = f'0{month}'
    dateStr = f'{day}/{month}/{match.group("year")}'

    date: datetime.date = None
    try:
        # DD/MM/'YY
        if match.group("year").startswith("'"):
            date = datetime.datetime.strptime(dateStr, "%d/%m/'%y")
        # DD/MM/YYYY
        else:
            date = datetime.datetime.strptime(dateStr, "%d/%m/%Y")
    except ValueError:
        await interaction.response.send_message(f"`{dateStr}` is not a proper date value. Days should range from 1 to 31, and months should range from 1 to 12.")
        return

    logfile = fileNameGenerator(date)
    ziplogfile = f'{logfile}.gz'
    if os.path.isfile(logfile):
        content = date.strftime('%d %B, %Y')
        fileName = re.search("/([^/]+)$", logfile)
        try:
            with gzip.open(ziplogfile, "rb") as f:
                file = discord.File(f, fileName.group(1))
                await interaction.response.send_message(content=content, file=file)
                return
        except:
            await interaction.response.send_message(f"An error occurred when attempting to open log file corresponding to the date provided ({content}). Opened file at the path below.```{ziplogfile}```")
    else:
        await interaction.response.send_message(f"Could not find any logs corresponding to the provided date ({date.strftime('%d %B, %Y')}). Checked at the path below.```{ziplogfile}```")

timezone = tz.gettz('America/Los_Angeles')
time = datetime.time(hour=5, minute=30, tzinfo=timezone)

@tasks.loop(time=time)
async def myloop():
    date = datetime.datetime.now() - datetime.timedelta(days=1)
    logPath = fileNameGenerator(date)
    zipLogPath = f'{logPath}.gz'
    channel = client.get_channel(CHANNEL_ID)
    fileName = re.search("/([^/]+)$", logPath)
    embedVar = discord.Embed(title="Daily task encounted an error!", color=0xF22121)

    if os.path.isfile(zipLogPath):
        try:
            with gzip.open(zipLogPath, 'rb') as f:
                file = discord.File(f, fileName.group(1))
                await channel.send(content=date.strftime("%d %B, %Y"), file=file)
                return
        except:
            embedVar.description = f'Failed to open file at path below.```{logPath}.gz```'
    else:
        embedVar.description = f'Failed to locate file at path below.```{logPath}.gz```'

    embedVar.timestamp=datetime.datetime.now()
    await channel.send(embed=embedVar)

client.run(TOKEN)