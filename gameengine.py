import easyAI
from easyAI.AI.DictTT import DictTT
from easyAI import TT
from copy import copy
import random
from characters import AI_LIST
from tactics import Tactics

USER = 1
AI = 2

PLAYER_LIST = [USER, AI]

#
#   BOARD LAYOUT
#
#     13   12   11   10   09   08        AI
# 14                               07
#     01   02   03   04   05   06        USER
#
# HAND = 00

HOUSE_LIST = {
    USER: [1, 2, 3, 4, 5, 6],
    AI: [8, 9, 10, 11, 12, 13]
}
STORE_IDX = {
    USER: 7,
    AI: 14
}
HAND = 0


OWNER = 0
NEXT = 1
ROLE = 2
OPP = 3
DISTPIT = 4

HOUSE = 88
STORE = 99

#     13   12   11   10   09   08        AI
# 14                               07
#     01   02   03   04   05   06        USER
P = {
     1: {OWNER: USER, NEXT: {USER:  2, AI:  2}, ROLE: HOUSE, OPP: 13, DISTPIT: {USER:  6, AI: 12}},
     2: {OWNER: USER, NEXT: {USER:  3, AI:  3}, ROLE: HOUSE, OPP: 12, DISTPIT: {USER:  5, AI: 11}},
     3: {OWNER: USER, NEXT: {USER:  4, AI:  4}, ROLE: HOUSE, OPP: 11, DISTPIT: {USER:  4, AI: 10}},
     4: {OWNER: USER, NEXT: {USER:  5, AI:  5}, ROLE: HOUSE, OPP: 10, DISTPIT: {USER:  3, AI:  9}},
     5: {OWNER: USER, NEXT: {USER:  6, AI:  6}, ROLE: HOUSE, OPP:  9, DISTPIT: {USER:  2, AI:  8}},
     6: {OWNER: USER, NEXT: {USER:  7, AI:  8}, ROLE: HOUSE, OPP:  8, DISTPIT: {USER:  1, AI:  7}},
     7: {OWNER: USER, NEXT: {USER:  8, AI:  8}, ROLE: STORE, OPP: -1, DISTPIT: None},
     8: {OWNER: AI  , NEXT: {USER:  9, AI:  9}, ROLE: HOUSE, OPP:  6, DISTPIT: {USER: 12, AI:  6}},
     9: {OWNER: AI  , NEXT: {USER: 10, AI: 10}, ROLE: HOUSE, OPP:  5, DISTPIT: {USER: 11, AI:  5}},
    10: {OWNER: AI  , NEXT: {USER: 11, AI: 11}, ROLE: HOUSE, OPP:  4, DISTPIT: {USER: 10, AI:  4}},
    11: {OWNER: AI  , NEXT: {USER: 12, AI: 12}, ROLE: HOUSE, OPP:  3, DISTPIT: {USER:  9, AI:  3}},
    12: {OWNER: AI  , NEXT: {USER: 13, AI: 13}, ROLE: HOUSE, OPP:  2, DISTPIT: {USER:  8, AI:  2}},
    13: {OWNER: AI  , NEXT: {USER:  1, AI: 14}, ROLE: HOUSE, OPP:  1, DISTPIT: {USER:  7, AI:  1}},
    14: {OWNER: AI  , NEXT: {USER:  1, AI:  1}, ROLE: STORE, OPP: -1, DISTPIT: None},
}
ALL_PITS = range(1, 15)

OWN_PITS_FROM_STORE = [
    None,
    [6, 5, 4, 3, 2, 1],
    [13, 12, 11, 10, 9, 8],
]

ACTION = "action"
COUNT = "count"
LOC = "loc"

BALANCE = 0
GREED = 1
CAUTION = 2

EMPTY = 0
FULL = 1

INF = float("inf")

class MancalaAI(easyAI.NonRecursiveNegamax, object):

    def __init__(self, settings, testing=False, tt=None, defender_role=False):
        self.settings = settings
        self.testing = testing
        self.defender_role = defender_role
        self.tactics = Tactics()
        self.set_character()
        super(MancalaAI, self).__init__(self.character['lookahead'], tt=self.tt)

    def set_character(self):
        if self.testing:
            if self.defender_role:
                self.character = self.testing[1]
            else:
                self.character = self.testing[0]
        else:
            self.character = AI_LIST[self.settings["ai_chosen"]]
        self.depth = self.character['lookahead']
        self.tt = None
        self.tactics.remap(self.character, self.settings)
        #

    def __call__(self, game):
        if self.character['strategy'] == "random":
            # this is only used by Maisy
            possible_moves = game.possible_moves()
            shortest_length = min([len(m) for m in possible_moves])
            shortest_moves = [m for m in possible_moves if len(m)==shortest_length]
            return random.choice(shortest_moves)
        if self.character['error_rate'] > 0.0:
            chance = random.random()
            if chance < self.character['error_rate']:
                possible_moves = game.possible_moves()
                return random.choice(possible_moves)
        return super(MancalaAI, self).__call__(game)


class KalahHumanPlayer(easyAI.Human_Player):
    def get_tactics(self):
        return None


class KalahAIPlayer(easyAI.AI_Player):

    def set_character(self):
        self.AI_algo.set_character()

    def get_tactics(self):
        return self.AI_algo.tactics


class KalahGame(easyAI.TwoPlayersGame):

    def __init__(self, settings, testing=False, verbose=True):
        self.testing = testing
        self.settings = settings
        self.verbose = verbose
        if self.testing:
            self.players = [
                KalahAIPlayer(MancalaAI(
                    self.settings,
                    testing=testing
                )),
                KalahAIPlayer(MancalaAI(
                    self.settings,
                    testing=testing,
                    defender_role=True
                ))
            ]
        else:
            self.players = [
                KalahHumanPlayer(),
                KalahAIPlayer(MancalaAI(self.settings))
            ]
        self.set_character()
        self.nplayer = self.settings['first_player']
        self.animate = []
        self.want_animation = False
        self.board = [0] * 15
        self.reset_board(empty=True)

    def set_character(self):
        self.character = AI_LIST[self.settings["ai_chosen"]]
        self.players[1].set_character()

    def is_stopping_in_own_store(self, pit):
        count = self.board[pit] % 13  # if seeds > 12 then they wrap around board; so modulo 13
        return count == P[pit][DISTPIT][self.nplayer]

    def ttentry(self):
        return tuple(self.board)

    def ttrestore(self, entry_tuple):
        for index in range(len(self.board)):
            self.board[index] = entry_tuple[index]

    def possible_moves(self):
        move_list = [[pit] for pit in self.possible_moves_choices()]
        completed_list = []
        self.recurse_moves(move_list, completed_list)
        return completed_list

    def recurse_moves(self, move_list, completed_list):
        for move in move_list:
            last_pit = move[-1]
            if self.is_stopping_in_own_store(last_pit):
                board_copy = copy(self.board)
                self.make_move_choice(last_pit)
                more_choices = self.possible_moves_choices()
                if more_choices:
                    next_todo = []
                    for pit in more_choices:
                        next_todo.append(move + [pit])
                    self.recurse_moves(next_todo, completed_list)
                else:
                    completed_list.append(move)
                self.board = board_copy
            else:
                completed_list.append(move)

    def possible_moves_choices(self):
        possible = []
        for house in HOUSE_LIST[self.nplayer]:
            if self.board[house]:
                possible.append(house)
        return possible

    def animated_play_move(self, move):
        self.want_animation = True
        self.play_move(move)
        self.want_animation = False

    def make_move(self, move):
        self.animate = []
        for pit in move:
            self.make_move_choice(pit)

    def make_move_choice(self, house):
        if self.want_animation:
            self.animate.append({ACTION: "normal_move", LOC: house})
        # scoop up the house chosen
        self._scoop(house)
        current_house = house
        # drop the seeds into the pits
        for ctr in range(self.board[HAND]):
            next_house = P[current_house][NEXT][self.nplayer]
            self._drop(next_house)
            current_house = next_house
        #
        # capture if possible
        #
        if self.settings['capture_rule'] == 0:  # capture if opposite is full
            if self.board[current_house] == 1:
                if P[current_house][OWNER] == self.nplayer:
                    if P[current_house][ROLE] == HOUSE:
                        if self.board[P[current_house][OPP]]:
                            if self.want_animation:
                                self.animate.append({ACTION: "steal"})
                            self._scoop(P[current_house][OPP])
                            self._scoop(current_house)
                            self._drop_all(STORE_IDX[self.nplayer])
        elif self.settings['capture_rule'] == 1:  # capture even if opposite is empty
            if self.board[current_house] == 1:
                if P[current_house][OWNER] == self.nplayer:
                    if P[current_house][ROLE] == HOUSE:
                        if self.want_animation:
                            self.animate.append({ACTION: "steal"})
                        if self.board[P[current_house][OPP]]:
                            self._scoop(P[current_house][OPP])
                        self._scoop(current_house)
                        self._drop_all(STORE_IDX[self.nplayer])
        # elif settings['capture_rule'] == 2: # no capture
        #     pass
        #
        # end of game scooping
        #
        if self.is_over():
            if self.want_animation:
                self.animate.append({ACTION: "game_over"})
            if self.settings['eog_rule'] == 0:
                # traditional end-of-game handling: both players scoop own houses into store
                for player in PLAYER_LIST:
                    for house in HOUSE_LIST[player]:
                        if self.board[house]:
                            self._scoop(house)
                    if self.board[HAND]:
                        self._drop_all(STORE_IDX[player])
            elif self.settings['eog_rule'] == 1:
                # put seed in store of player who does not have seeds
                if any([self.board[house] for house in HOUSE_LIST[USER]]):
                    empty_player = AI
                else:
                    empty_player = USER
                for player in PLAYER_LIST:
                    for house in HOUSE_LIST[player]:
                        if self.board[house]:
                            self._scoop(house)
                    if self.board[HAND]:
                        self._drop_all(STORE_IDX[empty_player])
            elif self.settings['eog_rule'] == 2:
                # put seeds in store of player who ended game (current player)
                for player in PLAYER_LIST:
                    for house in HOUSE_LIST[player]:
                        if self.board[house]:
                            self._scoop(house)
                    if self.board[HAND]:
                        self._drop_all(STORE_IDX[self.nplayer])
            elif self.settings['eog_rule'] == 3:
                # leave seeds alone
                # just place in hand for proper scoring; don't animate this ever
                temp = self.want_animation
                self.want_animation = False
                for player in PLAYER_LIST:
                    for house in HOUSE_LIST[player]:
                        if self.board[house]:
                            self._scoop(house)
                self.want_animation = temp  # restore

    def is_over(self):
        for player in PLAYER_LIST:
            has_seed = False
            for house in HOUSE_LIST[player]:
                if self.board[house]:
                    has_seed = True
            if has_seed is False:
                return True
        return False

    def show(self, full=False):
        print "player: {} with score {}".format(self.nplayer, self.scoring())
        if full:
            print "    tactical: "
            for line in self.trace:
                print "        {}".format(line)
        print "hand: {}".format(self.board[HAND])
        print "board:\n"
        print "          13   12   11   10   09   08      AI"
        print "         " + " ".join(
            ["[{:02d}]".format(self.board[pit]) for pit in reversed(HOUSE_LIST[AI])]
        )
        print "    [{:02d}]                               [{:02d}]".format(
            self.board[STORE_IDX[AI]], self.board[STORE_IDX[USER]]
        )
        print "         " + " ".join(
            ["[{:02d}]".format(self.board[pit]) for pit in HOUSE_LIST[USER]]
        )
        print "          01   02   03   04   05   06      USER"

    def scoring(self, player=None):
        if self.is_over():
            s = self.strategic_scoring(self.nplayer, self.nopponent)
            if s > 0:
                t = 9000
            else:
                t = -9000
        else:
            if self.character['fitness'] == "caution":
                s = self.caution_scoring(player)
            elif self.character['fitness'] == "greed":
                s = self.greed_scoring(player)
            else:
                s = self.strategic_scoring(self.nplayer, self.nopponent)
            t = self.tactical_scoring(self.nplayer, self.nopponent)
        return s + t

    def strategic_scoring(self, player, opponent):
        raw_score = self.board[STORE_IDX[player]] - self.board[STORE_IDX[opponent]]
        return raw_score * 1000

    def caution_scoring(self, player):
        raw_score = self.board[STORE_IDX[USER]]
        if self.player==AI:
            raw_score *= -1
        return raw_score * 1000

    def greed_scoring(self, player):
        raw_score = self.board[STORE_IDX[AI]]
        if self.player==USER:
            raw_score *= -1
        return raw_score * 1000

    def tactical_scoring(self, player, opponent):
        '''
            Measure the relative value of a board layout in terms
            of short-term tactics.

            Because we are using MiniMax (Negamax), it is critical that
            the measure be zero sum. A advantage for one player must
            exactly equal the disadvantage fo the other player.
        '''
        # leaving empty pits on own side
        if True: self.trace = []
        if self.character['tactics'] == "blind":
            if True: self.trace.append("+0 BLIND TACTICS")
            return 0
        tactics = self.players[player - 1].get_tactics()
        if not tactics:
            return 0
        score = 0
        for dist, pit in enumerate(OWN_PITS_FROM_STORE[player]):
            if self.board[pit]==0:
                opp_count = self.board[P[pit][OPP]]
                if opp_count:
                    score += tactics.empty_pit_value[dist][FULL] * opp_count
                    if True: self.trace.append("+{} OWN EMPTY/FULL PIT {} cnt={}".format(tactics.empty_pit_value[dist][FULL] * opp_count, pit, opp_count))
                else:
                    score += tactics.empty_pit_value[dist][EMPTY]
                    if True: self.trace.append("+{} OWN EMPTY/EMPTY PIT {}".format(tactics.empty_pit_value[dist][EMPTY], pit))
        for dist, pit in enumerate(OWN_PITS_FROM_STORE[opponent]):
            if self.board[pit]==0:
                opp_count = self.board[P[pit][OPP]]
                if opp_count:
                    score -= tactics.empty_pit_value[dist][FULL] * opp_count
                    if True: self.trace.append("-{} OPP EMPTY/FULL PIT {} cnt={}".format(tactics.empty_pit_value[dist][FULL] * opp_count, pit, opp_count))
                else:
                    score -= tactics.empty_pit_value[dist][EMPTY]
                    if True: self.trace.append("-{} OPP EMPTY/EMPTY PIT {}".format(tactics.empty_pit_value[dist][EMPTY], pit))
        # easy repeat patterns seen
        for dist, pit in enumerate(OWN_PITS_FROM_STORE[player]):
            if self.board[pit] == (dist + 1):
                score += tactics.easy_repeat_value[dist]
                if True: self.trace.append("+{} OWN EASY REPEAT AT {}".format(tactics.easy_repeat_value[dist], pit))
        for dist, pit in enumerate(OWN_PITS_FROM_STORE[opponent]):
            if self.board[P[pit][OPP]] == (dist + 1):
                score -= tactics.easy_repeat_value[dist]
                if True: self.trace.append("-{} OPP EASY REPEAT AT {}".format(tactics.easy_repeat_value[dist], pit))
        return score

#    def unmake_move(self, move):
#        pass

    def reset_board(self, restoration=False, empty=False):
        self.want_animation = True
        #
        # manipulate basic settings
        #
        self.seeds_per_house = self.settings['seeds_per_house']
        #
        # manipulate board
        #
        if self.want_animation:
            self.animate = [{ACTION: "setting_up"}]
        # determine new board
        if restoration:
            new_board = copy(self.board)
            self.board = [12 * self.seeds_per_house] + [0] * 14
        else:
            if empty:
                self.board = [12 * self.seeds_per_house] + [0] * 14
                new_board = copy(self.board)
            else:
                new_board = [0] + \
                            [self.seeds_per_house] * 6 + [0] + \
                            [self.seeds_per_house] * 6 + [0]
        for pit in ALL_PITS:
            if self.board[pit]:
                self._scoop(pit)
        for pit in ALL_PITS:
            if new_board[pit]:
                self._drop(pit, count=new_board[pit])
        self.board[HAND] = 0  # this is for error recovery. In theory, you
                              # should never needs this as the hand will be
                              # empty already.
        #
        # manipulate AI character
        #
        self.set_character()
        #
        # set nplayer
        #
        if not restoration:
            self.nplayer = self.settings['first_player']
        self.want_animation = False

    def _scoop(self, pit):
        self.board[HAND] += self.board[pit]
        self.board[pit] = 0
        if self.want_animation:
            self.animate.append({ACTION: "scoop", LOC: pit})

    def _drop(self, pit, count=1):
        self.board[HAND] -= count
        self.board[pit] += count
        if self.want_animation:
            self.animate.append({ACTION: "drop", LOC: pit, COUNT: count})

    def _drop_all(self, pit):
        count = self.board[HAND]
        self.board[pit] += self.board[HAND]
        self.board[HAND] = 0
        if self.want_animation:
            self.animate.append({ACTION: "drop_all", LOC: pit, COUNT: count})

    def get_winner(self):
        user_score = self.strategic_scoring(USER, AI)
        if user_score > 0:
            return USER
        if user_score < 0:
            return AI
        return 0

    def get_animation(self):
        return self.animate

    def usermove_start_simulation(self):
        self.want_animation = True
        self.animate = []
        self.original_board = copy(self.board)

    def usermove_simulate_choice(self, choices_so_far):
        self.animate = []
        current_choice = choices_so_far[-1]
        self.make_move_choice(current_choice)

    def usermove_finish_simulation(self):
        self.animate = []
        self.board = self.original_board
        self.want_animation = False


if __name__=="__main__":
    settings = {
        "ai_chosen": 4,
        "who_plays_first": 0,
        "first_player": USER,
        "seeds_per_house_selection": 1,
        "seeds_per_house": 4,
        "capture_rule": 0,
        "eog_rule": 0,
        "seed_drop_rate": 0.4,
    }
    character = AI_LIST[settings['ai_chosen']]

    game = KalahGame(settings)
    game.reset_board()

    while not game.is_over():
        # print game.animate
        game.show(full=True)
        if game.nplayer==USER:
            poss = game.possible_moves()
            for index, move in enumerate(poss):
                print index, move
            index = int(input("enter move:"))
            move = poss[index]
        else:
            move = game.get_move()
            print "AI plays", move
        game.play_move(move)
    print
    print "GAME OVER!"
    print
    print game.show()
    print
    print "RESULT:", ["TIE", "USER WON", "AI WON"][game.get_winner()]

