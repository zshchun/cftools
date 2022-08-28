#!/usr/bin/env python3
import json
import re
import asyncio
from lxml import html, etree
from . import util
from . import _http
from . import config
from . import ui
from . import problem
from .constants import *
from .config import conf, db
from time import time, sleep
from datetime import datetime, timezone, timedelta
from os import path, listdir, system
from sys import argv, exit
from operator import itemgetter

async def async_view_submission(sid, prefix=''):
    json_path = "{}/{}-{}.json".format(path.expanduser(conf['cache_dir']), prefix, sid)
    if path.isfile(json_path):
        res = open(json_path, 'r').read()
    else:
        res = await _http.async_post("/data/submitSource", { 'submissionId':sid })
        open(json_path, 'w').write(res)
    js = json.loads(res)
    lang_ext = js['prettifyClass'][5:] if js['prettifyClass'].startswith('lang-') else js['prettifyClass']
    source_path = "{}/{}-{}.{}".format(path.expanduser(conf['cache_dir']), prefix, sid, lang_ext)
    open(source_path, 'w').write(js['source'])
    if "pager" in conf:
        system(conf["pager"] + ' "' + source_path + '"')

def get_solutions(args):
    asyncio.run(async_get_solutions(args))

async def async_get_solutions(args):
    cid, level = util.guess_cid(args)
    if not cid or not level:
        print("[!] Invalid contestID or level")
        return
    post_data = { 'action':'setupSubmissionFilter', \
            'frameProblemIndex':level.upper(), \
            'verdictName':'OK', \
            'programTypeForInvoker':'anyProgramTypeForInvoker', \
            'comparisonType':'NOT_USED', \
            'judgedTestCount':'', \
            'participantSubstring':'', \
    }
#        order = 'BY_JUDGED_DESC'
    order = 'BY_ARRIVED_ASC'
    await _http.open_session()
    try:
        for page in range(1,20):
            url = "/contest/{}/status/page/{}?order={}".format(cid, page, order)
            res = await _http.async_post(url, post_data)
            doc = html.fromstring(res)
            rows = doc.xpath('.//table[@class="status-frame-datatable"]/tr[@data-submission-id]')
            assert len(rows) > 0, "empty tr tag"
            for tr in rows:
                td = tr.xpath('.//td')
                assert len(td) > 6, "not enough td tags"
                sid = td[0].xpath('.//a[@class]')[0].text.strip()
                when = datetime.strptime(td[1].xpath('.//span')[0].text, "%b/%d/%Y %H:%M").replace(tzinfo=config.tz_msk).astimezone(tz=None).strftime('%y-%m-%d %H:%M')
                a = td[2].xpath('.//a[@href]')[0]
                user = {}
                user['profile'] = a.get('href')
                user['class'] = a.get('class').split(' ')[1]
                user['title'] = a.get('title')
                user['name'] = ''.join(a.itertext()).strip()
                c = user['class'].split('-')[1]
                name = ui.setcolor(c, user['name'].ljust(20))
                prob_title = td[3].xpath('.//a')[0].text.strip()
                level = prob_title.split('-')[0].strip()
                lang = td[4].text.strip()
                verdict = td[5].xpath('.//span[@class="verdict-accepted"]')
                verdict = verdict[0].text if verdict and verdict[0].text == 'Accepted' else None
                if not verdict or verdict != 'Accepted': continue
                ms = td[6].text.strip()
                mem = td[7].text.strip()
                print("{} {:9s} {} {:<15s} {:>7s} {:>8s} ".format(level, sid, name, lang, ms, mem), end='')
                choice = input("View? [Y/n] ").lower()
                if choice == "yes" or choice == 'y' or choice == '':
                    r = await async_view_submission(sid, str(cid)+level)
    finally:
        await _http.close_session()

def get_contest_materials(args):
    asyncio.run(async_get_contest_materials(args))

async def async_get_contest_materials(args):
    cid, _ = util.guess_cid(args)
    contest_info = get_contest_info(cid)
    if not cid or not contest_info:
        print("[!] Invalid contestID")
        return
    await _http.open_session()
    try:
        contest_url = "/contest/{}".format(cid)
        resp = await _http.async_get(contest_url)
        doc = html.fromstring(resp)
        captions = doc.xpath('.//div[@class="caption titled"]')
        for c in captions:
            title = c.text[1:].strip()
            if title != 'Contest materials':
                continue
            links = c.getparent().xpath('.//a[@href]')
            for a in links:
                print("[+] {}\n{}{}".format(a.get('title'), CF_HOST, a.get('href')))
    finally:
        await _http.close_session()

def search_editorial(args):
    asyncio.run(async_search_editorial(args))

async def async_search_editorial(args):
    cid, _ = util.guess_cid(args)
    contest_info = get_contest_info(cid)
    if not cid or not contest_info:
        print("[!] Invalid contestID")
        return
    title = re.sub(r' ?\([^)]*\)', '', contest_info[0])
    print("[+] Searching for", title, "editorial")
    await _http.open_session()
    try:
        res = await _http.async_post('/search', {'query': title + ' editorial' })
    finally:
        await _http.close_session()
    doc = html.fromstring(res)
    topics = doc.xpath('.//div[@class="topic"]')
    finding_words = [t.lower() for t in title.split()] + ['editorial']
    if not topics:
        print("[!] No result")
        return
    posts = []
    for t in topics:
        div = t.xpath('.//div[@class="title"]')
        page_title = div.a.text.strip()
        if page_title.lower().find('editorial') == -1: continue
        page_url = CF_HOST + div.xpath('.//a')[0].get('href')
        words = [t.lower() for t in page_title.split()]
        matches = sum(w in finding_words for w in words)
        posts += [{'title':page_title, 'url':page_url, 'match':matches}]

    posts.sort(key=itemgetter('match'), reverse=True)
    for p in posts:
        print("\n[+] Title: {}\n[+] URL : {}".format(p['title'], p['url']))
        if 'open_in_browser' in conf and conf['open_in_browser'] == True:
            system('''{} "{}"'''.format(conf['browser'], p['url']))

def get_contest_info(cid):
    if cid:
        cur = db.cursor()
        return cur.execute(f'''SELECT title, authors, start, length, participants, upcoming FROM codeforces WHERE cid = {cid};''').fetchone()
    else:
        return []

def show_contest_info(args):
    cid, level = util.guess_cid(args)
    if cid:
        c = get_contest_info(cid)
        if not c:
            print("[!] ContestID not found")
            return
        print("[+] Show contest info")
        if level:
            print("{} {} {}".format(cid, c[0], level.upper()))
        else:
            print("{} {}".format(cid, c[0]))
        print("{}/contest/{}".format(CF_HOST, cid))
    else:
        print("[!] ContestID is empty")

def open_url(args):
    cid, level = util.guess_cid(args)
    if not cid: return
    problems_url = "{}/contest/{}/problems".format(CF_HOST, cid)
    contest_url = "{}/contest/{}".format(CF_HOST, cid)
    print("[+] Open", contest_url)
    print("[+] Open", problems_url)
    if 'open_in_browser' in conf and conf['open_in_browser'] == True:
        system('''{} "{}" "{}"'''.format(conf['browser'], contest_url, problems_url))

def count_contests(contests):
    return len(contests.xpath('.//tr[@data-contestid]'))

def parse_list(raw_contests, upcoming=0, write_db=True):
    cur = db.cursor()
#    last_contest = cur.execute('''SELECT cid, start FROM codeforces WHERE upcoming = 0 ORDER BY start DESC;''').fetchone()
    contests = {}
#    page_overlapped = False
    for c in raw_contests.xpath('.//tr[@data-contestid]'):
        cid = int(c.get('data-contestid'))
#        if last_contest and last_contest[0] == cid: page_overlapped = True
        td = c.xpath('.//td')
        title = td[0].text.lstrip().splitlines()[0]
        authors = [{'class':a.get('class').split(' ')[1],'profile':a.get('href'),'title':a.get('title'),'name':a.text} for a in td[1].xpath('.//a')]
        start = td[2].xpath('.//span')[0].text
        start = datetime.strptime(start, "%b/%d/%Y %H:%M").replace(tzinfo=config.tz_msk)
        length = td[3].text.strip()

        if upcoming:
            participants = 0
        else:
            participants = ''.join(td[5].itertext()).strip().lstrip('x')

        contests[cid] = {'title':title, 'authors':authors, 'start':start, 'length':length, 'participants':participants, 'upcoming':0}
        if write_db:
            cur.execute('INSERT or REPLACE INTO codeforces (cid, title, authors, start, length, participants, upcoming) VALUES (?, ?, ?, ?, ?, ?, ?)', (cid, title, json.dumps(authors), start, length, participants, upcoming))
    if write_db: db.commit()
#    return page_overlapped

def parse_div(title):
    r = []
    if 'Div.' in title:
        r += ['D']
        for i in range(1, 5):
            if re.compile('Div\. ?' + str(i)).search(title): r += [str(i)]
    elif 'Global' in title:
        r += ['G']
    return r

def solved_problems():
    ret = {}
    for fn in listdir(path.expanduser(conf['solved_dir'])):
        t = path.splitext(fn)
        name = t[0]
        ext = t[1].lstrip('.')
        p = re.compile(r'^([0-9]+)([a-zA-Z])$').search(name)
        if ext and ext in conf['lang_ext'] and p and len(p.groups()) == 2:
            cid = int(p.group(1))
            level = p.group(2)
            if not cid in ret:
                ret[cid] = [level]
            else:
                ret[cid].append(level)
    return ret

async def async_get_solved_count():
    getsolved_data = { 'action':'getSolvedProblemCountsByContest' }
    solved_string = await _http.async_post("/data/contests", getsolved_data, csrf=True)
    solved_json = json.loads(solved_string)
    open(config.solved_path, 'w').write(solved_string)
    return solved_json

def show_contests(contests, show_all=False, upcoming=False, solved_json=None):
    total_contests = 0;
    solved_contests = 0
    for c in contests:
        puts = print
        total_contests += 1
        cid = c[0]
        title = c[1]
        div = ''.join(parse_div(title))
        start = datetime.strptime(c[3], '%Y-%m-%d %H:%M:%S%z').astimezone(tz=None)
        length = c[4]
        countdown = ''
        if upcoming:
            length_secs = int(length.split(':')[0])*3600 + int(length.split(':')[1])*60
            if start > datetime.now().astimezone(tz=None):
                d = start - datetime.now().astimezone(tz=None)
                h = d.seconds // 3600
                m = d.seconds // 60 % 60
                countdown = ' {:02}d+{:02d}:{:02d}'.format(d.days, h, m)
            elif (datetime.now().astimezone(tz=None)-start).seconds < length_secs:
                d = start - datetime.now().astimezone(tz=None)
                t = d.seconds + length_secs
                h = t // 3600
                m = t // 60 % 60
                countdown = '    -{:02d}:{:02d}'.format(h, m)
            else:
                countdown = '       END'
            participants = ''
            weekday = start.strftime(' %a')
        else:
            participants = ('x'+str(c[5])).rjust(7, ' ')
            weekday = ''

        if solved_json and str(cid) in solved_json['solvedProblemCountsByContestId'] and str(cid) in solved_json['problemCountsByContestId']:
            solved_cnt = solved_json['solvedProblemCountsByContestId'][str(cid)]
            prob_cnt = solved_json['problemCountsByContestId'][str(cid)]
            solved_str = "{:d}/{:d} ".format(solved_cnt, prob_cnt)
            if len(div) > 0 and solved_cnt > 0 and (solved_cnt == prob_cnt or solved_cnt >= conf['contest_goals'][div[-1]]):
                solved_contests += 1
                if not show_all and conf['hide_solved_contest']:
                    puts = lambda *args: None
                else:
                    puts = ui.green
        elif solved_json:
            solved_str = "    "
        else:
            solved_str = ""

        if not show_all and conf['only_goals'] and (len(div) == 0 or conf['contest_goals'][div[-1]] == 0):
            puts = lambda *args: None
        contest_info = "{:04d} {:<3} {}{:<{width}} {} ({}){}{}{}".format(cid, div, solved_str, title[:conf['title_width']], start.strftime("%Y-%m-%d %H:%M"), length, weekday, countdown, participants, width=conf['title_width'])
        puts(contest_info)
    if not upcoming:
        print("[+] Solved {:d}/{:d} contests".format(solved_contests, total_contests))

def list_contest(args, upcoming=False):
    asyncio.run(async_list_contest(args, upcoming))

async def async_list_contest(args, upcoming=False):
    solved_json = None
    cur = db.cursor()
    if args.force:
        update = True;
    else:
        update = False;
#    last_modified = int(cur.execute('''SELECT strftime('%s', last_modified) FROM modifications WHERE site = 'codeforces';''').fetchone()[0])
    now = int(time())
    row_count = cur.execute('''SELECT COUNT(*) FROM codeforces''').fetchone()[0]
#    if now - last_modified > 24 * 3600 * 7 or row_count == 0:
    if row_count == 0:
        update = True
    else:
        contests = cur.execute('''SELECT start, length FROM codeforces WHERE upcoming = 1 ORDER BY start;''')
        for start, length in contests:
            duration = timedelta(hours=int(length.split(':')[0])+1, minutes=int(length.split(':')[1]))
            contest_end = (datetime.strptime(start, '%Y-%m-%d %H:%M:%S%z').astimezone(tz=None) + duration)
            now = datetime.now().astimezone(tz=None)
            if contest_end < now:
                update = True

    await _http.open_session()
    if ('solved' in args and args.solved) or not path.isfile(config.solved_path):
        solved_json = await async_get_solved_count()
    else:
        with open(config.solved_path, 'r') as f:
            solved_json = json.load(f)

    if update:
        print('[+] Update contests list')
        urls = []
        for page in range(1, conf['max_page']+1):
            urls += [_http.GET('/contests/page/{:d}'.format(page))]
        pages = await _http.async_urlsopen(urls)
        for page in pages:
            doc = html.fromstring(page)
            table = doc.xpath('.//div[@class="datatable"]')
            if count_contests(table[1]) == 0:
                print("[!] Contest is running")
                break
            parse_list(table[0], upcoming=1, write_db=True)
            parse_list(table[1], write_db=True)
    await _http.close_session()

    if upcoming:
        print("[+] Current or upcoming contests")
        upcoming = cur.execute('''SELECT cid, title, authors, start, length, participants FROM codeforces WHERE upcoming = 1 ORDER BY start;''')
        show_contests(upcoming, show_all=args.all, upcoming=True)
    else:
        print("[+] Past contests")
        contests = cur.execute('''SELECT cid, title, authors, start, length, participants FROM codeforces WHERE upcoming = 0 ORDER BY start;''')
        show_contests(contests, show_all=args.all, solved_json=solved_json)

def list_past_contest(args):
    list_contest(args, upcoming=False)

def list_upcoming(args):
    list_contest(args, upcoming=True)

def race_contest(args):
    if 'cid' in args and args.cid:
        cid = int(args.cid)
    else:
        print("[!] Invalid contestID")
        return
    c = get_contest_info(cid)
    if not c:
        print("[!] Contest not found")
        return
    if not c[5]:
        print("[!] {} {} is not upcoming contest".format(cid, c[0]))
        return
    start = datetime.strptime(c[2], '%Y-%m-%d %H:%M:%S%z').astimezone(tz=None)
    now = datetime.now().astimezone(tz=None)
    if now > start:
        print("[!] {} {} is past contest".format(cid, c[0]))
        return
    print()
    while now < start:
        delta = int((start-now).total_seconds())
        h = delta // 3600
        m = delta // 60 % 60
        s = delta % 60
        fmt = ui.setcolor('green', " {:d}:{:02d}:{:02d}".format(h, m, s))
        ui.redraw(fmt)
        sleep(0.2)
        now = datetime.now().astimezone(tz=None)
    problem.parse_problems(args)

def register(args):
    asyncio.run(async_register(args))

async def async_register(args):
    if not 'cid' in args or not args.cid:
        print("[!] Select a contestID")
        return
    try:
        await _http.open_session()
        print("[+] Registration for the contestID", args.cid)
        url = 'https://codeforces.com/contestRegistration/' + str(args.cid)
        resp = await _http.async_get(url)
        doc = html.fromstring(resp)
        title = doc.xpath('.//title')[0].text
        print(title)
        msg = util.show_message(resp)
        if msg:
            print('[!]', msg)
            return
        terms = doc.xpath('.//textarea[@class="terms" and @id="registrationTerms"]')[0].text
        print(terms)
        choice = input("Take part as individual participant? [y/N] ").lower()
        if not choice in ['y', 'yes']: return
        token = _http.get_tokens()
        register_form = {
            'csrf_token': token['csrf'],
            'action': 'formSubmitted',
            'takePartAs': 'personal',
            'backUrl': '',
        }
        form = _http.add_form_data(register_form)
        resp = await _http.async_post(url, form)
        msg = util.show_message(resp)
        if msg: print('[+]', msg)
    finally:
        await _http.close_session()
