from http.cookiejar import CookieJar
from urllib.request import build_opener, HTTPCookieProcessor
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from Cryptodome.Cipher import AES

CF_DOMAIN = 'https://codeforces.com'
default_headers = {
    'Accept': '*/*',
    'content-type':
    'application/x-www-form-urlencoded',
    }

opener = None

def get(path, headers=None):
    if headers == None: headers = default_headers
    if path.startswith('/'): path = CF_DOMAIN + path
    req = Request(path, headers=default_headers);
    result = None
    with opener.open(req) as response:
        result = response.read()
    return result.decode('utf-8')

def post(path, data, headers=None):
    if headers == None: headers = default_headers
    if path.startswith('/'): path = CF_DOMAIN + path
    req = Request(path, headers=default_headers, data=urlencode(data).encode())
    result = None
    with opener.open(req) as response:
        result = response.read()
    return result.decode('utf-8')

if not opener:
    cookies = CookieJar()
    opener = build_opener(HTTPCookieProcessor(cookies))
