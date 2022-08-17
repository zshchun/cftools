import ssl
import json
import asyncio
import websockets
from concurrent.futures import TimeoutError

async def message_receiver(url, callback):
    async with websockets.connect(url) as ws:
        timeout = 10
        msg = ""
        try:
            finished = 2
            ret = []
            while finished != 0:
                msg = await asyncio.wait_for(ws.recv(), timeout=timeout)
                js = json.loads(msg)
                js['text'] = json.loads(js['text'])
                ret += [js]
                finished = js['text']['d'][17]
            await callback(ret)
        except TimeoutError as e:
            if len(msg) == 0:
                print("[!] Timeout")
