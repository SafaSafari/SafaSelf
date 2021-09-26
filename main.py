import re
from pyrogram import Client
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
import config

client = Client('user', config.API_ID, config.API_HASH, plugins=dict(root="plugins"))

@client.on_message(filters.regex('^version$', re.I) & filters.user("me"))
async def version(client: Client, message: Message):
    await message.edit("SafaSelf\n[Source](https://github.com/SafaSafari/SafaSelf)\nVersion 1.4")

client.run()
