import tomli
import sqlite3
from os import makedirs, path, environ
from datetime import timezone, timedelta

DEFAULT_CONFIG = {
    'contest_dir': '~/codeforces',
    'cache_dir': '~/.cf/cache',
    'database': '~/.cf/cache.db',
    'title_width': 40,
    'max_page': 3,
    'open_in_browser': True,
    'browser': 'google-chrome',
    'pager': 'less',
    'prog_id': 61,
    'hide_solved_contest': False,
    'lang': [
        {'ext': "cpp", 'cmd': "g++ -O2", },
        {'ext': "py", 'cmd': "python3", },
    ],
    'contest_goals': {
        '1': 3,
        '2': 5,
        '3': 9,
        '4': 9,
        'G': 5,
        }
    }
PROG_TYPE_ID = {
     3: "Delphi 7",
     4: "Free Pascal 3.0.2",
     6: "PHP 8.1.7",
     7: "Python 2.7.18",
     9: "C# Mono 6.8",
     12: "Haskell GHC 8.10.1",
     13: "Perl 5.20.1",
     19: "OCaml 4.02.1",
     20: "Scala 2.12.8",
     28: "D DMD32 v2.091.0",
     31: "Python 3.8.10",
     32: "Go 1.18.3",
     34: "JavaScript V8 4.8.0",
     36: "Java 1.8.0_241",
     40: "PyPy 2.7.13 (7.3.0)",
     41: "PyPy 3.6.9 (7.3.0)",
     43: "GNU GCC C11 5.1.0",
     48: "Kotlin 1.4.31",
     50: "GNU G++14 6.4.0",
     51: "PascalABC.NET 3.4.2",
     52: "Clang++17 Diagnostics",
     54: "GNU G++17 7.3.0",
     55: "Node.js 12.16.3",
     59: "Microsoft Visual C++ 2017",
     60: "Java 11.0.6",
     61: "GNU G++17 9.2.0 (64 bit, msys 2)",
     65: "C# 8, .NET Core 3.1",
     67: "Ruby 3.0.0",
     70: "PyPy 3.9.10 (7.3.9, 64bit)",
     72: "Kotlin 1.5.31",
     73: "GNU G++20 11.2.0 (64 bit, winlibs)",
     74: "Java 17 64bit",
     75: "Rust 1.58.0 (2021)",
     77: "Kotlin 1.6.10",
     79: "C# 10, .NET SDK 6.0",
     80: "Clang++20 Diagnostics",
}

base_dir = environ["HOME"] + "/.cf"
cookies_path = base_dir + '/cookies'
token_path = base_dir + '/tokens.json'
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
    for d in [base_dir, conf['contest_dir'], conf['cache_dir']]:
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
