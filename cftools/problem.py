from . import util
from . import _http
from . import _ws
from . import color
from .contest import get_solved_count
from time import time, sleep
from os import listdir, path
from bs4 import BeautifulSoup
from .config import conf

def submit(args):
    cid, level = util.guess_cid(args)
    if not cid or not level:
        print("[!] Invalid contestID or level")
        return
    if args.input:
        filename = args.input
        if not path.isfile(filename):
            print("[!] File not found : {}".format(filename))
            return
    else:
        exts = [k['ext'] for k in conf['lang']]
        if not exts: return
        filename = [f for f in listdir('.') if path.isfile(f) and path.splitext(f)[1].lstrip('.') in exts]
        if len(filename) == 0:
            print("[!] File not found")
            return
        elif len(filename) >= 2:
            print("[!] There are multiple solutions. Select one of solutions. (-i)")
            return
        filename = filename[0]
    print("[+] Submit {}{} : {}".format(cid, level.upper(), filename))

    epoch = int(time() * 1000)
    tokens = _http.get_tokens()
    url = '/contest/{}/problem/{}?csrf_token={}'.format(cid, level.upper(), tokens['csrf'])
    resp = _http.post_source(url, filename, level.upper())
    bs = BeautifulSoup(resp, 'html.parser')
    err = bs.find("span", {"class": "error"})
    if err and err.text == 'You have submitted exactly the same code before':
        print("[!] You have submitted exactly the same code before")
    else:
        ws_url = "wss://pubsub.codeforces.com/ws/{}/{}?_={}&tag=&time=&eventid=".format(tokens['uc'], tokens['usmc'], epoch)
        resp = _ws.recv(ws_url)
        update = False
        submits = []
        for r in resp:
            d = r['text']['d']
            submit_id = d[1]
            if submit_id in submits:
                continue
            submits.append(submit_id)
            cid = d[2]
            title = d[4] # "TESTS"
            msg = d[6]
            passed = d[7]
            testcases = d[8]
            ms = d[9]
            mem = d[10]
            date1 = d[13]
            date2 = d[14]
            lang_id = d[16]
            if msg == "OK":
                puts = color.green
                msg = 'Accepted'
                update = True
            elif msg == "WRONG_ANSWER":
                msg = 'Wrong Answer'
                puts = color.red
            else:
                puts = print
            puts("[+] [{}] {}".format(cid, msg))
            puts("[+] Test Cases {}/{}, {} ms, {} KB".format(passed, testcases, ms, mem//1024))
        if update:
            sleep(0.5)
            get_solved_count()
