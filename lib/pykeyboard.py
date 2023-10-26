import re
from msvcrt import getch

normal_keys = {
    3:"ctrl-c",
    8:"backspace",
    13:"enter",
    27:"esc",
    32:"space"
}
special_keys = {
    80:"down",
    71:"home",
    72:"up",
    75:"left",
    77:"right",
    79:"end",
    134:"f12"
}
is_debug = False

def readkey(prnt=True):
    result = None
    key = ord(getch())
    if key in normal_keys:
        return normal_keys[key]
    elif key == 224:
        key = ord(getch())
        if key in special_keys:
            return special_keys[key]
        else:
            print(" special:",(key))
    else:
        key_char = re.sub(r'[^\w]', '', chr(key))
        if key_char: return key_char
        print(" normal:",key)




























#
