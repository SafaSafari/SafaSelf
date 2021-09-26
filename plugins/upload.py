import os
import requests
from tqdm import tqdm
from io import StringIO
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
import re
help = """
upload {LINK | REPLY} [NAME]: upload file from link
rename REPLY [NAME]: rename replied file
/cu: cancel rename or upload proccess
"""
old = None
stop = False
file = StringIO()

@Client.on_message(filters.regex('^upload', re.I) & filters.user("me"))
async def upload(client: Client, message: Message):
    global stop
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
                if stop:
                    stop = False
                    await message.delete()
                    return
                new = file.getvalue().strip()
                file.truncate(0)
                file.seek(0)
                if new and edit != new:
                    edit = new
                    await message.edit_caption("Download to server: {}\n/cu to cancel it!!!".format(edit))
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

@Client.on_message(filters.regex('^rename', re.I) & filters.user("me"))
async def rename(client: Client, message: Message):
    part = message.text.split(' ')
    if len(part) == 2 and message.reply_to_message:
        name = part[1]
        tq = tqdm(desc=name, total=message.reply_to_message.document.file_size,
                    file=file, unit='B', unit_scale=True, mininterval=1)
        tag = "Download from telegram"
        await message.reply_to_message.download(name, progress=progress, progress_args=(message, tq, file, tag))
        tag = "Upload to telegram"
        await client.send_document(message.chat.id, "downloads/" + name, progress=progress, progress_args=(message, tq, file, tag))
        await message.delete()
        os.remove("downloads/" + name)

@Client.on_message(filters.command('cu') & filters.user("me"))
async def cancel(client: Client, message: Message):
    global stop
    stop = True

async def progress(current, total, message, tq, file, tag):
    global old, stop
    tq.update(current - (old if old else 0))
    old = current
    progress = file.getvalue()
    if stop:
        stop = False
        await message.delete()
        await client.stop_transmission()
    if progress:
        await message.edit_text("{}: {}\n/cu to cancel it!!!".format(tag, progress))
    file.truncate(0)
    file.seek(0)
