import asyncio
from random import sample
from string import ascii_uppercase, digits


asyncio.set_event_loop(asyncio.SelectorEventLoop())
loop = asyncio.get_event_loop()
global_session_id = 'A' + ''.join(sample(ascii_uppercase + digits, k=4))

