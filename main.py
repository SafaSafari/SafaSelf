
from base64 import b64decode
import pyrogram
import os
import re
import json
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
from pyrogram.types import MessageEntity

import config

client = pyrogram.Client('user', config.API_ID, config.API_HASH)


@client.on_message(filters.regex('^debug', re.I))
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


@client.on_message(filters.regex('^info', re.I))
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
        await client.send_document(message.chat.id, 'info.json', reply_to_message_id=message.message_id)
        os.remove('info.json')
    else:
        await message.edit(text)


@client.on_message(filters.regex('^@all', re.I) & filters.group)
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
        await client.send_message(message.chat.id, text, entities=entity)


@client.on_message(filters.regex('^version$', re.I))
async def version(client: Client, message: Message):
    await client.send_message(message.chat.id, "SafaSelf\n[Source](https://github.com/SafaSafari/SafaSelf)\nVersion 1.0", reply_to_message_id=message.message_id)


async def parse(item: dict):
    ret = {}
    for i, j in item.items():
        if type(j) == dict:
            ret["`{}`".format(i)] = await parse(j)
        else:
            ret["`{}`".format(i)] = "`{}`".format(j)
    return ret

client.run()
