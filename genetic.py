# GENETIC TACTICS ALGORITHM

def build_scenario_tuples(combos):
    current = [None] * len(combos)
    s = []
    f = []
    for a in combos[0]:
        for b in combos[1]:
            for c in combos[2]:
                for d in combos[3]:
                    for e in combos[4]:
                        s.append((a, b, c, d, e))
                        f.append("tactics/kalah-results-{}-{}-{}-{}-{}.json".format(a, b, c, d, e))
    return s, f

#
# Genetic algorithm used to determine tactical values to be used by the
# minimax (negamax) routines.
#
#  COMBOS TO TEST
COMBOS = []
#
#     (2) GOES_FIRST vs GOES_SECOND
COMBOS.append([1, 2])
#
#     (4) 3, 4, 5, or 6 SEEDS PER PIT
COMBOS.append([4, 3, 5, 6]) # doing 4 first to help with early analysis
#
#     (6) LOOKING 1, 2, 3, 4, 5, or 6 TURNS AHEAD
COMBOS.append([1, 2, 3, 4, 5, 6])
#
#     (3) CAPTURE RULE VARIATIONS
COMBOS.append([0, 1, 2])
#
#     (4) END OF GAME VARIATIONS
COMBOS.append([0, 1, 2, 3])
#
#  SO, A TOTAL OF 2x4x6x3x4 = 576 SCENARIOS
SCENARIOS, FILENAMES = build_scenario_tuples(COMBOS)
#
#  FINAL RESULTS OF EACH COMBO ARE APPENDED TO 'tactics/kalah-results-A-B-C-D-E.json'
#  AT START, FIND THE LAST COMBO to know where to start
#
#  LATER, a SCRIPT will assemble the result files into a 'tactical.py' file.
#
#  DO 10 "islands" of independent evolution;
#     then later run all of them together for 20 more generations
ISLAND_QTY = 1 # 10
#
#  RUN 100 generations for each island
GENERATION_QTY = 5 # 100
#  HAVE 50 genomes start each generation
POPULATION_SIZE = 10 # 50
#  EACH genome engages each of the other genomes in the "attacker" role
#     EACH engagement is 10 plays, the final scores are tallied for fitness
PLAYS_PER_ENGAGEMENT = 5
#     WHEN a genome is in the defender role; have a 15% chance of wrong move
#        per round of play to mimic diversity
#  AFTER ALL engagements are finished, extinct the bottom 60%
EXTINCTION_RATE = 0.6
#  BREED replacements:
#        1/3rd get a +1 or -1 change to a random gene
#        1/3rd get a big change to a random gene
#                RANGE (-100 to +100)
#        1/3rd swaps values of a random gene with a random survivor
BREED_OPTIONS = ["minor", "major", "cross"]
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
GENE_MAP_SIZE = len(GENE_MAP)

PROTO_GENOME = {
    'id': 0,
    'score': -1000000,  # negative 1 million is below all possible scores
    'genes': [1]*len(GENE_MAP),
    'life_span': 0,
    'parent_qty': 0
}

ID_CTR = 1

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
from copy import copy, deepcopy
import random
import gameengine
from characters import Tactics
from operator import itemgetter

settings = {
    "ai_chosen": 0,
    "who_plays_first": 1,
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
        "lookahead": 1,  # 1 to 6
        "error_rate": 0.0,  # 0.0 to 1.0; odds of making mistake
        "fitness": "balance", # options: greed, caution, balance
        "desc": "test genome",
        "tagline": "",
        "tactics": Tactics()
    },
    {
        "index": 2,
        "name": "Defender",
        "rank": "1",
        "strategy": "negamax",  # options: "random", "negamax"
        "lookahead": 3,  # 1 to 6
        "error_rate": 0.15,  # 0.0 to 1.0; odds of making mistake
        "fitness": "balance", # options: greed, caution, balance
        "desc": "test genome defender",
        "tagline": "",
        "tactics": Tactics()
    },
]


game = gameengine.KalahGame(settings, testing=ALT_AI_LIST)

def play_engagement():
    score = 0
    for round in range(PLAYS_PER_ENGAGEMENT):
        #print "    round {:02d}".format(round),
        game.reset_board()
        while not game.is_over():
            move = game.get_move()
            game.play_move(move)
        #print "RESULT:", game.get_winner(), game.strategic_scoring(1, 2)
        score += game.strategic_scoring(1, 2)
    final_score = score / PLAYS_PER_ENGAGEMENT
    # print "    FINAL SCORE:", final_score
    return final_score

def do_extinction(genome_list):
    l = len(genome_list)
    last = int(l * EXTINCTION_RATE)
    new_list = genome_list[0:last]
    for genome in new_list:
        genome['life_span'] += 1
    return new_list

def do_reproduction(genome_list):
    global ID_CTR
    missing = POPULATION_SIZE - len(genome_list)
    if missing <= 0:
        return
    for _ in range(missing):
        parent = random.choice(genome_list)
        new_gene = deepcopy(parent)
        qty_changes = random.randint(1, 5)
        for _ in range(qty_changes):
            action = random.randint(1, 3)
            gene_select = random.randint(1, GENE_MAP_SIZE) - 1
            if action==1:
                # minor adjustment
                if new_gene['genes'][gene_select] == 0:
                    degree = random.choice([1, 2])
                else:
                    degree = random.choice([-1, 1])
                new_gene['genes'][gene_select] += degree
            elif action==2:
                # major adjustment
                degree = random.randint(-1000, 1000)
                new_gene['genes'][gene_select] += degree
                if new_gene['genes'][gene_select] < 0:
                    new_gene['genes'][gene_select] = 0
            elif action==3:
                # swap genes
                life_partner = random.choice(genome_list)
                new_gene['genes'][gene_select] = copy(life_partner['genes'][gene_select])
        new_gene['life_span'] = 0
        new_gene['parent_qty'] += 1
        new_gene['id'] = ID_CTR
        ID_CTR += 1
        genome_list.append(new_gene)            
    return

def do_trials(genome_list):
    opp_qty = len(genome_list) - 1
    for me, genome in enumerate(genome_list):
        apply_genome(game.players[0], genome)
        print me, "GENE", genome['id'], "ANCESTORS", genome["parent_qty"], "LIFESPAN", genome['life_span']
        total = 0
        for other, opponent in enumerate(genome_list):
            if me!=other:
                apply_genome(game.players[1], opponent)
                total += play_engagement()
        genome['score'] = int(total / opp_qty)
        print "    SCORE", genome['score']
    return

def apply_genome(character, genome):
    # TODO!
    return

def do_sort(genome_list):
    new_list = sorted(genome_list, key=itemgetter('score'), reverse=True)    
    return new_list


######################################
#
#  MAIN
#
######################################

for si, scenario in enumerate(SCENARIOS):
    #-----------
    #
    #  SETUP SCENARIO
    #
    #-----------
    a, b, c, d, e = scenario
    filename = FILENAMES[si]
    print "file:",filename
    short = ""
    if a==1:
        settings['who_plays_first'] = 2
        short += "PLYR FIRST:"
    else:
        settings['who_plays_first'] = 1
        short += "AI FIRST  :"
    settings['seeds_per_house'] = b
    short += "SEEDS"+str(b)+":"
    ALT_AI_LIST[0]['lookahead'] = c
    ALT_AI_LIST[1]['lookahead'] = c
    short += "LOOK"+str(c)+":"
    settings["capture_rule"] = d
    short += "CAPTURE"+str(d)+":"
    settings["eog_rule"] = e
    short += "EOG"+str(e)
    #---------------------
    #
    # islands
    #
    #---------------------
    winner_list = []
    for island in range(ISLAND_QTY):
        genome_list = []
        for _ in range(POPULATION_SIZE):
            genome = deepcopy(PROTO_GENOME)
            genome_list.append(genome)
        #---------------------
        #
        # generations
        #
        #---------------------
        for gen in range(GENERATION_QTY):
            genome_list = do_extinction(genome_list)
            do_reproduction(genome_list)
            do_trials(genome_list)
            genome_list = do_sort(genome_list)
        # save the winners on this island
        winner_list.extend(genome_list[0:10])
    #---------------------
    #
    # compete across the islands
    #
    #---------------------
    for gen in range(GENERATION_QTY):
        do_trials(winner_list)          # for these rounds, START with trials
        winner_list = do_sort(winner_list)
        winner_list = do_extinction(winner_list)
        do_reproduction(winner_list)
    #--------------------
    #
    # save the WINNER
    #
    #--------------------
    # fopenxxx
    print "winners:"
    for winner in winner_list:
        print "   ", winner 
    break
