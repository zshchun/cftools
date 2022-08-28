from . import ui
from . import _http
from . import config
from . import problem
from . import contest
from .util import *
from time import time
from os import path
from lxml import html
import aiohttp
import asyncio

def submit(args):
    return asyncio.run(async_submit(args))

async def async_submit(args):
    cid, level = guess_cid(args)
    if not cid or not level:
        print("[!] Invalid contestID or level")
        return
    if args.input:
        filename = args.input
    else:
        filename = problem.select_source_code(cid, level)
    if not path.isfile(filename):
        print("[!] File not found : {}".format(filename))
        return

    print("[+] Submit {}{} : {}".format(cid, level.upper(), filename))
    epoch = int(time() * 1000)
    await _http.open_session()
    token = _http.get_tokens()
    ws_url = "wss://pubsub.codeforces.com/ws/{}/{}?_={}&tag=&time=&eventid=".format(token['uc'], token['usmc'], epoch)
    submit_form = {
        'csrf_token': token['csrf'],
        'ftaa': token['ftaa'],
        'bfaa': token['bfaa'],
        'action': 'submitSolutionFormSubmitted',
        'submittedProblemIndex': level,
        'programTypeId': str(config.conf['prog_id']),
    }
    try:
        task = asyncio.create_task(_http.websockets(ws_url, display_submit_result))
        url = '/contest/{}/problem/{}?csrf_token={}'.format(cid, level.upper(), token['csrf'])
        form = _http.add_form_data(submit_form)
        form.add_field('sourceFile', open(filename, 'rb'), filename=filename)
        resp = await _http.async_post(url, form)
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
#    submits = []
    for r in result:
        d = r['text']['d']
        submit_id = d[1]
#        if submit_id in submits: continue
#        submits.append(submit_id)
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
        elif msg == "TIME_LIMIT_EXCEEDED":
            msg = 'Time Limit Exceed'
            puts = ui.red
        elif msg == "RUNTIME_ERROR":
            msg = 'Runtime Error'
            puts = ui.blue
        else:
            puts = print
        puts("[+] [{}] {}".format(cid, msg))
        puts("[+] Test Cases {}/{}, {} ms, {} KB".format(passed, testcases, ms, mem//1024))
    if update:
        await asyncio.sleep(1.5)
        await contest.async_get_solved_count()
