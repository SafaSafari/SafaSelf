from base64 import b64decode
import re
from pyrogram.client import Client
from pyrogram.types import MessageEntity
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
help = """
@all INT: Split messages mention by INT
"""
@Client.on_message(filters.regex('^@all', re.I) & filters.group & filters.user("me"))
async def all(client: Client, message: Message):
    n = 100
    part = message.text.split(' ')
    if len(part) == 2:
        n = int(part[1])
    all = await client.get_chat_members(message.chat.id, 0, await client.get_chat_members_count(message.chat.id))
    pad = b64decode("4oGj").decode('utf-8')
    chunk = [all[i:i + n] for i in range(0, len(all), n)]
    for members in chunk:
        text = "آهای جماعت"
        entity = [MessageEntity(type="code", offset=0, length=text.__len__())]
        for i in range(len(members)):
            entity.append(MessageEntity(type="text_mention", offset=text.__len__(
            ), length=pad.__len__(), user=members[i]['user']))
            text += pad
        await message.reply_text(text, entities=entity)

