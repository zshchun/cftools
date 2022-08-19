from . import util
from . import _http
from . import _ws
from . import ui
from . import config
from . import contest
from time import time, sleep
from os import listdir, path, sep, makedirs
from bs4 import BeautifulSoup
from .config import conf
import asyncio

def submit(args):
    return asyncio.run(_submit(args))

async def _submit(args):
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
    ws_url = "wss://pubsub.codeforces.com/ws/{}/{}?_={}&tag=&time=&eventid=".format(tokens['uc'], tokens['usmc'], epoch)
    await _http.open_session()
    try:
        task = asyncio.create_task(_ws.message_receiver(ws_url, display_submit_result))
        url = '/contest/{}/problem/{}?csrf_token={}'.format(cid, level.upper(), tokens['csrf'])
        resp = await _http.async_post_source(url, filename, level.upper())
        bs = BeautifulSoup(resp, 'html.parser')
        err = bs.find("span", {"class": "error"})
        if err and err.text == 'You have submitted exactly the same code before':
            print("[!] You have submitted exactly the same code before")
            return
        await task
    finally:
        await _http.close_session()

async def display_submit_result(result):
    update = False
    submits = []
    for r in result:
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
            puts = ui.green
            msg = 'Accepted'
            update = True
        elif msg == "WRONG_ANSWER":
            msg = 'Wrong Answer'
            puts = ui.red
        else:
            puts = print
        puts("[+] [{}] {}".format(cid, msg))
        puts("[+] Test Cases {}/{}, {} ms, {} KB".format(passed, testcases, ms, mem//1024))
    if update:
        await asyncio.sleep(0.5)
        await contest.async_get_solved_count()

def extract_testcases(tags):
    ret = []
    for i in tags:
        i.find('div', {'class':"title"}).decompose()
        divs = i.find_all('div', {'class':True})
        if len(divs) == 0:
            ret.append([i.text.strip()+'\n'])
        else:
            l = ''
            prev = divs[0]['class']
            lines = []
            for d in divs:
                if d['class'] == prev:
                    l += d.text + '\n'
                else:
                    lines.append(l)
                    prev = d['class']
                    l = d.text + '\n'
            if l: lines.append(l.strip()+'\n')
            ret.append(lines)
    return ret

def parse_problems(args):
    asyncio.run(async_parse_problems(args))

async def async_parse_problems(args):
    if 'cid' in args and args.cid:
        cid = int(args.cid)
    else:
        print("[!] Invalid contestID")
        return
    url = "/contest/{}/problems".format(cid)
    await _http.open_session()
    resp = await _http.async_get(url)
    await _http.close_session()
    base_dir = path.expanduser(config.conf['contest_dir'] + sep + str(cid))
    makedirs(base_dir, exist_ok=True)
    bs = BeautifulSoup(resp, 'html.parser')
    probs = bs.find_all('div', {'class':'problemindexholder', 'problemindex':True})
    for p in probs:
        alert = p.find('div', {'class':'alert'})
        level = p['problemindex']
        typo = p.find('div', {'class':'ttypography'})
        title = typo.find('div', {'class':'title'}).extract().text
        time_limit = typo.find('div', {'class':'time-limit'}).div.next.next.replace(' seconds', 's').replace(' second', 's')
        memory_limit = typo.find('div', {'class':'memory-limit'}).div.next.next.replace(' megabytes', 'MB')
        desc = typo.find('div', {'class':False}).get_text()
        in_spec = typo.find('div', {'class':'input-specification'})
        in_spec.find('div', {'class':"section-title"}).decompose()
        in_spec = in_spec.get_text()
        out_spec = typo.find('div', {'class':'output-specification'})
        out_spec.find('div', {'class':"section-title"}).decompose()
        out_spec = out_spec.get_text()
        ins = extract_testcases(typo.find_all('div', {'class':'input'}))
        outs = extract_testcases(typo.find_all('div', {'class':'output'}))
        note = typo.find('div', {'class':'note'})
        ui.green('[+] ' + title)
        print('Limit: {} {}'.format(time_limit, memory_limit))
        print('DESC:', desc)
        print('INPUT SPEC:', in_spec)
        print('OUTPUT SPEC:', out_spec)
        print('INPUTS:' , ins)
        print('OUTPUTS:' , outs)
        if note:
            note.find('div', {'class':"section-title"}).decompose()
            note = note.text
            print('NOTE:', note)
        for i in ins:
            prob_dir = base_dir + sep + level.lower()
            makedirs(prob_dir, exist_ok=True)
            for j in range(len(ins)):
                fi = open(prob_dir+sep+'in'+str(j+1)+'.txt', 'w')
                fo = open(prob_dir+sep+'ans'+str(j+1)+'.txt', 'w')
                for k in ins[j]: fi.write(k)
                for k in outs[j]: fo.write(k)
