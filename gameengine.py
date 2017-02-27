import easyAI
from copy import copy

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

HOUSE=88
STORE=99

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
ALL_PITS = range(1, 14)

ACTION = "action"
COUNT = "count"
LOC = "loc"


class KalahHumanPlayer(easyAI.Human_Player):
    pass

class KalahAIPlayer(easyAI.AI_Player):
    pass

class KalahGame(easyAI.TwoPlayersGame):

    def __init__(self):
        self.players = [KalahHumanPlayer(), KalahAIPlayer(easyAI.Negamax(6))]
        self.nplayer = 1
        self.animate = []
        self.want_animation = True
        self.board = [0]*15
        self.seeds_per_house = 4
        self.board[HAND] = 12*self.seeds_per_house
        self.reset_board()

    def is_stopping_in_own_store(self, pit):
        count = self.board[pit] % 13  # if seeds > 12 then they wrap around board; so modulo 13
        return count == P[pit][DISTPIT][self.nplayer]
        
    def possible_moves(self):
        move_list = [[pit] for pit in self.possible_moves_choices()]
        completed_list = []
        self.recurse_moves(move_list, completed_list)
        return completed_list

    def recurse_moves(self, move_list, completed_list):
        for move in move_list:
            last_pit = move[-1]
            if self.is_stopping_in_own_store(last_pit):
                want_copy = self.want_animation
                self.want_animation = False
                board_copy = copy(self.board)
                self.make_move_choice(last_pit)
                more_choices = self.possible_moves_choices()
                if more_choices:
                    next_todo = []
                    for pit in more_choices:
                        next_todo.append(move+[pit])
                    self.recurse_moves(next_todo, completed_list)
                else:
                    completed_list.append(move)
                self.board = board_copy
                self.want_animation = want_copy
            else:
                completed_list.append(move)

    def possible_moves_choices(self):
        possible = []
        for house in HOUSE_LIST[self.nplayer]:
            if self.board[house]:
                possible.append(house)
        return possible

    def make_move(self, move):
        self.animate = []
        for pit in move:
            self.make_move_choice(pit)

    def make_move_choice(self, house):
        # scoop up the house chosen
        self._scoop(house)
        current_house = house
        # drop the seeds into the pits
        for ctr in range(self.board[HAND]):
            next_house = P[current_house][NEXT][self.nplayer]
            self._drop(next_house)
            current_house = next_house
        # steal if possible
        if self.board[current_house]==1:
            if P[current_house][OWNER]==self.nplayer:
                if P[current_house][ROLE]==HOUSE:
                    if self.board[P[current_house][OPP]]:
                        if self.want_animation:
                            self.animate.append({ACTION: "steal"})
                        self._scoop(current_house)
                        self._scoop(P[current_house][OPP])
                        self._drop_all(STORE_IDX[self.nplayer])
        # end of game scooping
        if self.is_over():
            if self.want_animation:
                self.animate.append({ACTION: "game_over"})
            # traditional end-of-game handling: both players scoop own houses into store
            for player in PLAYER_LIST:
                for house in HOUSE_LIST[player]:
                    if self.board[house]:
                        self._scoop(house)
                if self.board[HAND]:
                    self._drop_all(STORE_IDX[player])
    
    def is_over(self):
        for player in PLAYER_LIST:
            has_seed = False
            for house in HOUSE_LIST[player]:
                if self.board[house]:
                    has_seed = True
            if has_seed is False:
                return True
        return False

    def show(self):
        print "player: {} with score {}".format(self.nplayer, self.scoring())
        print "hand: {}".format(self.board[HAND])
        print "board:\n"
        print "          13   12   11   10   09   08      AI"
        print "         "+" ".join(
            ["[{:02d}]".format(self.board[pit]) for pit in reversed(HOUSE_LIST[AI])]
        )
        print "    [{:02d}]                               [{:02d}]".format(
            self.board[STORE_IDX[AI]], self.board[STORE_IDX[USER]]
        )
        print "         "+" ".join(
            ["[{:02d}]".format(self.board[pit]) for pit in HOUSE_LIST[USER]]
        )
        print "          01   02   03   04   05   06      USER"

    def scoring(self, player=None):
        if player is None:
            player = self.nplayer
        other = USER if player==AI else AI        
        return self.board[STORE_IDX[player]] - self.board[STORE_IDX[other]]

#    def unmake_move(self, move):
#        pass

    def ttentry(self):
        return "Mancala (Kalah) Game"

    def reset_board(self):
        for pit in ALL_PITS:
            if self.board[pit]:
                self._scoop(pit)
        for player in PLAYER_LIST:
            for pit in HOUSE_LIST[player]:
                self._drop(pit, count=self.seeds_per_house)

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
        user_score = self.scoring(player=USER)
        ai_score = self.scoring(player=AI)
        if user_score>ai_score:
            return USER
        if user_score<ai_score:
            return AI
        return 0

    def get_animation(self):
        return self.animate

    def usermove_start_simulation(self):
        self.animate = []
        self.original_board = copy(self.board)

    def usermove_simulate_choice(self, choices_so_far):
        self.animate = []
        current_choice = choices_so_far[-1]
        self.make_move_choice(current_choice)

    def usermove_finish_simulation(self):
        self.animate = []
        self.board = self.original_board


if __name__=="__main__":
    game = KalahGame()

    while not game.is_over():
        game.show()
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

