import discord
from discord.ext import commands
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
bot_token = config.get('BotConfig', 'Token')


intents = discord.Intents.default()
intents.reactions = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Bot ist bereit: {bot.user.name}')

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return

    log_message = f'Benutzer: {message.author.name} | Nachricht: {message.content} | Zeit: {message.created_at}\n'

    with open('message_log.txt', 'a+') as file:
        file.write(log_message)

print(bot_token)
bot.run(bot_token)
