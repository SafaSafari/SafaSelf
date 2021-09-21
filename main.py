
import os
import re
import json
import sys
import importlib
from pyrogram import Client
from pyrogram.client import Client
from pyrogram.types.messages_and_media.message import Message
from pyrogram import filters
import config

client = Client('user', config.API_ID, config.API_HASH)

sys.path.insert(1, 'plugins')
modules = []
plugin_files = []
for file in os.listdir('plugins'):
    if os.path.isdir(file):
        continue
    split = file.split('.')
    plugin_files.append(split[0])
    plugin = importlib.import_module(split[0])
    plugin.setClient(client)
    modules.append(plugin)


@client.on_message(filters.regex('^reload$', re.I) & filters.user("me"))
async def reload(client: Client, message: Message):
    global modules
    for plugin_file in os.listdir('plugins'):
        if os.path.isdir(plugin_file):
            continue
        plugin_file = plugin_file.split('.')[0]
        if not plugin_file in plugin_files:
            plugin_files.append(plugin_file)
            modules.append(importlib.import_module(plugin_file))
    for module in modules:
        plugin = importlib.reload(module)
        plugin.setClient(client)
    await message.edit_text("Reloaded successfully\n{} Plugins loaded\n{}".format(len(plugin_files), '\n'.join(plugin_files)))


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


@client.on_message(filters.regex('^version$', re.I) & filters.user("me"))
async def version(client: Client, message: Message):
    await message.edit("SafaSelf\n[Source](https://github.com/SafaSafari/SafaSelf)\nVersion 1.3")


async def parse(item: dict):
    ret = {}
    for i, j in item.items():
        if type(j) == dict:
            ret["`{}`".format(i)] = await parse(j)
        else:
            ret["`{}`".format(i)] = "`{}`".format(j)
    return ret

client.run()
