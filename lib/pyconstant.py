default_cmd_col = 70
default_cmd_line = 25

party_symbol = "■"
PARTYICONLIST = [(227, 67, 67),(216, 67, 227),(67, 70, 227),(67, 227, 208),(226, 237, 57),(212, 82, 207)]

RANKSCOLORS = [
            ('Unranked', (46, 46, 46)),
            ('Unranked', (46, 46, 46)),
            ('Unranked', (46, 46, 46)),
            ('Iron 1', (72, 69, 62)),
            ('Iron 2', (72, 69, 62)),
            ('Iron 3', (72, 69, 62)),
            ('Bronze 1', (187, 143, 90)),
            ('Bronze 2', (187, 143, 90)),
            ('Bronze 3', (187, 143, 90)),
            ('Silver 1', (174, 178, 178)),
            ('Silver 2', (174, 178, 178)),
            ('Silver 3', (174, 178, 178)),
            ('Gold 1', (197, 186, 63)),
            ('Gold 2', (197, 186, 63)),
            ('Gold 3', (197, 186, 63)),
            ('Platinum 1', (24, 167, 185)),
            ('Platinum 2', (24, 167, 185)),
            ('Platinum 3', (24, 167, 185)),
            ('Diamond 1', (216, 100, 199)),
            ('Diamond 2', (216, 100, 199)),
            ('Diamond 3', (216, 100, 199)),
            ('Ascendant 1', (24, 148, 82)),
            ('Ascendant 2', (24, 148, 82)),
            ('Ascendant 3', (24, 148, 82)),
            ('Immortal 1', (221, 68, 68)),
            ('Immortal 2', (221, 68, 68)),
            ('Immortal 3', (221, 68, 68)),
            ('Radiant', (255, 253, 205)),
        ]
def level_to_color(level):
        if level >= 400:
            return (102, 212, 212)
        elif level >= 300:
            return (207, 207, 76)
        elif level >= 200:
            return (71, 71, 204)
        elif level >= 100:
            return (241, 144, 54)
        elif level < 100:
            return (211, 211, 211)
