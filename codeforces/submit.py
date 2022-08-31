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

        status = parse_submit_status(resp)
        assert status[0]['url'].split('/')[-1] == level.upper()
        submission_id = status[0]['id']
        done, pending = await asyncio.wait([task], timeout=5)
        if pending:
            while True:
                status_url = '/contest/{}/my'.format(cid, token['csrf'])
                resp = await _http.async_get(status_url)
                status = parse_submit_status(resp)
                status = [st for st in status if st['id'] == submission_id][0]
                if ' '.join(status['verdict'].split()[:2]) in ['Wrong answer', 'Runtime error', 'Time limit', 'Hacked', 'Idleness limit', 'Memory limit']:
                    ui.red(status['verdict'])
                    print("{}, {}".format(status['time'], status['mem']))
                    break
                elif status['verdict'].startswith('Wrong Answer'):
                    ui.green(status['verdict'])
                    print("{}, {}".format(status['time'], status['mem']))
                    break
                else:
                    print("Status:", status['verdict'])
                await asyncio.sleep(3)
    finally:
        await _http.close_session()

def parse_submit_status(html_page):
    ret = []
    doc = html.fromstring(html_page)
    tr = doc.xpath('.//table[@class="status-frame-datatable"]/tr[@class="last-row"]')
    for t in tr:
        td = t.xpath('.//td')
        submission_id = ''.join(td[0].itertext()).strip()
        url = td[3].xpath('.//a[@href]')[0].get('href')
        verdict = ''.join(td[5].itertext()).strip()
        prog_time = td[6].text.strip().replace('\xa0', ' ')
        prog_mem = td[7].text.strip().replace('\xa0', ' ')
        ret.append({ 'id':submission_id, 'url':url, 'verdict':verdict, 'time':prog_time, 'mem':prog_mem })
    return ret


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
