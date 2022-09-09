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
    'nocolor': "\033[0m",
    }

def setcolor(c, msg):
    if c and c in colors:
        return colors[c] + msg + colors['nocolor']
    if c == 'legendary':
        return colors['white'] + msg[:1] + colors['red'] + msg[1:] + colors['nocolor']
    else:
        return msg;

def BLUE(msg):
    return colors['blue'] + msg + colors['nocolor']

def RED(msg):
    return colors['red'] + msg + colors['nocolor']

def GREEN(msg):
    return colors['green'] + msg + colors['nocolor']

def YELLOW(msg):
    return colors['yellow'] + msg + colors['nocolor']

def MAGENTA(msg):
    return colors['magenta'] + msg + colors['nocolor']

def CYAN(msg):
    return colors['cyan'] + msg + colors['nocolor']

def WHITE(msg):
    return colors['white'] + msg + colors['nocolor']

def BBLUE(msg):
    return colors['bright_blue'] + msg + colors['nocolor']

def BRED(msg):
    return colors['bright_red'] + msg + colors['nocolor']

def BGREEN(msg):
    return colors['bright_green'] + msg + colors['nocolor']

def BYELLOW(msg):
    return colors['bright_yellow'] + msg + colors['nocolor']

def BMAGENTA(msg):
    return colors['bright_magenta'] + msg + colors['nocolor']

def BCYAN(msg):
    return colors['bright_cyan'] + msg + colors['nocolor']

def BWHITE(msg):
    return colors['bright_white'] + msg + colors['nocolor']

def GRAY(msg):
    return colors['gray'] + msg + colors['nocolor']

def redraw(msg, end=linesep):
    print('\033[A' + msg, end=end)
