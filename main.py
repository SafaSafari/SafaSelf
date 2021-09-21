
from io import StringIO
import os
import re
import json
import requests
import asyncio
from tqdm import tqdm
from base64 import b64decode
from pyrogram import Client
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
from pyrogram.types import MessageEntity

import config

client = Client('user', config.API_ID, config.API_HASH)

old = None
file = StringIO()


@client.on_message(filters.regex('^debug', re.I) & filters.user("me"))
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


@client.on_message(filters.regex('^info', re.I) & filters.user("me"))
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


@client.on_message(filters.regex('^@all', re.I) & filters.group & filters.user("me"))
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


@client.on_message(filters.regex('^upload', re.I) & filters.user("me"))
async def upload(client: Client, message: Message):
    caption = "Uploaded with SafaSelf ([Source](https://github.com/SafaSafari/SafaSelf))"
    part = message.text.split(' ')
    REGEX = re.compile(
        "((?:(?:https?):\/\/|www\.)*[-a-z0-9+&@#\/%?=~_|!:,.;]*\.[-a-z0-9+&@#\/%=~_|\?]*)", re.I)
    name = None
    tq = None
    document = None
    if message.reply_to_message:
        i = 0
        if len(part) == 2:
            if isinstance(part[1], int):
                i = part[1]
            else:
                name = part[1]
        text = message.reply_to_message.text if message.reply_to_message.text else message.reply_to_message.caption
        result = REGEX.findall(text)
        link = result[i] if len(result) > i else None
    elif len(part) > 1:
        link = part[1]
    if len(part) == 3:
        name = part[2]
    if ((message.web_page and message.web_page.document) or (message.reply_to_message and message.reply_to_message.web_page and message.reply_to_message.web_page.document)) and not name:
        document = link
    elif link:
        response = requests.get(link, stream=True)
        header = response.headers
        if not name:
            name = header['content-disposition'].split(';')[1].replace('filename=', '').strip(
                '" ') if header.get('content-disposition') else link.split('/')[-1]
        edit = ''
        tq = tqdm(desc=name, total=int(
            header['content-length']), file=file, unit='B', unit_scale=True, mininterval=1)
        with open(name, 'wb') as f:
            chunk_size = 4096
            for chunk in response.iter_content(chunk_size=chunk_size):
                new = file.getvalue().strip()
                file.truncate(0)
                file.seek(0)
                if new and edit != new:
                    edit = new
                    await message.edit_caption("Download to server: {}\n/cancel to cancel it!!!".format(edit))
                tq.update(chunk_size)
                f.write(chunk)
        document = name
        tq.reset()
    if document:
        tag = "Upload to telegram"
        await client.send_document(message.chat.id, document=document, file_name=name, caption=caption, progress=progress, progress_args=(message, tq, file, tag))
        await message.delete()
    if os.path.exists(name):
        os.remove(name)


@client.on_message(filters.regex('^rename', re.I) & filters.user("me"))
async def rename(client: Client, message: Message):
    part = message.text.split(' ')
    if len(part) == 2 and message.reply_to_message:
        name = part[1]
        tq = tqdm(desc=name, total=message.reply_to_message.document.file_size, file=file, unit='B', unit_scale=True, mininterval=1)
        tag = "Download from telegram"
        await message.reply_to_message.download(name, progress=progress, progress_args=(message, tq, file, tag))
        tag = "Upload to telegram"
        await client.send_document(message.chat.id, "downloads/" + name, progress=progress, progress_args=(message, tq, file, tag))
        os.remove("downloads/" + name)


@client.on_message(filters.regex('^version$', re.I) & filters.user("me"))
async def version(client: Client, message: Message):
    await message.edit("SafaSelf\n[Source](https://github.com/SafaSafari/SafaSelf)\nVersion 1.3")


@client.on_message(filters.command('cancel') & filters.user("me"))
async def cancel(client: Client, message: Message):
    os.system("nohup python3 main.py &")
    asyncio.sleep(2)
    exit()


async def progress(current, total, message, tq, file, tag):
    global old
    tq.update(current - (old if old else 0))
    old = current
    progress = file.getvalue()
    if progress:
        await message.edit_text("{}: {}\n/cancel to cancel it!!!".format(tag, progress))
    file.truncate(0)
    file.seek(0)


async def parse(item: dict):
    ret = {}
    for i, j in item.items():
        if type(j) == dict:
            ret["`{}`".format(i)] = await parse(j)
        else:
            ret["`{}`".format(i)] = "`{}`".format(j)
    return ret

client.run()
