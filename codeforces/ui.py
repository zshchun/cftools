from os import linesep
colors = {
    'black': "\033[30m",
    'red': "\033[31m",
    'green': "\033[32m",
    'yellow': "\033[33m",
    'blue': "\033[34m",
    'magenta': "\033[35m",
    'cyan': "\033[36m",
    'white': "\033[37m",
    'nocolor': "\033[0m",
    'orange': "\033[33m", # yellow
    'violet': "\033[35m", # magenta
    'gray': "\033[90m",
    'bright_red': "\033[91m",
    'bright_green': "\033[92m",
    'bright_yellow': "\033[93m",
    'bright_blue': "\033[94m",
    'bright_magenta': "\033[95m",
    'bright_cyan': "\033[96m",
    'bright_white': "\033[97m",
    }

def setcolor(c, msg):
    if c and c in colors:
        return colors[c] + msg + colors['nocolor']
    if c == 'legendary':
        return colors['white'] + msg[:1] + colors['red'] + msg[1:] + colors['nocolor']
    else:
        return msg;

def blue(msg, end=linesep):
    print(colors['blue'] + msg + colors['nocolor'], end=end)

def red(msg, end=linesep):
    print(colors['red'] + msg + colors['nocolor'], end=end)

def green(msg, end=linesep):
    print(colors['green'] + msg + colors['nocolor'], end=end)

def yellow(msg, end=linesep):
    print(colors['yellow'] + msg + colors['nocolor'], end=end)

def magenta(msg, end=linesep):
    print(colors['magenta'] + msg + colors['nocolor'], end=end)

def cyan(msg, end=linesep):
    print(colors['cyan'] + msg + colors['nocolor'], end=end)

def white(msg, end=linesep):
    print(colors['white'] + msg + colors['nocolor'], end=end)

def bblue(msg, end=linesep):
    print(colors['bright_blue'] + msg + colors['nocolor'], end=end)

def bred(msg, end=linesep):
    print(colors['bright_red'] + msg + colors['nocolor'], end=end)

def bgreen(msg, end=linesep):
    print(colors['bright_green'] + msg + colors['nocolor'], end=end)

def byellow(msg, end=linesep):
    print(colors['bright_yellow'] + msg + colors['nocolor'], end=end)

def bmagenta(msg, end=linesep):
    print(colors['bright_magenta'] + msg + colors['nocolor'], end=end)

def bcyan(msg, end=linesep):
    print(colors['bright_cyan'] + msg + colors['nocolor'], end=end)

def bwhite(msg, end=linesep):
    print(colors['bright_white'] + msg + colors['nocolor'], end=end)

def redraw(msg, end=linesep):
#    print('\033[2K' + msg, end=end)
    print('\033[A' + msg, end=end)
