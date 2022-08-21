from . import _http
from . import _ws
from . import ui
from . import config
from . import contest
from .util import guess_cid, pop_element
from time import time, sleep
from os import listdir, path, sep, makedirs
from lxml import html, etree
from .config import conf
import asyncio

def submit(args):
    return asyncio.run(_submit(args))

async def _submit(args):
    cid, level = guess_cid(args)
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
    await _http.open_session()
    tokens = _http.get_tokens()
    ws_url = "wss://pubsub.codeforces.com/ws/{}/{}?_={}&tag=&time=&eventid=".format(tokens['uc'], tokens['usmc'], epoch)
    try:
        task = asyncio.create_task(_ws.message_receiver(ws_url, display_submit_result))
        url = '/contest/{}/problem/{}?csrf_token={}'.format(cid, level.upper(), tokens['csrf'])
        resp = await _http.async_post_source(url, filename, level.upper())
        doc = html.fromstring(resp)
        for e in doc.xpath('.//span[@class="error for__sourceFile"]'):
            if e.text == 'You have submitted exactly the same code before':
                print("[!] " + e.text)
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
        pop_element(i.xpath('.//div[@class="title"]')[0])
        divs = i.xpath('.//div[@class]')
        if len(divs) == 0:
            ret.append([t.strip()+'\n' for t in i.itertext()])
        else:
            l = ''
            prev = divs[0].get('class')
            lines = []
            for d in divs:
                if d.get('class') == prev:
                    l += d.text + '\n'
                else:
                    lines.append(l)
                    prev = d.get('class')
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
    doc = html.fromstring(resp)
    probs = doc.xpath('.//div[@class="problemindexholder"]')
    for p in probs:
        #if alert: alert = alert[0].text
        level = p.get('problemindex')
        typo = p.xpath('.//div[@class="ttypography"]')[0]
        title = pop_element(typo.xpath('.//div[@class="title"]')[0])
        time_limit = typo.xpath('.//div[@class="time-limit"]')[0]
        time_limit = [t for t in time_limit.itertext()][1].split(' ')[0]
        memory_limit = typo.xpath('.//div[@class="memory-limit"]')[0]
        memory_limit = [t for t in memory_limit.itertext()][1].split(' ')[0]
        desc = typo.xpath('.//div[not(@class)]')
        if desc:
            desc = '\n'.join([t for t in desc[0].itertext()])
        else:
            desc = ""

        for j in typo.xpath('.//div[@class="section-title"]'):
            pop_element(j)

        in_spec = typo.xpath('.//div[@class="input-specification"]')
        if in_spec:
            in_spec = '\n'.join([t for t in in_spec[0].itertext()])
        else:
            in_spec = ""

        out_spec = typo.xpath('.//div[@class="output-specification"]')
        if out_spec:
            out_spec = '\n'.join([t for t in out_spec[0].itertext()])
        else:
            out_spec = ""

        in_tc  = extract_testcases(typo.xpath('.//div[@class="input"]'))
        out_tc = extract_testcases(typo.xpath('.//div[@class="output"]'))
        note = typo.xpath('.//div[@class="note"]')
        ui.green('[+] ' + title)
        print('[+] Limit: {}s {} MB'.format(time_limit, memory_limit))
        print('[+] DESCRIPTION:\n{}'.format(desc))
        print('[+] INPUT SPEC:\n{}'.format(in_spec))
        print('[+] OUTPUT SPEC:\n{}'.format(out_spec))
        print('[+] INPUT EXAMPLE:\n{}'.format(in_tc))
        print('[+] OUTPUT EXAMPLE\n{}'.format(out_tc))
        if note:
            note = '\n'.join([t for t in note[0].itertext()])
            print('NOTE:', note)
        for i in in_tc:
            prob_dir = base_dir + sep + level.lower()
            makedirs(prob_dir, exist_ok=True)
            for j in range(len(in_tc)):
                fi = open(prob_dir+sep+'in'+str(j+1)+'.txt', 'w')
                fo = open(prob_dir+sep+'ans'+str(j+1)+'.txt', 'w')
                for k in in_tc[j]: fi.write(k)
                for k in out_tc[j]: fo.write(k)
