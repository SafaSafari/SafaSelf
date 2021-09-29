import re
import os
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
from pyrogram.types.user_and_chats.chat import Chat
from tqdm import tqdm
from io import StringIO
import streamlink
from pytgcalls import PyTgCalls
from pytgcalls import idle
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioVideoPiped, AudioPiped, VideoPiped

help = """
live (CHAT_ID | USERNAME) {STREAM LINK | YOUTUBE | TWITCH | MP4 | REPLY} [AO | VO]: Start live stream from mp4 OR streaming url
leave (CHAT_ID | USERNAME): Leave voice chat
"""

file = StringIO()
old = None
stop = False
call_py = {}
stream = {}


@Client.on_message(filters.regex(r'^live', re.I) & filters.me)
async def live(client: Client, message: Message):
    global file, call_py, stream
    mode = ''
    part = message.text.split(' ')
    if message.chat.type in ['supergroup', 'channel', 'group']:
        chat_id = message.chat.id
    if message.reply_to_message:
        link = message.reply_to_message.text
    if message.reply_to_message.media:
        media = message.reply_to_message.document if hasattr(message.reply_to_message.document, "file_size") else message.reply_to_message.video if hasattr(
            message.reply_to_message.video, "file_size") else message.reply_to_message.audio if hasattr(message.reply_to_message.audio, "file_size") else message.reply_to_message.voice if hasattr(message.reply_to_message.voice, "file_size") else None
        if not media:
            return
        tq = tqdm(desc="Download to Stream", total=media.file_size,
                  file=file, unit='B', unit_scale=True, mininterval=2)
        tag = "Download media to stream"
        link = await message.reply_to_message.download(progress=progress, progress_args=(message, tq, file, tag, client))
    for parameter in part:
        if parameter.__len__() == 2:
            mode = parameter
        elif parameter.__contains__('http'):
            link = parameter
        elif parameter.__len__() > 5:
            chat_id = parameter
    if not os.path.exists(link) and not link.__contains__('m3u8') and not link.__contains__('mpd'):
        streams = streamlink.streams(link)
        for key, link in dict(streams).items():
            if '720p' in key:
                break
        link = link.url
    if type(chat_id) == str:
        if chat_id[1:].isdigit():
            chat_id = int(chat_id)
        else:
            username = "@" + chat_id if chat_id[0:1] != "@" else chat_id
            chat_id = (await client.get_chat(username)).id
    stream[chat_id] = link
    if mode == 'AO':
        res = AudioPiped(stream[chat_id])
    elif mode == 'VO':
        res = VideoPiped(stream[chat_id])
    else:
        res = AudioVideoPiped(stream[chat_id])
    call_py[chat_id] = PyTgCalls(client)
    await call_py[chat_id].start()
    await call_py[chat_id].join_group_call(
        chat_id,
        res,
        stream_type=StreamType().local_stream)
    await message.edit("Live stream started")
    decor = call_py[chat_id]

    @decor.on_stream_end()
    async def end(client: PyTgCalls, update):
        if os.path.exists(stream[chat_id]):
            os.remove(stream[chat_id])
        await call_py[chat_id].leave_group_call(update.chat_id)


@Client.on_message(filters.regex(r'^leave', re.I) & filters.me)
async def leave(client: Client, message: Message):
    global call_py, stream
    if not call_py:
        return
    if message.chat.type in ['supergroup', 'channel', 'group']:
        chat_id = message.chat.id
    part = message.text.split(' ')
    if len(part) >= 2:
        chat_id = part[1]
        if type(chat_id) == str:
            if chat_id[1:].isdigit():
                chat_id = int(chat_id)
            else:
                username = "@" + chat_id if chat_id[0:1] != "@" else chat_id
                chat_id = (await client.get_chat(username)).id
    if os.path.exists(stream[chat_id]):
        os.remove(stream[chat_id])
    await call_py[chat_id].leave_group_call(chat_id)
    await message.reply_text("Live stream stopped")


@Client.on_message(filters.command('cs') & filters.me)
async def cancel(client: Client, message: Message):
    global stop
    stop = True


async def progress(current, total, message, tq, file, tag, client):
    global old, stop
    tq.update(current - (old if old else 0))
    old = current
    progress = file.getvalue()
    if stop:
        stop = False
        await message.delete()
        await client.stop_transmission()
    if progress:
        await message.edit_text("{}: {}\n/cs to cancel it!!!".format(tag, progress))
    file.truncate(0)
    file.seek(0)
