import re
from os import path, getcwd, sep
from lxml import html

def guess_cid(args):
    if 'cid' in args and args.cid:
        cid = int(args.cid)
        if 'level' in args and args.level:
            level = args.level
        else:
            level = None
    else:
        cid, level = get_cwd_info()
    return cid, level

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

def pop_element(t):
        text = t.text
        t.getparent().remove(t)
        return text

def show_message(resp):
    doc = html.fromstring(resp)
    for lines in doc.xpath('.//script[@type="text/javascript" and not(@src)]'):
        for l in lines.text.splitlines():
            if l.find('Codeforces.showMessage("') != -1:
                return l.split('"')[1]
