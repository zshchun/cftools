from . import _http
from random import choice
from getpass import getpass
from bs4 import BeautifulSoup

def check_login(html_data):
    bs = BeautifulSoup(html_data, 'html.parser')
    titled = bs.find('div', {'class':'caption titled'}).text.strip()
    if titled == 'Login into Codeforces':
        return False
    else:
        return True

def extract_channel(html_data):
    bs = BeautifulSoup(html_data, 'html.parser')
    uc = bs.find("meta", {"name": "uc", "content": True})
    if uc: uc = uc['content']
    usmc = bs.find("meta", {"name": "usmc", "content": True})
    if usmc: usmc = usmc['content']
    cc = bs.find("meta", {"name": "cc", "content": True})
    if cc: cc = cc['content']
    pc = bs.find("meta", {"name": "pc", "content": True})
    if pc: pc = pc['content']
    return uc, usmc, cc, pc

def login(args):
    print('[+] Login account')
    login_url = _http.CF_DOMAIN + "/enter?back=%2F"
    handle = input("Input handle or email: ")
    passwd = getpass()
    html_data = _http.get(login_url)
    bs = BeautifulSoup(html_data, 'html.parser')
    csrf_token = bs.find("span", {"class": "csrf-token", 'data-csrf':True})['data-csrf']
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
    html_data = _http.post(login_url, login_data)
    if check_login(html_data):
        print("[+] Login successful")
        uc, usmc, _, _ = extract_channel(html_data)
        _http.update_tokens(csrf_token, ftaa, bfaa, uc, usmc)
    else:
        print("[!] Login failed")
