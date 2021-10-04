import os
import asyncio
import json
from PIL import Image
from aiohttp import ClientSession
from tqdm import tqdm
from io import StringIO
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
import re
import hashlib
help = """
upload {LINK | REPLY} [NAME]: upload file from link
rename REPLY [NAME]: rename replied file
/cu: cancel rename or upload proccess
"""
STOP = {}
FILE = StringIO()
TQ = {}


@Client.on_message(filters.regex(r'^upload', re.I) & filters.me)
async def upload(client: Client, message: Message):
    caption = "Uploaded with SafaSelf ([Source](https://github.com/SafaSafari/SafaSelf))"
    part = message.text.split(' ')
    REGEX = re.compile(
        r"(?i)\b((?:[a-z][\w-]+:(?:\/{1,3}|[a-z0-9%])|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]+|\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))*\))+(?:\((?:[^\s()<>]+|(?:\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))", re.I)
    YOUTUBE_REGEX = re.compile(
        r"http(?:s?):\/\/(?:www\.)?(?:m\.)?youtu(?:be\.com\/watch\?v=|\.be\/)([\w\-\_]*)", re.I)

    name = None
    document = None
    i = 0
    if message.reply_to_message:
        if len(part) == 2:
            if part[1].isdigit():
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
    youtube = YOUTUBE_REGEX.findall(link)
    youtube_id = youtube[i] if len(youtube) > i else None
    if youtube_id:
        await download_youtube(youtube_id, client, message, caption)
    elif (message.web_page or (message.reply_to_message and message.reply_to_message.web_page)) and not name:
        document = link
    elif link:
        document = await download(link, name, message)
    if document:
        tag = "Upload to telegram"
        hash = hashlib.md5(document.encode('utf-8')).hexdigest()
        await client.send_document(message.chat.id, document=document, file_name=document, caption=caption, progress=progress, progress_args=(message, tag, client, hash))
        await message.delete()
    if type(document) == str and os.path.exists(document):
        os.remove(document)


@Client.on_message(filters.regex('^rename', re.I) & filters.me)
async def rename(client: Client, message: Message):
    part = message.text.split(' ')
    if len(part) == 2 and message.reply_to_message:
        name = part[1]
        hash = hashlib.md5(name.encode('utf-8')).hexdigest()
        STOP[hash] = False
        TQ[hash] = tqdm(file=FILE, unit='b', unit_scale=True,
                        mininterval=2, unit_divisor=1024, ascii=False)
        TQ[hash].set_description(name)
        TQ[hash].reset(message.reply_to_message.document.file_size)
        tag = "Download from telegram"
        FILE.truncate(0)
        FILE.seek(0)
        await message.reply_to_message.download(name, progress=progress, progress_args=(message, tag, client, hash))
        tag = "Upload to telegram"
        
        await client.send_document(message.chat.id, "downloads" + os.sep + name, progress=progress, progress_args=(message, tag, client, hash))
        await message.delete()
        os.remove("downloads" + os.sep + name)


@Client.on_message(filters.command('cu') & filters.me)
async def cancel(client: Client, message: Message):
    if len(message.command) > 1:
        STOP[message.command[1]] = True


async def download(link, name, message):
    FILE.truncate(0)
    FILE.seek(0)
    async with ClientSession() as session:
        async with session.get(link) as response:
            header = response.headers
            if not name:
                name = header['content-disposition'].split(';')[1].replace('filename=', '').strip(
                    '" ') if header.get('content-disposition') else link.split('/')[-1]
                if name.__contains__('?'):
                    name = ''.join(name.split('?')[:-1])
            edit = ''
            hash = hashlib.md5(name.encode('utf-8')).hexdigest()
            STOP[hash] = False
            TQ[hash] = tqdm(file=FILE, unit='B', unit_scale=True,
                            mininterval=2, unit_divisor=1024, ascii=False)
            TQ[hash].reset(int(header['content-length']))
            TQ[hash].set_description(name)
            with open(name, 'wb') as f:
                chunk_size = 4096
                async for chunk in response.content.iter_chunked(chunk_size):
                    if STOP[hash]:
                        return
                    new = FILE.getvalue()
                    if new.__contains__('\r'):
                        new = new.split('\r')[1]
                    FILE.truncate(0)
                    FILE.seek(0)
                    if new and edit != new:
                        edit = new
                        text = "Download to server:\n`{}`\n`/cu {}`\nto cancel (Click to copy)".format(
                            edit, hash)
                        await message.edit_text(text)
                    TQ[hash].update(chunk_size)
                    f.write(chunk)
    TQ[hash].reset()
    return name


async def progress(current, total, message, tag, client, hash):
    TQ[hash].update(current - TQ[hash].n)
    progress = FILE.getvalue()
    if progress.__contains__('\r'):
        progress = progress.split('\r')[1]
    FILE.truncate(0)
    FILE.seek(0)
    if STOP[hash]:
        STOP[hash] = False
        await message.edit_text("لغو شد\nCanceled")
        files = os.scandir('.')
        for file in files:
            if str(file).__contains__(TQ[hash].get_description()):
                os.remove(file)
        await client.stop_transmission()
    if progress:
        text = "{}:\n`{}`\n`/cu {}`\nto cancel (Click to copy)".format(
            tag, progress, hash)
        await message.edit_text(text)


async def run(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()
    if proc.returncode == 0:
        return stdout
    else:
        return False

get_json = "youtube-dl --cookie cookie.txt '{link}' -j"


async def parse_json(input, force_request=False):
    request = None
    data = json.loads(input)
    for format in data["formats"]:
        if force_request and format['format_id'] == force_request:
            request = format
            break
        if format['format_id'] == "22":
            request = format
        if not request and format['format_id'] == "18":
            request = format
    thumbnail = data["thumbnail"]
    title = data["title"]
    desc = data["description"]
    duration = data["duration"]
    url = request["url"]
    width = request['width']
    height = request['height']
    channelid = data['channel_id']
    return [thumbnail, title, desc, url, width, height, duration, channelid]


async def download_youtube(id, client, message, caption):
    j = (await run(get_json.format(link="https://youtube.com/watch?v=" + id)))
    result = (await parse_json(j))
    if not result[3]:
        asyncio.sleep(500)
        return await download_youtube(id, client, message, caption)
    video = id + ".mp4"
    hash = hashlib.md5(video.encode('utf-8')).hexdigest()
    await download(result[3], video, message)
    if not os.path.exists(video):
        await asyncio.sleep(60)
        return await download_youtube(id, client, message, caption)
    async with ClientSession() as session:
        async with session.get(result[0]) as get:
            ext = client.guess_extension(
                get.headers['Content-Type'].split(';')[0])
            if not ext:
                ext = '.' + \
                    get.headers['Content-Type'].split(';')[0].split('/')[1]
            image = id + ext
            thumb = await get.read()
            with open(image, 'wb') as f:
                f.write(thumb)
    caption = result[1] + "\n\n" + result[2]
    if os.path.splitext(image)[1] == '.webp':
        im = Image.open(image)
        im.save(id + '.jpg', 'jpeg')
    if str(caption).__len__() - 44 > 1024:
        caption = "\n".join(
            caption[:(1024 - 43 - 3)].split("\n")[:-1]) + "\n..."
    if not STOP[hash]:
        await client.send_video(message.chat.id, video, caption=caption, thumb=id + '.jpg', duration=result[6], supports_streaming=True, width=result[4], height=result[5], progress=progress, progress_args=(message, "Uploading to telegram", client, hash))
    audio = id + ".mp3"
    if not os.path.exists(audio) and not STOP[hash]:
        await run('ffmpeg -i "{}" -vn -- "{}"'.format(video, audio))
    if STOP[hash]:
        STOP[hash] = False
        await message.edit_text("لغو شد\nCanceled")
    else:
        await client.send_audio(message.chat.id, audio, caption=caption, thumb=id + '.jpg', duration=result[6], title="@SafaSelf", performer="@SafaSelf", progress=progress, progress_args=(message, "Uploading to telegram", client, hash))

    files = os.scandir('.')
    for file in files:
        if str(file).__contains__(id):
            os.remove(file)
