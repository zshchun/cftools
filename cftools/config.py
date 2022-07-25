import tomli
import sqlite3
from os import makedirs, path, environ
from datetime import timezone, timedelta

DEFAULT_CONFIG = {
    'solved_dir': '~/codeforces',
    'cache_dir': '~/codeforces/cache',
    'lang_ext': ['cpp'],
    'database': '~/codeforces/cache.db',
    'title_width': 40,
    'max_page': 3,
    'open_in_browser': True,
    'browser': 'google-chrome',
    'pager': 'less',
    'contest_goals': {
        '1': 3,
        '2': 5,
        '3': 9,
        '4': 9,
        'G': 5,
        }
    }

base_dir = environ["HOME"] + "/.cf"
cookies_path = base_dir + '/cookies'
csrf_path = base_dir + '/csrf_token'
solved_path = base_dir + '/solved.json'
config_path = base_dir + "/config.toml"
tz_msk = timezone(timedelta(hours=3))
conf = None

def loads():
    global conf, db
    if path.isfile(config_path):
        conf = tomli.load(open(config_path, "rb"))
    else:
        conf = DEFAULT_CONFIG
    for d in [base_dir, conf['solved_dir'], conf['cache_dir']]:
        if not path.isdir(path.expanduser(d)):
            makedirs(path.expanduser(d))
    db_path = path.expanduser(conf['database'])

    if not path.isfile(db_path):
        db = sqlite3.connect(db_path)
        cur = db.cursor()
        cur.execute('''CREATE TABLE codeforces (cid integer primary key, title varchar, authors varchar, start varchar, length varchar, participants integer, upcoming integer);''')
        cur.execute('''CREATE TABLE modifications (site TEXT NOT NULL PRIMARY KEY ON CONFLICT REPLACE, last_modified TIMESTAMP DEFAULT current_timestamp);''')
        cur.execute('''INSERT INTO modifications (site) VALUES ('codeforces');''')
        cur.execute('''CREATE TRIGGER update_time_codeforces AFTER UPDATE ON codeforces BEGIN UPDATE modifications SET last_modified = current_timestamp WHERE site = 'codeforces'; END;''')
        cur.execute('''CREATE TRIGGER delete_time_codeforces AFTER DELETE ON codeforces BEGIN UPDATE modifications SET last_modified = current_timestamp WHERE site = 'codeforces'; END;''')
        cur.execute('''CREATE TRIGGER insert_time_codeforces AFTER INSERT ON codeforces BEGIN UPDATE modifications SET last_modified = current_timestamp WHERE site = 'codeforces'; END;''')
        db.commit()
    else:
        db = sqlite3.connect(db_path)

if not conf:
    loads()
