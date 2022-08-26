from . import _http
from . import ui
from . import config
from . import contest
from .util import guess_cid, pop_element
from time import time, sleep
from os import listdir, path, sep, makedirs
from lxml import html, etree
from .config import conf
import asyncio

def find_source_files(_dir):
    exts = [k['ext'] for k in conf['lang']]
    if not exts: return
    files = [_dir + sep + f for f in listdir(_dir) if path.isfile(f) and path.splitext(f)[-1].lstrip('.') in exts]
    return files

def prepare_problem_dir(cid, level=None):
    p = path.expanduser(config.conf['contest_dir'] + sep + str(cid))
    if level == None:
        makedirs(p, exist_ok=True)
    else:
        p += sep + level.lower()
        makedirs(p, exist_ok=True)
    return p

def find_input_files(_dir):
    ins = [_dir + sep + f for f in listdir(_dir) if path.isfile(f) and path.splitext(f)[-1] == '.txt' and f.startswith('in')]
    return ins

def select_source_code(cid, level):
    prob_path = prepare_problem_dir(cid, level)
    files = find_source_files(prob_path)
    if len(files) == 0:
        print("[!] File not found")
        return None
    elif len(files) >= 2:
        print("[!] There are multiple solutions")
        return None
    return files[0]

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
            prob_dir = prepare_problem_dir(cid, level)
            for j in range(len(in_tc)):
                fi = open(prob_dir+sep+'in'+str(j+1)+'.txt', 'w')
                fo = open(prob_dir+sep+'ans'+str(j+1)+'.txt', 'w')
                for k in in_tc[j]: fi.write(k)
                for k in out_tc[j]: fo.write(k)

def generate_source(args):
    cid, level = guess_cid(args)
    if not cid or not level:
        print("[!] Invalid contestID or level")
        return
    template_path = path.expanduser(conf['template'])
    if not path.isfile(template_path):
        print("[!] Template file not found")
        return
    prob_dir = prepare_problem_dir(cid, level)
    ext = path.splitext(template_path)[-1]
    assert ext != "", "[!] File extension not found"
    new_path = prob_dir + sep + level.lower() + ext
    inf = open(template_path, 'r')
    outf = open(new_path, 'w')
    for line in inf:
        outf.write(line)
    ui.green('[+] Generate {}'.format(new_path))
