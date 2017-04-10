from tactics_data import TDATA

#
EMPTY_AGAINST_EMPTY_PIT_VALUE = 0
EMPTY_AGAINST_FULL_PIT_VALUE = 1
EASY_REPEAT_VALUE = 3

EMPTY_PIT = 0
FULL_PIT = 1

GENE_MAP = [
    (EMPTY_AGAINST_EMPTY_PIT_VALUE, 0),
    (EMPTY_AGAINST_EMPTY_PIT_VALUE, 1),
    (EMPTY_AGAINST_EMPTY_PIT_VALUE, 2),
    (EMPTY_AGAINST_EMPTY_PIT_VALUE, 3),
    (EMPTY_AGAINST_EMPTY_PIT_VALUE, 4),
    (EMPTY_AGAINST_EMPTY_PIT_VALUE, 5),
    (EMPTY_AGAINST_FULL_PIT_VALUE, 0),
    (EMPTY_AGAINST_FULL_PIT_VALUE, 1),
    (EMPTY_AGAINST_FULL_PIT_VALUE, 2),
    (EMPTY_AGAINST_FULL_PIT_VALUE, 3),
    (EMPTY_AGAINST_FULL_PIT_VALUE, 4),
    (EMPTY_AGAINST_FULL_PIT_VALUE, 5),
    (EASY_REPEAT_VALUE, 0),
    (EASY_REPEAT_VALUE, 1),
    (EASY_REPEAT_VALUE, 2),
    (EASY_REPEAT_VALUE, 3),
    (EASY_REPEAT_VALUE, 4),
    (EASY_REPEAT_VALUE, 5),
]
GENE_DESC = [
    "EMPTY_AGAINST_EMPTY_PIT_VALUE 0",
    "EMPTY_AGAINST_EMPTY_PIT_VALUE 1",
    "EMPTY_AGAINST_EMPTY_PIT_VALUE 2",
    "EMPTY_AGAINST_EMPTY_PIT_VALUE 3",
    "EMPTY_AGAINST_EMPTY_PIT_VALUE 4",
    "EMPTY_AGAINST_EMPTY_PIT_VALUE 5",
    "EMPTY_AGAINST_FULL_PIT_VALUE 0",
    "EMPTY_AGAINST_FULL_PIT_VALUE 1",
    "EMPTY_AGAINST_FULL_PIT_VALUE 2",
    "EMPTY_AGAINST_FULL_PIT_VALUE 3",
    "EMPTY_AGAINST_FULL_PIT_VALUE 4",
    "EMPTY_AGAINST_FULL_PIT_VALUE 5",
    "EASY_REPEAT_VALUE 0",
    "EASY_REPEAT_VALUE 1",
    "EASY_REPEAT_VALUE 2",
    "EASY_REPEAT_VALUE 3",
    "EASY_REPEAT_VALUE 4",
    "EASY_REPEAT_VALUE 5",
]


class Tactics(object):
    def __init__(self):
        self.empty_pit_value = [
            [1, 1], # 0 = nearest to STORE, (empty/empty, empty/full)
            [1, 1],  # 1    first value is value for empty; second is multiplier
            [1, 1],  # 2
            [1, 1],  # 3
            [1, 1],  # 4
            [1, 1],  # 5
        ]
        self.easy_repeat_value = [
            1, # pit 0 from store
            1, # 
            1, # 
            1, # 
            1, # 
            1, # 
        ]

    def remap(self, character, settings):
        first_player = settings['first_player']
        seed_count = settings['seeds_per_house']
        turns_ahead = character['lookahead']
        if turns_ahead > 4:
            turns_ahead = 4
        capture_rule = settings['capture_rule']
        eog_rule = settings['eog_rule']
        tup = (first_player, seed_count, turns_ahead, capture_rule, eog_rule)
        tl = TDATA[tup]
        for index, gene in enumerate(tl):
            place, pit = GENE_MAP[index]
            if place == EMPTY_AGAINST_EMPTY_PIT_VALUE:
                self.empty_pit_value[pit][EMPTY_PIT] = gene
            elif place == EMPTY_AGAINST_FULL_PIT_VALUE:
                self.empty_pit_value[pit][FULL_PIT] = gene
            elif place == EASY_REPEAT_VALUE:
                self.easy_repeat_value[pit] = gene
        return

def build_tactics_from_list(t, tl):
    for index, gene in enumerate(tl):
        place, pit = GENE_MAP[index]
        if place == EMPTY_AGAINST_EMPTY_PIT_VALUE:
            t.empty_pit_value[pit][EMPTY_PIT] = gene
        elif place == EMPTY_AGAINST_FULL_PIT_VALUE:
            t.empty_pit_value[pit][FULL_PIT] = gene
        elif place == EASY_REPEAT_VALUE:
            t.easy_repeat_value[pit] = gene
    return

