from os import linesep
colors = {
    'black': "\033[90m",
    'red': "\033[91m",
    'green': "\033[92m",
    'yellow': "\033[93m",
    'blue': "\033[94m",
    'magenta': "\033[95m",
    'cyan': "\033[96m",
    'white': "\033[97m",
    'nocolor': "\033[0m",
    }

def setcolor(c, msg):
    if c and c in colors:
        return colors[c] + msg + colors['nocolor']
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
