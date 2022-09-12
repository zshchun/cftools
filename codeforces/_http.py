from . import config
from .constants import *
from lxml import html, etree
from os import path
import asyncio
import aiohttp
import pyaes
import json
import re

default_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip',
    }

session = None
tokens = {}
cookie_jar = None

class RCPCRedirectionError(Exception):
    def __init__(self):
        super().__init__("RCPC redirection detected")

def add_header(newhdr, headers=default_headers):
    headers.update(newhdr)
    return headers

def get(url, headers=None, csrf=False):
    resp = asyncio.run(async_get(url, headers, csrf))
    if resp:
        return resp[0]
    else:
        return None

def post(url, data, headers=None, csrf=False):
    resp = asyncio.run(async_post(url, data, headers, csrf))
    if resp:
        return resp[0]
    else:
        return None

def GET(url, headers=None, csrf=False):
    return {'method':async_get, 'url':url, 'headers':headers, 'csrf':csrf}

def POST(url, data, headers=None, csrf=False):
    return {'method':async_post, 'url':url, 'data':data, 'headers':headers, 'csrf':csrf}

def check_rcpc(html_data):
    doc = html.fromstring(html_data)
    aesmin = doc.xpath(".//script[@type='text/javascript' and @src='/aes.min.js']")
    if len(aesmin) > 0:
        print("[+] RCPC redirection detected")
        js = doc.xpath(".//script[not(@type)]")
        assert len(js) > 0
        keys = re.findall(r'[abc]=toNumbers\([^\)]*', js[0].text)
        for k in keys:
            if k[0] == 'a':
                key = bytes.fromhex(k.split('"')[1])
            elif k[0] == 'b':
                iv = bytes.fromhex(k.split('"')[1])
            elif k[0] == 'c':
                ciphertext = bytes.fromhex(k.split('"')[1])
        assert len(key) == 16 and len(iv) == 16 and len(ciphertext) == 16, 'AES decryption error'
        c = pyaes.AESModeOfOperationCBC(key, iv=iv)
        plaintext = c.decrypt(ciphertext)
        rcpc = plaintext.hex()
        cookie = { 'RCPC':rcpc }
        cookie_jar.update_cookies(cookie)
        cookie_jar.save(file_path=config.cookie_path)
        raise RCPCRedirectionError()

async def async_get(url, headers=None, csrf=False):
    if headers == None: headers = default_headers
    if csrf and 'csrf' in tokens:
        headers = add_header({'X-Csrf-Token': tokens['csrf']})
    if url.startswith('/'): url = CF_HOST + url
    result = None
    try:
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            check_rcpc(await response.text())
            cookie_jar.save(file_path=config.cookie_path)
            return await response.text()
    except RCPCRedirectionError:
        async with session.get(url, headers=headers) as response:
            assert response.status == 200
            cookie_jar.save(file_path=config.cookie_path)
            return await response.text()

async def async_post(url, data, headers=None, csrf=False):
    if headers == None: headers = default_headers
    if csrf and 'csrf' in tokens:
        headers = add_header({'X-Csrf-Token': tokens['csrf']})
    if url.startswith('/'): url = CF_HOST + url
    result = None
    try:
        async with session.post(url, headers=headers, data=data) as response:
            assert response.status == 200
            check_rcpc(await response.text())
            cookie_jar.save(file_path=config.cookie_path)
            return await response.text()
    except RCPCRedirectionError:
        async with session.post(url, headers=headers, data=data) as response:
            assert response.status == 200
            cookie_jar.save(file_path=config.cookie_path)
            return await response.text()

def urlsopen(urls):
    return asyncio.run(async_urlsopen(urls))

async def async_urlsopen(urls):
    tasks = []
    for u in urls:
        if u['method'] == async_get:
            tasks += [async_get(u['url'], u['headers'], u['csrf'])]
        elif u['method'] == async_post:
            tasks += [async_post(u['url'], u['data'], u['headers'], u['csrf'])]
    return await asyncio.gather(*tasks)

async def on_request_start(session, trace_request_ctx, params):
    trace_request_ctx.start = asyncio.get_event_loop().time()
    print(session)
    print("[*] Request start : {}".format(params))

async def on_request_chunk_sent(session, trace_request_ctx, params):
    print("[*] Request sent chunk : {}".format(params.chunk))

async def on_request_end(session, trace_request_ctx, params):
    elapsed = asyncio.get_event_loop().time() - trace_request_ctx.start
    print("[*] Request end : {}".format(elapsed))

async def open_session():
    global session, tokens, cookie_jar
    cookie_jar = aiohttp.CookieJar()
    if path.isfile(config.cookie_path):
        cookie_jar.load(file_path=config.cookie_path)
    else:
        cookie_jar.save(file_path=config.cookie_path)
    if path.isfile(config.token_path):
        with open(config.token_path, 'r') as f:
            tokens = json.load(f)
    if config.conf['trace_requests']:
        trace_config = [aiohttp.TraceConfig()]
        trace_config[0].on_request_start.append(on_request_start)
        trace_config[0].on_request_chunk_sent.append(on_request_chunk_sent)
        trace_config[0].on_request_end.append(on_request_end)
    else:
        trace_config = []
    if session == None:
        session = await aiohttp.ClientSession(cookie_jar=cookie_jar, trace_configs=trace_config).__aenter__()

async def close_session():
    global session, tokens, cookie_jar
    await session.__aexit__(None, None, None)
    tokens = {}
    cookie_jar = {}
    session = None

def get_tokens():
    return tokens

def update_tokens(csrf, ftaa, bfaa, uc, usmc):
    global tokens
    tokens = {'csrf':csrf[:32], 'ftaa':ftaa, 'bfaa':bfaa, 'uc':uc, 'usmc':usmc}
    with open(config.token_path, 'w') as f:
        json.dump(tokens, f)

async def websockets(url, callback):
    async with session.ws_connect(url) as ws:
        finished = 2
        ret = []
        async for msg in ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                js = json.loads(msg.data)
                js['text'] = json.loads(js['text'])
                ret += [js]
                finished = js['text']['d'][17]
                if finished == 0:
                    break
            else:
                break;
        await callback(ret)

def add_form_data(form_data):
    form = aiohttp.FormData()
    for k, v in form_data.items():
        form.add_field(k, v)
    return form
