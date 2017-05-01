# GENETIC TACTICS ALGORITHM

from copy import copy, deepcopy
import random
from operator import itemgetter
import json
import os
import sys

import easyAI
import gameengine
from tactics import Tactics, GENE_MAP, build_tactics_from_list

# you can launch with combo's limited to one value using FIRST, SEEDS, LOOK
#
# for example:
#    python tactics_generator.py FIRST 2 LOOK 5
#
# will only generate JSON files for 'AI GOING FIRST' and 'LOOKAHEAD 5'


def build_scenario_tuples(combos):
    if len(sys.argv) >= 3:
        try:
            i = sys.argv.index("FIRST")
            combos[0] = [int(sys.argv[i + 1])]
        except ValueError:
            pass
        try:
            i = sys.argv.index("SEEDS")
            combos[1] = [int(sys.argv[i + 1])]
        except ValueError:
            pass
        try:
            i = sys.argv.index("LOOK")
            combos[2] = [int(sys.argv[i + 1])]
        except ValueError:
            pass
    s = []
    f = []
    for a in combos[0]:
        for b in combos[1]:
            for c in combos[2]:
                for d in combos[3]:
                    for e in combos[4]:
                        s.append((a, b, c, d, e))
                        f.append("tactics_work/kalah-results-{}-{}-{}-{}-{}.json".format(
                            a, b, c, d, e
                        ))
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
COMBOS.append([4, 3, 5, 6])  # doing 4 first to help with early analysis
#
#     (6) LOOKING 1, 2, 3, 4, 5, or 6 TURNS AHEAD
# COMBOS.append([1, 2, 3, 4, 5, 6])
COMBOS.append([0, 3])
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
ISLAND_QTY = 5  # 10
#
#  RUN 100 generations for each island
GENERATION_QTY = 10  # 100
#  HAVE 50 genomes start each generation
POPULATION_SIZE = 12  # 50
#  EACH genome engages each of the other genomes in the "attacker" role
#     EACH engagement is N plays, the final scores are tallied for fitness
PLAYS_PER_ENGAGEMENT = 1
#     WHEN a genome is in the defender role; it COULD have a % chance of wrong move
#        per round of play to mimic diversity, however it currently does not
#  AFTER ALL engagements are finished, extinct the bottom 60%
EXTINCTION_RATE = 0.45
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

EMPTY_PIT = 0
FULL_PIT = 1

GENE_MAP_SIZE = len(GENE_MAP)

PROTO_GENOME = {
    'id': 0,
    'score': -1000000,  # negative 1 million is below all possible scores
    'genes': [0] * len(GENE_MAP),
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


settings = {
    "ai_chosen": 1,
    "who_plays_first": 1,
    "first_player": 2,  # use inverse because we are from AI point of view
    "seeds_per_house_selection": 1,
    "seeds_per_house": 4,
    "capture_rule": 0,
    "eog_rule": 0,
    "seed_drop_rate": 0.4,
}


ALT_AI_LIST = [
    {
        "index": 1,
        "name": "USER ROLE",
        "rank": "1",
        "strategy": "negamax",  # options: "random", "negamax"
        "lookahead": 4,  # 1 to 6
        "error_rate": 0.00,  # 0.0 to 1.0; odds of making mistake
        "fitness": "balance",  # options: greed, caution, balance
        "desc": "test genome",
        "tagline": "",
        "tactics": "standard"
    },
    {
        "index": 2,
        "name": "AI ROLE",
        "rank": "1",
        "strategy": "negamax",  # options: "random", "negamax"
        "lookahead": 4,  # 1 to 6
        "error_rate": 0.00,  # 0.0 to 1.0; odds of making mistake
        "fitness": "balance",  # options: greed, caution, balance
        "desc": "test genome defender",
        "tagline": "",
        "tactics": "standard"
    },
]


game = None

def play_engagement(genome):
    score = 0
    for round in range(PLAYS_PER_ENGAGEMENT):
        game.reset_board()
        # game.play(verbose=False)
        while not game.is_over():
            if game.nplayer==1:
                # USER
                apply_genome(game.players[0], PROTO_GENOME)
                apply_genome(game.players[1], PROTO_GENOME)
            else:
                # AI
                apply_genome(game.players[0], genome)
                apply_genome(game.players[1], genome)
            move = game.get_move()
            game.play_move(move)
        result = game.strategic_scoring(2, 1) # we are scoring from AI perspective
        score += result
    final_score = score / PLAYS_PER_ENGAGEMENT
    return final_score

def do_extinction(genome_list):
    l = len(genome_list)
    last = int(l * (1.0 - EXTINCTION_RATE))
    new_list = genome_list[0:last]
    for genome in new_list:
        genome['life_span'] += 1
    return new_list

def do_reproduction(genome_list):
    global ID_CTR
    missing = POPULATION_SIZE - len(genome_list)
    if missing <= 0:
        return
    if not genome_list: # on first entry, the list is empty, so create an Adam/Eve
        new_genome = deepcopy(PROTO_GENOME)
        genome_list.append(new_genome)
    for _ in range(missing):
        parent = random.choice(genome_list)
        new_genome = deepcopy(parent)
        qty_changes = random.randint(1, 10)
        for _ in range(qty_changes):
            action = random.randint(1, 3)
            gene_select = random.randint(1, GENE_MAP_SIZE) - 1
            gene_type = GENE_MAP[gene_select][0]
            if action==1:
                # minor adjustment
                degree = random.choice([-1, 1])
                new_genome['genes'][gene_select] += degree
            elif action==2:
                # major adjustment
                if gene_type==EMPTY_AGAINST_FULL_PIT_VALUE:
                    degree = random.randint(-4, 4)
                else:
                    degree = random.randint(-2000, 2000)
                new_genome['genes'][gene_select] += degree
            elif action==3:
                # swap genes
                life_partner = random.choice(genome_list)
                new_genome['genes'][gene_select] = copy(life_partner['genes'][gene_select])
        new_genome['life_span'] = 0
        new_genome['parent_qty'] += 1
        new_genome['id'] = ID_CTR
        ID_CTR += 1
        new_genome['score'] = -1000000
        genome_list.append(new_genome)            
    return

def do_trials(genome_list):
    # opp_qty = len(genome_list) - 1
    opp_qty = 4
    for me, genome in enumerate(genome_list):
        # apply_genome(game.players[1], genome) # always apply to AI 
        print me, "GENOME", genome['id'], "ANCESTORS", genome["parent_qty"],
        print "LIFESPAN", genome['life_span'], "OLD_SCORE",
        if genome['score'] == -1000000:
            print "None"
        else:
            print genome['score']
        print "    CURRENT:", genome['genes']
        genome['score'] = play_engagement(genome)
        print "    SCORE", genome['score']
    return

def apply_genome(character, genome):
    t = character.get_tactics()
    build_tactics_from_list(t, genome['genes'])
    character.set_character()
    return

def do_sort(genome_list):
    new_list = sorted(genome_list, key=itemgetter('score'), reverse=True)
    return new_list


######################################
#
#  MAIN
#
######################################

if __name__=="__main__":

    for si, scenario in enumerate(SCENARIOS):
        #----------
        #
        #  JUMP PAST WORK DONE
        #
        #----------
        a, b, c, d, e = scenario
        filename = FILENAMES[si]
        print "FILE:", filename
        if os.path.exists(filename):
            print "    FILE ALREADY BUILT"
            continue
        if os.path.exists(filename+".lock"):
            print "    FILE ALREADY BEING WORKED ON"
            continue
        with open(filename+".lock", 'w') as outfile:
            outfile.write("lock")
        #-----------
        #
        #  SETUP SCENARIO
        #
        #-----------
        short = ""
        if a==1:
            settings['who_plays_first'] = 2
            short += "PLYR FIRST:"
        else:
            settings['who_plays_first'] = 1
            short += "AI FIRST  :"
        settings['seeds_per_house'] = b
        short += "SEEDS"+str(b)+":"
        ALT_AI_LIST[1]['lookahead'] = c
        short += "LOOK"+str(c)+":"
        settings["capture_rule"] = d
        short += "CAPTURE"+str(d)+":"
        settings["eog_rule"] = e
        short += "EOG"+str(e)
        game = gameengine.KalahGame(settings, testing=ALT_AI_LIST, verbose=False)
        #---------------------
        #
        # islands
        #
        #---------------------
        winner_list = []
        for island in range(ISLAND_QTY):
            genome_list = []
            #---------------------
            #
            # generations
            #
            #---------------------
            print "EVOLUTION OF ISLAND", island+1, "OF", ISLAND_QTY
            for gen in range(GENERATION_QTY):
                print "WORKING ON ", short
                print "ISLAND", island, "GENERATION", gen, "OF", GENERATION_QTY
                genome_list = do_extinction(genome_list)
                do_reproduction(genome_list)
                do_trials(genome_list)
                genome_list = do_sort(genome_list)
            # save the TOP10 winners on this island
            winner_list.extend(genome_list[0:10])
        #---------------------
        #
        # compete across the islands
        #
        #---------------------
        print "CHAMPIONSHIP FOR WORLD"
        for gen in range(GENERATION_QTY):
            print "CHAMPIONSHIP GEN", gen + 1, "OF", GENERATION_QTY
            do_trials(winner_list)          # for these rounds, START with trials
            winner_list = do_sort(winner_list)
            winner_list = do_extinction(winner_list)
            do_reproduction(winner_list)
        #--------------------
        #
        # save the WINNER
        #
        #--------------------
        winner_list = do_sort(winner_list)
        winner = winner_list[0]
        print "WINNER:"
        print "    ", winner
        print "WRITING", filename
        with open(filename, 'w') as outfile:
            json.dump(winner, outfile)
        os.remove(filename+".lock")
