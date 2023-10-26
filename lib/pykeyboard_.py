from msvcrt import getch

normal_key = {
    "3":"ctrl-c",
    "13":"enter",
    "27":"esc",
    "32":"space"
}
special_key = {
    "80":"down",
    "71":"home",
    "72":"up",
    "75":"left",
    "77":"right",
    "79":"end",
    "134":"f12"
}

def readkey(prnt=True):
    result = None
    key = ord(getch())
    if key in normal_key:
        return normal_key[key]
    elif key == 224:
        key = ord(getch())
        if key in special_key:
            return special_key[key]
        else:
            print(" Special Key:",key)
    else:
        print(" Normal Key:",key)

    return



























#
