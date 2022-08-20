from . import contest
from . import problem
from . import judge
from . import account
from . import __version__
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

def main():
    parser = ArgumentParser(prog='Codeforces CLI', description="Codeforce CLI tool")
    parser.add_argument('--version', help="version", action='version', version='%(prog)s ' + __version__)
    subparsers = parser.add_subparsers(title='commands', dest='command')
    commands = {}

    _list = subparsers.add_parser('list', aliases=['l'], help="List contests", allow_abbrev=True)
    _list.add_argument('-f', '--force',  action='store_true', help="Update cache")
    _list.add_argument('-s', '--solved',  action='store_true', help="Update solved problems")
    _list.add_argument('-a', '--all',  action='store_true', help="Show all contests")
    _list.set_defaults(func=contest.list_past_contest)

    _upcoming = subparsers.add_parser('upcoming', aliases=['u'], help="List upcoming contests", allow_abbrev=True)
    _upcoming.add_argument('-f', '--force',  action='store_true', help="Update cache")
    _upcoming.set_defaults(func=contest.list_upcoming)

    _solution = subparsers.add_parser('solution', aliases=['q'], help="Get problem's solutions", allow_abbrev=True)
    _solution.add_argument('cid', metavar='contestID', nargs='?', action='store', type=int)
    _solution.add_argument('level', metavar='problem level', nargs='?', action='store', type=str)
    _solution.set_defaults(func=contest.get_solutions)

    _info = subparsers.add_parser('info', aliases=['i'], help="Show contest info")
    _info.add_argument('cid', metavar='contestID', nargs='?', action='store', type=int)
    _info.add_argument('level', metavar='problem level', nargs='?', action='store', type=str)
    _info.set_defaults(func=contest.show_contest_info)

    _login = subparsers.add_parser('login', help="Sign in codeforces account")
    _login.set_defaults(func=account.login)

    _editorial = subparsers.add_parser('editorial', aliases=['d'], help="Show editorial and announcement links")
    _editorial.add_argument('cid', metavar='contestID', nargs='?', action='store', type=int)
    _editorial.set_defaults(func=contest.get_contest_materials)

    _open = subparsers.add_parser('open', aliases=['o'], help="Open codeforces URL")
    _open.add_argument('cid', metavar='contestID', nargs='?', action='store', type=int)
    _open.add_argument('level', metavar='problem level', nargs='?', action='store', type=str)
    _open.set_defaults(func=contest.open_url)

    _parse = subparsers.add_parser('parse', aliases=['p'], help="Parse problems of a contest")
    _parse.add_argument('cid', metavar='contestID', action='store', type=int)
    _parse.set_defaults(func=problem.parse_problems)

    _race = subparsers.add_parser('race', aliases=['r'], help="Race a contest")
    _race.add_argument('cid', metavar='contestID', action='store', type=int)
    _race.set_defaults(func=contest.race_contest)

    _submit = subparsers.add_parser('submit', aliases=['s'], help="Submit a solution file")
    _submit.add_argument('cid', metavar='contestID', nargs='?', action='store', type=int)
    _submit.add_argument('level', metavar='level', nargs='?', action='store', type=str)
    _submit.add_argument('-i', '--input', action='store', type=str, help="Input source")
    _submit.set_defaults(func=problem.submit)

    args = parser.parse_args()
    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()
