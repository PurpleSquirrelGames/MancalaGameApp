#
# Genetic algorithm used to determine tactical values to be used by the
# minimax (negamax) routines.
#
#  COMBOS TO TEST
#
#     (2) GOES_FIRST vs GOES_SECOND  A=[1, 2]
#
#     (4) 3, 4, 5, or 6 SEEDS PER PIT B=[3, 4, 5, 6]
#
#     (6) LOOKING 1, 2, 3, 4, 5, or 6 TURNS AHEAD C=[1, 2, 3, 4, 5, 6]
#
#     (3) CAPTURE RULE VARIATIONS D=[0, 1, 2]
#
#     (4) END OF GAME VARIATIONS E=[0, 1, 2, 3]
#
#  SO, A TOTAL OF 2x4x6x3x4 = 576 SCENARIOS
#
#  FINAL RESULTS OF EACH COMBO ARE APPENDED TO 'tactics/results-A-B-C-D-E.csv'
#  AT START, FIND THE LAST COMBO to know where to start
#
#  LATER, a SCRIPT will assemble the result files into a 'tactical.py' file.
#
#  DO 10 "islands" of independent evolution;
#     then later run all of them together for 20 more generations
#
#  RUN 100 generations for each island
#  HAVE 50 genomes start each generation
#  EACH genome engages each of the other genomes in the "attacker" role
#     EACH engagement is 50 plays, the final scores are tallied for fitness
#     WHEN a genome is in the defender role; have a 15% chance of wrong move
#        per round of play to mimic diversity
#  AFTER ALL engagements are finished, extinct the bottom 60%
#  BREED replacements:
#        1/3rd get a +1 or -1 change to a random gene
#        1/3rd get a big change to a random gene
#                RANGE (-100 to +100)
#        1/3rd swaps values of a random gene with a random survivor
#
# The GENE values:
#

EMPTY_AGAINST_EMPTY_PIT_VALUE = 0
EMPTY_AGAINST_FULL_PIT_VALUE = 1
EASY_REPEAT_VALUE = 3

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

PROTO_GENOME = [1]*len(GENE_MAP)

# GENES CAN RANGE FROM 0 to 8000 BUT THEY CANNOT BE NEGATIVE

##STARTING_TACTICS = {
##    TACTIC_EMPTY_PIT_VALUE = [
##        (12, 1),  # 0 = nearest to STORE, (empty/empty, empty/full)
##        (8, 2),   # 1    first value is value for empty; second is multiplier
##        (5, 1),   # 2
##        (4, 1),   # 3
##        (7, 1),   # 4
##        (9, 1),   # 5
##    ]
##    TACTIC_EASY_REPEAT_VALUE = [
##        4, # pit 0 from store
##        5, # 
##        3, # 
##        2, # 
##        1, # 
##        1, # 
##    ]
##}

import easyAI
from copy import copy
import random
import gameengine

settings = {
    "ai_chosen": 0,
    "who_plays_first": 0,
    "first_player": 2, #  use inverse because we are from AI point of view
    "seeds_per_house_selection": 1,
    "seeds_per_house": 4,
    "capture_rule": 0,
    "eog_rule": 0,
    "seed_drop_rate": 0.4,
}


ALT_AI_LIST = [
    {
        "index": 1,
        "name": "Attacker",
        "rank": "1",
        "strategy": "negamax",  # options: "random", "negamax"
        "lookahead": 2,  # 1 to 6
        "error_rate": 0.0,  # 0.0 to 1.0; odds of making mistake
        "fitness": "balance", # options: greed, caution, balance
        "desc": "test genome",
        "tagline": ""
    },
]


game = gameengine.KalahGame(settings, testing=ALT_AI_LIST)

needed_rounds = 50

score = 0
for round in range(needed_rounds):
    print "round {:02d}".format(round),
    game.reset_board()
    while not game.is_over():
        move = game.get_move()
        # print "    AI {} plays {}".format(game.nplayer, move)
        game.play_move(move)
    print "RESULT:", game.get_winner(), game.strategic_scoring(1, 2)
    score += game.strategic_scoring(1, 2)
final_score = score / needed_rounds
print "FINAL SCORE:", final_score
