import re, os, importlib
from pyrogram import Client
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters

client = Client('user', config_file='config.ini')

VERSION = 1.7

@client.on_message(filters.regex('^version$', re.I) & filters.user("me"))
async def version(client: Client, message: Message):
    await message.edit("SafaSelf\n[Source](https://github.com/SafaSafari/SafaSelf)\nVersion {}".format(VERSION))

@client.on_message(filters.regex('^help$', re.I) & filters.user("me"))
async def help(client: Client, message: Message):
    help = """
    version: Return current version of SafaSelf
    help: Return this help message
    """
    for file in os.listdir('plugins'):
        if file[-3:] != '.py': continue
        help += "\n" + importlib.import_module('plugins.' + file[:-3]).help + "\n"
    await message.edit("SafaSelf\n{}\n[Source](https://github.com/SafaSafari/SafaSelf)\nVersion {}".format(help, VERSION))

client.run()
