import easyAI

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

HOUSE=88
STORE=99

P = {
     1: {OWNER: USER, NEXT: {USER:  2, AI:  2}, ROLE: HOUSE, OPP: 13},
     2: {OWNER: USER, NEXT: {USER:  3, AI:  3}, ROLE: HOUSE, OPP: 12},
     3: {OWNER: USER, NEXT: {USER:  4, AI:  4}, ROLE: HOUSE, OPP: 11},
     4: {OWNER: USER, NEXT: {USER:  5, AI:  5}, ROLE: HOUSE, OPP: 10},
     5: {OWNER: USER, NEXT: {USER:  6, AI:  6}, ROLE: HOUSE, OPP:  9},
     6: {OWNER: USER, NEXT: {USER:  7, AI:  8}, ROLE: HOUSE, OPP:  8},
     7: {OWNER: USER, NEXT: {USER:  8, AI:  8}, ROLE: STORE, OPP: None},
     8: {OWNER: AI  , NEXT: {USER:  9, AI:  9}, ROLE: HOUSE, OPP:  6},
     9: {OWNER: AI  , NEXT: {USER: 10, AI: 10}, ROLE: HOUSE, OPP:  5},
    10: {OWNER: AI  , NEXT: {USER: 11, AI: 11}, ROLE: HOUSE, OPP:  4},
    11: {OWNER: AI  , NEXT: {USER: 12, AI: 12}, ROLE: HOUSE, OPP:  3},
    12: {OWNER: AI  , NEXT: {USER: 13, AI: 13}, ROLE: HOUSE, OPP:  2},
    13: {OWNER: AI  , NEXT: {USER:  1, AI: 14}, ROLE: HOUSE, OPP:  1},
    14: {OWNER: AI  , NEXT: {USER:  1, AI:  1}, ROLE: STORE, OPP: None},
}
ALL_PITS = range(1, 14)

class KalahHumanPlayer(easyAI.Human_Player):
    pass

class KalahAIPlayer(easyAI.AI_Player):
    pass

class KalahGame(easyAI.TwoPlayersGame):

    def __init__(self, players):
        self.players = players
        self.nplayer = 1
        self.board = [0]*15
        self.seeds_per_house = 4
        self.board[HAND] = 12*self.seeds_per_house
        self.reset_board()
        
    def possible_moves(self):
        return self.possible_moves_choices()

    def possible_moves_choices(self):
        possible = []
        for house in HOUSE_LIST[self.nplayer]:
            if self.board[house]:
                possible.append(house)
        return possible

    def make_move(self, house):
        house = int(house)
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
                        self._scoop(current_house)
                        self._scoop(P[current_house][OPP])
                        self._drop_all(STORE_IDX[self.nplayer])
    
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

    def scoring(self):
        return self.board[STORE_IDX[self.nplayer]] - self.board[STORE_IDX[self.nopponent]]

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

    def _drop(self, pit, count=1):
        self.board[HAND] -= count
        self.board[pit] += count

    def _drop_all(self, pit):
        self.board[pit] += self.board[HAND]
        self.board[HAND] = 0


if __name__=="__main__":
    human = KalahHumanPlayer()
    other_human = KalahHumanPlayer()
    game = KalahGame([human, other_human])

    game.play()
