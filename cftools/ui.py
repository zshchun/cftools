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

def redraw(msg, end=linesep):
#    print('\033[2K' + msg, end=end)
    print('\033[A' + msg, end=end)
