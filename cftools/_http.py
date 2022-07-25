from . import config
from Cryptodome.Cipher import AES
#from urllib.parse import urlencode
from os import path
import asyncio
import aiohttp
import gzip

CF_DOMAIN = 'https://codeforces.com'
default_headers = {
    'Accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept-Encoding': 'gzip',
    }

session = None
csrf_token = None
cookies = None
getsolved_data = {
        'action':'getSolvedProblemCountsByContest',
        'csrf_token': csrf_token,
    }

def add_header(newhdr, headers=default_headers):
    headers.update(newhdr)
    return headers

def get(url, headers=None, csrf=False):
    resp = asyncio.run(_urlsopen([GET(url, headers, csrf)]))
    if resp:
        return resp[0]
    else:
        return None

def post(url, data, headers=None, csrf=False):
    resp = asyncio.run(_urlsopen([POST(url, data, headers, csrf)]))
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
    if csrf and csrf_token: headers = add_header({'X-Csrf-Token': csrf_token})
    if url.startswith('/'): url = CF_DOMAIN + url
    result = None
    async with session.get(url, headers=headers) as response:
        cookies.save(file_path=config.cookies_path)
        return await response.text()

async def async_post(session, url, data, headers=None, csrf=False):
    if headers == None: headers = default_headers
    if csrf and csrf_token: headers = add_header({'X-Csrf-Token': csrf_token})
    if url.startswith('/'): url = CF_DOMAIN + url
    result = None
    async with session.post(url, headers=headers, data=data) as response:
#    async with session.post(url, headers=headers, data=urlencode(data).encode()) as response:
        cookies.save(file_path=config.cookies_path)
        return await response.text()

def urlsopen(urls):
    return asyncio.run(_urlsopen(urls))

async def _urlsopen(urls):
    async with aiohttp.ClientSession(cookie_jar=cookies) as session:
        tasks = []
        for u in urls:
            if u['method'] == async_get:
                tasks += [async_get(session, u['url'], u['headers'], u['csrf'])]
            elif u['method'] == async_post:
                tasks += [async_post(session, u['url'], u['data'], u['headers'], u['csrf'])]
        return await asyncio.gather(*tasks)

def update_csrf(csrf):
    csrf_token = csrf[:32]
    open(config.csrf_path, 'w').write(csrf_token)

if not cookies:
    cookies = aiohttp.CookieJar()
    if path.isfile(config.cookies_path):
        cookies.load(file_path=config.cookies_path)
    else:
        cookies.save(file_path=config.cookies_path)
    if path.isfile(config.csrf_path):
        csrf_token = open(config.csrf_path, 'r').read(32)
