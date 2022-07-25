from . import config
from http.cookiejar import CookieJar, MozillaCookieJar, Cookie
from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from Cryptodome.Cipher import AES
from os import path
import gzip

CF_DOMAIN = 'https://codeforces.com'
default_headers = {
    'Accept': '*/*',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept-Encoding': 'gzip',
    }

opener = None
csrf_token = None

def add_header(newhdr, headers=default_headers):
    headers.update(newhdr)
    return headers

def get(path, headers=None, csrf=False):
    return request(path, headers=headers, csrf=csrf)

def post(path, data, headers=None, csrf=False):
    return request(path, data=data, headers=headers, csrf=csrf)

def request(path, data=None, headers=None, csrf=False):
    if headers == None: headers = default_headers
    if csrf and csrf_token: headers = add_header({'X-Csrf-Token': csrf_token})
    if path.startswith('/'): path = CF_DOMAIN + path
    if data:
        req = Request(path, headers=default_headers, data=urlencode(data).encode())
    else:
        req = Request(path, headers=default_headers);
    result = None
    with opener.open(req) as response:
        if response.headers.get('Content-Encoding') == 'gzip':
            result = gzip.decompress(response.read())
        else:
            result = response.read()
        cookies.save()
    return result.decode('utf-8')

def update_csrf(csrf):
    csrf_token = csrf[:32]
    open(config.csrf_path, 'w').write(csrf_token)

if not opener:
    cookies = MozillaCookieJar(config.cookies_path)
    if path.isfile(config.cookies_path):
        cookies.load()
    else:
        cookies.save()
    opener = build_opener(HTTPCookieProcessor(cookies))
    if path.isfile(config.csrf_path):
        csrf_token = open(config.csrf_path, 'r').read(32)
