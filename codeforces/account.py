from . import _http
from .ui import *
from random import choice
from getpass import getpass
from lxml import html, etree
import asyncio

def check_login(html_data):
    doc = html.fromstring(html_data)
    captions = doc.xpath('.//div[@class="caption titled"]')
    for c in captions:
        titled = c.text.strip()
        if titled == 'Login into Codeforces':
            return False
    return True

def extract_channel(html_data):
    doc = html.fromstring(html_data)
    uc = doc.xpath('.//meta[@name="uc"]')
    uc = uc[0].get('content') if len(uc) > 0 else None
    usmc = doc.xpath('.//meta[@name="usmc"]')
    usmc = usmc[0].get('content') if len(usmc) > 0 else None
    cc = doc.xpath('.//meta[@name="cc"]')
    cc = cc[0].get('content') if len(cc) > 0 else None
    pc = doc.xpath('.//meta[@name="pc"]')
    pc = pc[0].get('content') if len(pc) > 0 else None
    return uc, usmc, cc, pc

def login(args):
    asyncio.run(async_login(args))

async def async_login(args):
    print('[+] Login account')
    login_url = "/enter?back=%2F"
    handle = input("Input handle or email: ")
    passwd = getpass()
    await _http.open_session()
    html_data = await _http.async_get(login_url)
    doc = html.fromstring(html_data)
    csrf_token = doc.xpath('.//span[@class="csrf-token"]')[0].get('data-csrf')
    assert len(csrf_token) == 32, "Invalid CSRF token"
    ftaa = ''.join([choice('abcdefghijklmnopqrstuvwxyz0123456789') for x in range(18)])
# bfaa : Fingerprint2.x64hash128
    bfaa = ''.join([choice('0123456789abcdef') for x in range(32)])
    login_data = {
        'csrf_token': csrf_token,
        'action': 'enter',
        'ftaa': ftaa,
        'bfaa': bfaa,
        'handleOrEmail': handle,
        'password': passwd,
        'remember': 'on',
    }
    html_data = await _http.async_post(login_url, login_data)
    await _http.close_session()
    if check_login(html_data):
        print(GREEN("[+] Login successful"))
        uc, usmc, _, _ = extract_channel(html_data)
        _http.update_tokens(csrf_token, ftaa, bfaa, uc, usmc)
    else:
        print(RED("[!] Login failed"))
