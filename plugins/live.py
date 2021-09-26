import re
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
import streamlink
from pytgcalls import PyTgCalls
from pytgcalls import idle
from pytgcalls import StreamType
from pytgcalls.types.input_stream import AudioVideoPiped



@Client.on_message(filters.regex('^live', re.I) & filters.user("me"))
async def live(client: Client, message: Message):
    call_py = PyTgCalls(client)
    await call_py.start()
    part = message.text.split(' ')
    if len(part) == 3:
        stream = part[2]
        chat_id = part[1]
    elif len(part) == 2 and message.reply_to_message:
        stream = message.reply_to_message.text
        chat_id = part[1]
    if not stream.__contains__('m3u8') and not stream.__contains__('mpd'):
        streams = streamlink.streams(stream)
        for key, stream in dict(streams).items():
            if '720p' in key:
                break
        stream = stream.url
    if chat_id[1:].isnumeric():
        chat_id = int(chat_id)
    await call_py.join_group_call(
        chat_id,
        AudioVideoPiped(stream),
        stream_type=StreamType().local_stream)
    await message.edit("Live stream started")

    @Client.on_message(filters.regex('^leave$', re.I) & filters.user("me"))
    async def leave(client: Client, message: Message):
        await call_py.leave_group_call(chat_id)
        await message.edit("Live stream stopped")

    @Client.on_message(filters.regex('^change', re.I) & filters.user("me"))
    async def pause(client: Client, message: Message):
        part = message.text.split(' ')
        if len(part) == 2:
            stream = part[1]
        elif message.reply_to_message:
            stream = message.reply_to_message.text
        if not stream.__contains__('m3u8') and not stream.__contains__('mpd'):
            streams = streamlink.streams(stream)
            for key, stream in dict(streams).items():
                if '720p' in key:
                    break
            stream = stream.url
            await call_py.change_stream(chat_id, AudioVideoPiped(stream), stream_type=StreamType().local_stream)
            await message.edit("Live stream changed")
