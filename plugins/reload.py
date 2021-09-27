import re
from pathlib import Path
from importlib import import_module, reload
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.handlers.handler import Handler
help = """
reload: Reload all modules
"""
@Client.on_message(filters.regex(r'^reload$', re.I) & filters.me)
async def reload_plugins(client: Client, message: Message):
    files = []
    functions = 0
    for path in sorted(Path("plugins/").rglob("*.py")):
        files.append(str(path).split('/')[1][:-3])
        module_path = '.'.join(path.parent.parts + (path.stem,))
        await reload_handlers(client, module_path, True)
        functions += (await reload_handlers(client, module_path))
    await message.edit_text("successfully reloaded {} functions from {} plugins\nloaded plugins:\n{}".format(functions, len(files), '\n'.join(files)))
async def reload_handlers(client, file, unload = False):
    functions = 0
    if unload:
        module = import_module(file)
    else: 
        module = reload(import_module(file))
    for name in vars(module).keys():
        try:
            for handler, group in getattr(module, name).handlers:
                if isinstance(handler, Handler) and isinstance(group, int):
                    if unload:
                        client.remove_handler(handler, group)
                    else:
                        client.add_handler(handler, group)
                        functions += 1
        except Exception:
            pass
    return functions
