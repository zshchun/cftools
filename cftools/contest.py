#!/usr/bin/env python3
import json
import logging
import re
from . import _http
from .config import conf, db, tz_msk
from time import time
from bs4 import BeautifulSoup
from datetime import datetime, timezone, timedelta
from os import path, listdir, system, getcwd, sep
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
    if args.cid and args.cid: 
        cid = int(args.cid)
        level = args.level
    else:
        cid, level = get_cwd_info()
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
    page_path = "/contest/{}/status/page/{}?order={}".format(cid, page, order)
    res = _http.post(page_path, post_data)
    bs = BeautifulSoup(res, 'html.parser')
    table = bs.find("table", {"class": "status-frame-datatable"})
    tr = table.find_all("tr", {"data-submission-id": True})
    assert len(tr) > 0, "empty tr tag"
    for t in tr:
        td = t.find_all("td")
        assert len(td) > 6, "not enough td tags"
        url = _http.CF_DOMAIN + td[0].find('a', href=True)['href']
        sid = td[0].text.strip()
        when = datetime.strptime(td[1].find('span').text, "%b/%d/%Y %H:%M").replace(tzinfo=tz_msk).astimezone(tz=None).strftime('%y-%m-%d %H:%M')
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
    cid = args.cid
    if not cid:
        cid, _ = get_cwd_info()
    db = get_contest_info(cid)
    if not cid or not db:
        print("[!] Invalid contestID")
        return
    title = re.sub(r' ?\([^)]*\)', '', db[0])
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

def get_cwd_info():
    p = path.normpath(getcwd()).split(sep)
    if len(p) >= 2 and p[-2].isnumeric() and re.match(r"[a-z]", p[-1]):
        cid = int(p[-2])
        level = p[-1]
    elif len(p) >= 1 and p[-1].isnumeric():
        cid = int(p[-1])
        level = None
    else:
        cid = None
        level = None
    return cid, level

def get_contest_info(cid):
    if cid:
        cur = db.cursor()
        return cur.execute(f'''SELECT title, authors, start, length, participants FROM codeforces WHERE cid = {cid};''').fetchone()
    else:
        return []

def show_contest_info(args):
    if args.cid: 
        cid = int(args.cid)
        level = args.level
    else:
        cid, level = get_cwd_info()
    if cid:
        c = get_contest_info(cid)
        print("[+] Show contest info")
        if level:
            print("{} - {} {}".format(c[0], cid, level))
        else:
            print("{} - {}".format(c[0], cid))
    else:
        print("[!] ContestID not found.")

def open_url(args):
    if args.cid:
        cid = int(args.cid)
        level = None
    else:
        cid, level = get_cwd_info()
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
    last_contest = cur.execute('''SELECT cid, start FROM codeforces WHERE upcoming = 0 ORDER BY start DESC;''').fetchone()
    contests = {}
    page_overlapped = False
    for c in raw_contests.find_all("tr", {"data-contestid": True}):
        cid = int(c['data-contestid'])
        if last_contest and last_contest[0] == cid: page_overlapped = True
        td = c.find_all("td")
#           urls = [h.extract()['href'] for h in td[0].find_all('a', href=True)]
        title = td[0].text.lstrip().splitlines()[0]
        authors = [{'profile':a['href'],'class':a['class'][1],'title':a['title'],'name':a.text} for a in td[1].find_all('a', href=True)]
        start = td[2].find('span').text
        start = datetime.strptime(start, "%b/%d/%Y %H:%M").replace(tzinfo=tz_msk)
        length = td[3].text.strip()
        if upcoming:
            participants = 0
        else:
            participants = td[5].text.strip().lstrip('x')

        contests[cid] = {'title':title, 'authors':authors, 'start':start, 'length':length, 'participants':participants, 'upcoming':0}
        if write_db:
            cur.execute('INSERT or REPLACE INTO codeforces (cid, title, authors, start, length, participants, upcoming) VALUES (?, ?, ?, ?, ?, ?, ?)', (cid, title, json.dumps(authors), start, length, participants, upcoming))
    if write_db: db.commit()
    return page_overlapped

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
    # TODO support directory hierachy. ex) 1600/a.cpp
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

def show_contests(contests, check_solved=False, upcoming=False):
    solved_width = 0
    solved_contests = 0
    contests_nr = 0;
    if check_solved:
        solved_list = solved_problems()
        solved_width = max(map(len, conf['problem_range'].values()))+1
    for c in contests:
        cid = c[0]
        title = c[1]
        div = ''.join(parse_div(title))
        start = datetime.strptime(c[3], '%Y-%m-%d %H:%M:%S%z').astimezone(tz=None)
        length = c[4]
        if upcoming:
            participants = ''
        else:
            participants = ' x' + str(c[5])
        problems = ''
        solved_cnt = 0
        if check_solved and len(div) > 0:
            for l in conf['problem_range'][div[-1]]:
                if cid in solved_list and l in solved_list[cid]:
                    solved_cnt += 1
                    problems += ' '
                else:
                    problems += l.upper()
            if solved_cnt > 0 and solved_cnt == len(conf['problem_range'][div[-1]]):
                solved_contests += 1
        countdown = ''
        if upcoming:
            if start > datetime.now().astimezone(tz=None):
                d = start - datetime.now().astimezone(tz=None)
                h = d.seconds // 3600
                m = d.seconds // 60 % 60
                countdown = ' {:02}d+{:02d}:{:02d}'.format(d.days, h, m)
            else:
                d = start - datetime.now().astimezone(tz=None)
                t = d.seconds + int(length.split(':')[0])*3600 + int(length.split(':')[1])*60
                h = t // 3600
                m = t // 60 % 60
#                countdown = ' {}d+{:02d}:{:02d}'.format(d.days, h, m)
#                d = datetime.now().astimezone(tz=None) - start
#                print(int(length.split(':')[0]), (d.seconds // 3600))
#                print(int(length.split(':')[1]), ((d.seconds // 60 % 60)+1))
#                h = int(length.split(':')[0]) - (d.seconds // 3600)
#                m = int(length.split(':')[1]) - ((d.seconds // 60 % 60)+1)
                countdown = '    -{:02d}:{:02d}'.format(h, m)

        if not check_solved or problems.strip():
            print("{:04d} {:<3} {:<{solved_width}}{:<{width}} {} ({}){}{}".format(cid, div, problems, title[:conf['title_width']], start.strftime("%Y-%m-%d %H:%M"), length, countdown, participants, width=conf['title_width'], solved_width=solved_width))
            contests_nr += 1
    if check_solved:
        print("[+] Solved {:d}/{:d} contests".format(solved_contests, contests_nr))

def list_contest(args, upcoming=False):
    cur = db.cursor()
    update = False;
    last_modified = int(cur.execute('''SELECT strftime('%s', last_modified) FROM modifications WHERE site = 'codeforces';''').fetchone()[0])
    now = int(time())
    row_count = cur.execute('''SELECT COUNT(*) FROM codeforces''').fetchone()[0]
    if now - last_modified > 24 * 3600 or row_count == 0:
        update = True

    if args.force or update:
        print('[+] Update contests list', end='', flush=True)
        for page in range(1, conf['max_page']+1):
            print('.', end='', flush=True)
            page_path = '/contests/page/{:d}'.format(page)
            html = _http.get(page_path)
            bs = BeautifulSoup(html, 'html.parser')
            table = bs.find_all("div", {"class": "datatable"})
            if count_contests(table[1]) == 0:
                print("\n[!] Contest is running")
                break
            parse_list(table[0], upcoming=1, write_db=True)
            if parse_list(table[1], write_db=True): break
        print()

    if upcoming:
        print("[+] Current or upcoming contests")
        upcoming = cur.execute('''SELECT cid, title, authors, start, length, participants FROM codeforces WHERE upcoming = 1 ORDER BY start;''')
        show_contests(upcoming, upcoming=True)
    else:
        print("[+] Past contests")
        contests = cur.execute('''SELECT cid, title, authors, start, length, participants FROM codeforces WHERE upcoming = 0 ORDER BY start;''')
        show_contests(contests, check_solved=not args.all)

def list_upcoming(args):
    list_contest(args, upcoming=True)
