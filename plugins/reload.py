import sys, re, os
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers.handler import Handler
help = """
reload: Reload all modules
"""
@Client.on_message(filters.regex('^reload$', re.I) & filters.user("me"))
async def load_plugin(client: Client, message: Message):
    await message.edit("Reloaded")
    python = sys.executable
    os.execl(python, python, *sys.argv)