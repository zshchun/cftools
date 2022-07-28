colors = {
    'black': "\033[90m",
    'red': "\033[91m",
    'green': "\033[92m",
    'yellor': "\033[93m",
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
