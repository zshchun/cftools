from . import config
from Cryptodome.Cipher import AES
from os import path
import asyncio
import aiohttp
import gzip
import json

CF_HOST = 'https://codeforces.com'
default_headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip',
    }

session = None
tokens = {}
cookies = None

def add_header(newhdr, headers=default_headers):
    headers.update(newhdr)
    return headers

def get(url, headers=None, csrf=False):
    resp = asyncio.run(async_urlsopen([GET(url, headers, csrf)]))
    if resp:
        return resp[0]
    else:
        return None

def post(url, data, headers=None, csrf=False):
    resp = asyncio.run(async_urlsopen([POST(url, data, headers, csrf)]))
    if resp:
        return resp[0]
    else:
        return None

async def async_post_source(url, filename, level, headers=None, csrf=False):
    info = {
        'csrf_token': tokens['csrf'],
        'ftaa': tokens['ftaa'],
        'bfaa': tokens['bfaa'],
        'action': 'submitSolutionFormSubmitted',
        'submittedProblemIndex': level,
        'programTypeId': str(config.conf['prog_id']),
    }
    form = aiohttp.FormData()
    for k, v in info.items():
        form.add_field(k, v)
    form.add_field('sourceFile', open(filename, 'rb'), filename=filename)
    resp = await async_urlsopen([POST(url, form, headers, csrf)])
    if resp:
        return resp[0]
    else:
        return None

def GET(url, headers=None, csrf=False):
    return {'method':async_get, 'url':url, 'headers':headers, 'csrf':csrf}

def POST(url, data, headers=None, csrf=False):
    return {'method':async_post, 'url':url, 'data':data, 'headers':headers, 'csrf':csrf}

async def async_get(session, url, headers=None, csrf=False):
    if headers == None: headers = default_headers
    if csrf and 'csrf' in tokens:
        headers = add_header({'X-Csrf-Token': tokens['csrf']})
    if url.startswith('/'): url = CF_HOST + url
    result = None
    async with session.get(url, headers=headers) as response:
        cookies.save(file_path=config.cookies_path)
        return await response.text()

async def async_post(session, url, data, headers=None, csrf=False):
    if headers == None: headers = default_headers
    if csrf and 'csrf' in tokens:
        headers = add_header({'X-Csrf-Token': tokens['csrf']})
    if url.startswith('/'): url = CF_HOST + url
    result = None
    async with session.post(url, headers=headers, data=data) as response:
        cookies.save(file_path=config.cookies_path)
        return await response.text()

def urlsopen(urls):
    return asyncio.run(async_urlsopen(urls))

async def async_urlsopen(urls):
    async with aiohttp.ClientSession(cookie_jar=cookies) as session:
        tasks = []
        for u in urls:
            if u['method'] == async_get:
                tasks += [async_get(session, u['url'], u['headers'], u['csrf'])]
            elif u['method'] == async_post:
                tasks += [async_post(session, u['url'], u['data'], u['headers'], u['csrf'])]
        return await asyncio.gather(*tasks)

def get_tokens():
    return tokens

def update_tokens(csrf, ftaa, bfaa, uc, usmc):
    global tokens
    tokens = {'csrf':csrf[:32], 'ftaa':ftaa, 'bfaa':bfaa, 'uc':uc, 'usmc':usmc}
    with open(config.token_path, 'w') as f:
        json.dump(tokens, f)

if not cookies:
    cookies = aiohttp.CookieJar()
    if path.isfile(config.cookies_path):
        cookies.load(file_path=config.cookies_path)
    else:
        cookies.save(file_path=config.cookies_path)
    if path.isfile(config.token_path):
        with open(config.token_path, 'r') as f:
            tokens = json.load(f)
