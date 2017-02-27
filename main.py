import thread
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.factory import Factory 
from kivy.garden.progressspinner import ProgressSpinner
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget 

from fixedlayout import FixedLayout, FixedLayoutRoot, FixedImage, FixedImageButton
from simplestate import StateMachine, State
from gameengine import KalahGame

__version__ = '0.0.6'

machine = StateMachine(debug=True)

settings = {
    "user_first_player": True
}

##############################
#
#  KIVY CLASSES
#
##############################

class GameScreen(FixedLayoutRoot):
    global machine

    HANDS = [
        {}, # 0, nobody
        {"pos": (500, 0)},       # 1 user
        {"pos": (500, 1080)}     # 2 ai
    ]

    PITS = [
        {}, #  0, hand (ignore)
        {"pos": (430,  350)}, #  1
        {"pos": (640,  350)}, #  2
        {"pos": (850,  350)}, #  3
        {"pos": (1060, 350)}, #  4
        {"pos": (1270, 350)}, #  5
        {"pos": (1480, 350)}, #  6
        {"pos": (1690, 350)}, #  7 user store
        {"pos": (1480, 770)}, #  8
        {"pos": (1270, 770)}, #  9
        {"pos": (1060, 770)}, # 10
        {"pos": (850,  770)}, # 11
        {"pos": (640,  770)}, # 12
        {"pos": (430,  770)}, # 13
        {"pos": (220,  770)}, # 14 ai store
    ]

    def pushed_pit(self, pit):
        machine.input("pushed_pit", pit)


class MancalaApp(App):
    def build(self):
        self.presentation = Builder.load_file('mancala.kv')
        return self.presentation

    def on_start(self):
        machine.bind_reference("kivy", self.presentation.ids)
        machine.change_state("init_game")

def build_animation(player, steps):
    hand_list = []
    message_list = []
    pit_pos = GameScreen.HANDS[player]["pos"]
    text = ""
    for step in steps:
        if step['action']=="scoop":
            pit_pos = GameScreen.PITS[step["loc"]]["pos"]
        if step['action']=="drop":
            pit_pos = GameScreen.PITS[step["loc"]]["pos"]
        if step['action']=="drop_all":
            pit_pos = GameScreen.PITS[step["loc"]]["pos"]
        if step['action']=="steal":
            text = "Stealing!"
        if step['action']=="game_over":
            text = "Handling End of Game"
        message_list.append(text)
        hand_list.append(Animation(pos_hint=pit_pos))
    hand_list.append(Animation(pos_hint=GameScreen.HANDS[player]["pos"]))
    message_list.append(text)
    return hand_list, message_list

##############################
#
#  SIMPLE STATE CLASSES
#
##############################

class PendingStartState(State):
    pass

class InitGameState(State):

    def on_entry(self):
        self.ref['kivy'].wait_on_ai.stop_spinning()
        self.ref["game"].reset_board()
        return self.change_state("start_turn")


def grab(alist, index):
    try:
        return alist[index]
    except IndexError:
        return None

def display_board(board, kivy_ids):
    for pit, count in enumerate(board):
        if pit > 0:
            pit_id = "counter,{}".format(pit)
            kivy_ids[pit_id].text = str(count)

class StartTurn(State):

    def on_entry(self):
        self.ref["choices_so_far"] = []
        self.ref["ai_choices"] = []
        if self.ref["game"].is_over():
            return self.change_state("eog")
        if self.ref["game"].nplayer==1:
            self.ref["kivy"].center_message.text = "Player, choose a house."
            self.ref["game"].usermove_start_simulation()
            self.ref["possible_user_moves"] = self.ref["game"].possible_moves()
            return self.change_state("wait_for_pit")
        return self.change_state("ai_thinking")

class WaitForPitButtons(State):

    def on_entry(self):
        display_board(self.ref['game'].board, self.ref['kivy'])

    def input(self, input_name, *args, **kwargs):
        if input_name=="pushed_pit":
            pit = args[0]
            index = len(self.ref['choices_so_far'])
            valid_move = any(grab(chlist, index)==pit for chlist in self.ref["possible_user_moves"])
            if valid_move:
                self.ref['kivy'].center_message.text = "playing house {}".format(pit)
                self.ref['choices_so_far'].append(pit)
                self.change_state("animate_user")
            else:
                self.ref['kivy'].center_message.text = "cannot play empty house. try again."

class AnitmateUserChoiceState(State):

    def on_entry(self):
        self.ref["game"].usermove_simulate_choice(self.ref['choices_so_far'])
        (self.move_list, self.message_list) = build_animation(
            self.ref["game"].nplayer, 
            self.ref["game"].get_animation()
        )
        self.idx = 0
        self.done_moving_hand(None, None)

    def done_moving_hand(self, sequence, widget):
        if self.idx<len(self.move_list):
            self.move_list[self.idx].bind(on_complete = self.done_moving_hand)
            self.move_list[self.idx].start(self.ref['kivy'].user_hand)
            self.ref['kivy'].center_message.text = self.message_list[self.idx]
            self.idx += 1
            return self.same_state
        possible_moves = self.ref["possible_user_moves"]
        done = any([chlist==self.ref['choices_so_far'] for chlist in possible_moves])
        if done:
            self.ref["game"].usermove_finish_simulation()
            self.ref["game"].play_move(self.ref['choices_so_far'])
            return self.change_state("start_turn")
        self.ref['kivy'].center_message.text ="landed in store. play again."
        return self.change_state("wait_for_pit")

    def on_exit(self):
        display_board(self.ref['game'].board, self.ref['kivy'])


def get_ai_move():
    global game
    global machine
    choices = game.get_move()
    machine.input("ai_move", choices)


class AIThinkingState(State):
    
    def on_entry(self):
        self.ref['kivy'].center_message.text = "AI is thinking"
        self.ref['kivy'].wait_on_ai.start_spinning()
        thread.start_new_thread(get_ai_move, ())

    def input(self, input_name, *args, **kwargs):
        if input_name == "ai_move":
            self.ref["ai_choices"] = args[0]
            self.ref["kivy"].wait_on_ai.stop_spinning()
            self.change_state("animate_ai")

class AnimateAIChoicesState(State):

    def on_entry(self):
        self.ref['game'].play_move(self.ref['ai_choices'])
        (self.move_list, self.message_list) = build_animation(
            self.ref["game"].nplayer, 
            self.ref["game"].get_animation()
        )
        self.idx = 0
        self.done_moving_hand(None, None)

    def done_moving_hand(self, sequence, widget):
        if self.idx<len(self.move_list):
            self.move_list[self.idx].bind(on_complete = self.done_moving_hand)
            self.move_list[self.idx].start(self.ref['kivy'].ai_hand)
            self.ref['kivy'].center_message.text = self.message_list[self.idx]
            self.idx += 1
            return self.same_state
        self.change_state('start_turn')

    def on_exit(self):
        display_board(self.ref['game'].board, self.ref['kivy'])

class EndOfGameDisplayState(State):

    def on_entry(self):
        winner = self.ref['game'].get_winner()    
        self.ref["kivy"].center_message.text = ["Tie Game.", "You won!", "AI won."][game.get_winner()]


if __name__=='__main__':
    game = KalahGame()
    machine.bind_reference("game", game)
    machine.bind_reference("settings", settings)
    machine.register_state(StartTurn("start_turn"))
    machine.register_state(PendingStartState("pending_start"))
    machine.register_state(InitGameState("init_game"))
    machine.register_state(WaitForPitButtons("wait_for_pit"))
    machine.register_state(AnitmateUserChoiceState("animate_user"))
    machine.register_state(AIThinkingState("ai_thinking"))
    machine.register_state(AnimateAIChoicesState("animate_ai"))
    machine.register_state(EndOfGameDisplayState("eog"))
    machine.start("pending_start")
    MancalaApp().run()
