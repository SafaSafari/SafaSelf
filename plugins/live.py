import re
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
import streamlink
from pytgcalls import PyTgCalls
from pytgcalls import idle
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioVideoPiped, AudioPiped, VideoPiped

help = """
live (CHAT_ID | USERNAME) {STREAM LINK | YOUTUBE | TWITCH | MP4 | REPLY} [AO | VO]: Start live stream from mp4 OR streaming url
leave (CHAT_ID | USERNAME): Leave voice chat
"""

chat_id = 0
@Client.on_message(filters.regex(r'^live', re.I) & filters.me)
async def live(client: Client, message: Message):
    global chat_id
    call_py = PyTgCalls(client)
    await call_py.start()
    mode = ''
    stream = ''
    part = message.text.split(' ')
    if message.chat.type in ['supergroup', 'channel', 'group']:
        chat_id = message.chat.id
    if message.reply_to_message:
        stream = message.reply_to_message.text
    for parameter in part:
        if parameter.__len__() == 2:
            mode = parameter
        elif parameter.__contains__('http'):
            stream = parameter
        elif parameter.__len__()> 5:
            chat_id = parameter
    if not stream.__contains__('m3u8') and not stream.__contains__('mpd'):
        streams = streamlink.streams(stream)
        for key, stream in dict(streams).items():
            if '720p' in key:
                break
        stream = stream.url
    print(chat_id)
    if type(chat_id) == str and chat_id[1:].isnumeric():
        chat_id = int(chat_id)
    if mode == 'AO':
        res = AudioPiped(stream)
    elif mode == 'VO':
        res = VideoPiped(stream)
    else:
        res = AudioVideoPiped(stream)
    await call_py.join_group_call(
        chat_id,
        res,
        stream_type=StreamType().local_stream)
    await message.edit("Live stream started")
    @client.on_message(filters.regex(r'^leave', re.I) & filters.me)
    async def leave(client: Client, message: Message):
        global chat_id
        if message.chat.type in ['supergroup', 'channel', 'group']:
            chat_id = message.chat.id
        part = message.text.split(' ')
        if len(part) >= 2:
            chat_id = part[1]
            if type(chat_id) == str and chat_id[1:].isnumeric():
                chat_id = int(chat_id)
        await call_py.leave_group_call(chat_id)
        await message.reply_text("Live stream stopped")
