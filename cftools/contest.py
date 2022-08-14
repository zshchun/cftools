#!/usr/bin/env python3
import json
import logging
import re
from . import util
from . import _http
from . import config
from .color import setcolor
from .config import conf, db
from time import time
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from os import path, listdir, system
from sys import argv, exit
from operator import itemgetter

def view_submission(sid, prefix=''):
    json_path = "{}/{}-{}.json".format(path.expanduser(conf['cache_dir']), prefix, sid)
    if path.isfile(json_path):
        res = open(json_path, 'r').read()
    else:
        res = _http.post("/data/submitSource", { 'submissionId':sid })
        open(json_path, 'w').write(res)
    print("[+] Cached:", json_path)
    js = json.loads(res)
    lang_ext = js['prettifyClass'][5:] if js['prettifyClass'].startswith('lang-') else js['prettifyClass']
    source_path = "{}/{}-{}.{}".format(path.expanduser(conf['cache_dir']), prefix, sid, lang_ext)
    open(source_path, 'w').write(js['source'])
    if "pager" in conf:
        print("[+] View source:", source_path)
        system(conf["pager"] + ' "' + source_path + '"')

def get_solutions(args):
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
    page = 1
    url = "/contest/{}/status/page/{}?order={}".format(cid, page, order)
    res = _http.post(url, post_data)
    bs = BeautifulSoup(res, 'html.parser')
    table = bs.find("table", {"class": "status-frame-datatable"})
    tr = table.find_all("tr", {"data-submission-id": True})
    assert len(tr) > 0, "empty tr tag"
    for t in tr:
        td = t.find_all("td")
        assert len(td) > 6, "not enough td tags"
#        url = _http.CF_DOMAIN + td[0].find('a', href=True)['href']
        sid = td[0].text.strip()
        when = datetime.strptime(td[1].find('span').text, "%b/%d/%Y %H:%M").replace(tzinfo=config.tz_msk).astimezone(tz=None).strftime('%y-%m-%d %H:%M')
        a = td[2].find('a', href=True)
#           TODO user color who['class']
        who = {'profile':a['href'],'class':a['class'][1],'title':a['title'],'name':a.text}
        problem = td[3].text.strip()
        lang = td[4].text.strip()
        verdict = td[5].text.strip()
        ms = td[6].text.strip()
        mem = td[7].text.strip()
        assert verdict == 'Accepted', 'submission was not accepted'
        print(sid, when, problem, who['name'], lang, ms, mem)
        choice = input("View this solution? [Y/n]").lower()
        if choice == "yes" or choice == 'y' or choice == '':
            r = view_submission(sid, str(cid)+level)

def search_editorial(args):
    cid, _ = util.guess_cid(args)
    contest_info = get_contest_info(cid)
    if not cid or not contest_info:
        print("[!] Invalid contestID")
        return
    title = re.sub(r' ?\([^)]*\)', '', contest_info[0])
    print("[+] Searching for", title, "editorial")
    res = _http.post('/search', {'query': title + ' editorial' })
    bs = BeautifulSoup(res, 'html.parser')
    topics = bs.find_all("div", {"class": "topic"})
    finding_words = [t.lower() for t in title.split()] + ['editorial']
    posts = []
    for t in topics:
        div = t.find("div", {"class": "title"})
        page_title = div.a.text.strip()
        if page_title.lower().find('editorial') == -1: continue

        page_url = _http.CF_DOMAIN + div.find('a', href=True)['href']
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
        return cur.execute(f'''SELECT title, authors, start, length, participants FROM codeforces WHERE cid = {cid};''').fetchone()
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
        print("{}/contest/{}".format(_http.CF_DOMAIN, cid))
    else:
        print("[!] ContestID is empty")

def open_url(args):
    cid, level = util.guess_cid(args)
    if not cid: return
    problems_url = "{}/contest/{}/problems".format(_http.CF_DOMAIN, cid)
    contest_url = "{}/contest/{}".format(_http.CF_DOMAIN, cid)
    print("[+] Open", contest_url)
    print("[+] Open", problems_url)
    if 'open_in_browser' in conf and conf['open_in_browser'] == True:
        system('''{} "{}" "{}"'''.format(conf['browser'], contest_url, problems_url))

def count_contests(contests):
     return len([c for c in contests.find_all("tr", {"data-contestid": True})])

def parse_list(raw_contests, upcoming=0, write_db=True):
    cur = db.cursor()
#    last_contest = cur.execute('''SELECT cid, start FROM codeforces WHERE upcoming = 0 ORDER BY start DESC;''').fetchone()
    contests = {}
#    page_overlapped = False
    for c in raw_contests.find_all("tr", {"data-contestid": True}):
        cid = int(c['data-contestid'])
#        if last_contest and last_contest[0] == cid: page_overlapped = True
        td = c.find_all("td")
#           urls = [h.extract()['href'] for h in td[0].find_all('a', href=True)]
        title = td[0].text.lstrip().splitlines()[0]
        authors = [{'profile':a['href'],'class':a['class'][1],'title':a['title'],'name':a.text} for a in td[1].find_all('a', href=True)]
        start = td[2].find('span').text
        start = datetime.strptime(start, "%b/%d/%Y %H:%M").replace(tzinfo=config.tz_msk)
        length = td[3].text.strip()
        if upcoming:
            participants = 0
        else:
            participants = td[5].text.strip().lstrip('x')

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

def get_solved_count():
    getsolved_data = { 'action':'getSolvedProblemCountsByContest' }
    solved_string = _http.post("/data/contests", getsolved_data, csrf=True)
    solved_json = json.loads(solved_string)
    open(config.solved_path, 'w').write(solved_string)
    return solved_json

def show_contests(contests, check_solved=False, upcoming=False, solved_json=None):
    total_contests = 0;
    solved_contests = 0
    for c in contests:
        color = ''
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

        if check_solved and solved_json and str(cid) in solved_json['solvedProblemCountsByContestId'] and str(cid) in solved_json['problemCountsByContestId']:
            solved_cnt = solved_json['solvedProblemCountsByContestId'][str(cid)]
            prob_cnt = solved_json['problemCountsByContestId'][str(cid)]
            solved_str = "{:d}/{:d} ".format(solved_cnt, prob_cnt)
            if len(div) > 0 and solved_cnt > 0 and (solved_cnt == prob_cnt or solved_cnt >= conf['contest_goals'][div[-1]]):
                solved_contests += 1
                color = 'green'
        elif solved_json:
            solved_str = "    "
        else:
            solved_str = ""
        contest_info = "{:04d} {:<3} {}{:<{width}} {} ({}){}{}{}".format(cid, div, solved_str, title[:conf['title_width']], start.strftime("%Y-%m-%d %H:%M"), length, weekday, countdown, participants, width=conf['title_width'])
        contest_info = setcolor(color, contest_info)
        print(contest_info)
    if check_solved:
        print("[+] Solved {:d}/{:d} contests".format(solved_contests, total_contests))

def list_contest(args, upcoming=False):
    solved_json = None
    cur = db.cursor()
    if args.force:
        update = True;
    else:
        update = False;
    last_modified = int(cur.execute('''SELECT strftime('%s', last_modified) FROM modifications WHERE site = 'codeforces';''').fetchone()[0])
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

    if ('solved' in args and args.solved) or not path.isfile(config.solved_path):
        solved_json = get_solved_count()
    else:
        with open(config.solved_path, 'r') as f:
            solved_json = json.load(f)

    if update:
        print('[+] Update contests list')
        urls = []
        for page in range(1, conf['max_page']+1):
            urls += [_http.GET('/contests/page/{:d}'.format(page))]
        pages = _http.urlsopen(urls)
        for page in pages:
            bs = BeautifulSoup(page, 'html.parser')
            table = bs.find_all("div", {"class": "datatable"})
            if count_contests(table[1]) == 0:
                print("[!] Contest is running")
                break
            parse_list(table[0], upcoming=1, write_db=True)
            parse_list(table[1], write_db=True)

    if upcoming:
        print("[+] Current or upcoming contests")
        upcoming = cur.execute('''SELECT cid, title, authors, start, length, participants FROM codeforces WHERE upcoming = 1 ORDER BY start;''')
        show_contests(upcoming, upcoming=True)
    else:
        print("[+] Past contests")
        contests = cur.execute('''SELECT cid, title, authors, start, length, participants FROM codeforces WHERE upcoming = 0 ORDER BY start;''')
        show_contests(contests, check_solved=not args.all, solved_json=solved_json)

def list_past_contest(args):
    list_contest(args, upcoming=False)

def list_upcoming(args):
    list_contest(args, upcoming=True)
