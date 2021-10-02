import os
import re
import json
from pyrogram import Client
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters

help = """
debug {[CHAT_ID [MESSAGE_ID | OFFSET LENGTH]] | REPLY}: Return a file that contain information of selected messages
info {[REPLY | CHAT_ID]}: Return information about a message or chat_id"""
@Client.on_message(filters.regex(r'^debug', re.I) & filters.me)
async def debug(client: Client, message: Message):
    part = message.text.split(' ')
    if message.reply_to_message:
        debug = message.reply_to_message
    elif len(part) == 3:
        debug = await client.get_messages(part[1], part[2])
    elif len(part) == 4:
        debug = await client.get_messages(part[1], range(int(part[2]), int(part[3])))
    else:
        return
    await message.delete()
    debug = str(debug)
    with open('debug.json', 'w+') as f:
        f.write(debug)
    await client.send_document("me", "debug.json")
    os.remove('debug.json')


@Client.on_message(filters.regex(r'^info', re.I) & filters.me)
async def info(client: Client, message: Message):
    info = message.reply_to_message if message.reply_to_message else message.chat
    part = message.text.split(' ')
    if len(part) == 2:
        info = await client.get_chat(part[1])
    info = str(info)
    text = json.dumps(await parse(json.loads(info)), indent=4)
    if text.__len__() > 4096:
        await message.delete()
        with open('info.json', 'w+') as f:
            f.write(info)
        await message.reply_document('info.json', reply_to_message_id=message.reply_to_message.message_id)
        os.remove('info.json')
    else:
        await message.edit(text)


async def parse(item: dict):
    ret = {}
    for i, j in item.items():
        if type(j) == dict:
            ret["`{}`".format(i)] = await parse(j)
        else:
            ret["`{}`".format(i)] = "`{}`".format(j)
    return ret
