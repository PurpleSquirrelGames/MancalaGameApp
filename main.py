import thread
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.factory import Factory 
from kivy.garden.progressspinner import ProgressSpinner
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.widget import Widget 

from fixedlayout import FixedLayout, FixedLayoutRoot, FixedImageButton
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

    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
        machine.bind_reference("kivy", self.ids)
        machine.change_state("init_game")

    def pushed_pit(self, pit):
        machine.input("pushed_pit", pit)


class MancalaApp(App):
    def build(self):
        presentation = Builder.load_file('mancala.kv')
        return presentation

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
        if self.ref["settings"]["user_first_player"]:
            self.change_state("start_user_turn")
        else:
            self.change_state("ai_thinking")


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

class StartUserTurn(State):

    def on_entry(self):
        self.ref["kivy"].center_message.text = "Player, choose a house."
        self.ref["choices_so_far"] = []
        self.change_state("wait_for_pit")

class WaitForPitButtons(State):

    def on_entry(self):
        display_board(self.ref['game'].board, self.ref['kivy'])
        self.possible_moves = self.ref["game"].possible_moves()

    def input(self, input_name, *args, **kwargs):
        if input_name=="pushed_pit":
            pit = args[0]
            index = len(self.ref['choices_so_far'])
            valid_move = any(grab(chlist, index)==pit for chlist in self.possible_moves)
            if valid_move:
                self.ref['kivy'].center_message.text = "playing house {}".format(pit)
                self.ref['choices_so_far'].append(pit)
                self.change_state("animate_user")
            else:
                self.ref['kivy'].center_message.text = "cannot play empty house. try again."
        else:
            print("WHAT IS A {} INPUT?".format(input_name))

class AnitmateUserChoiceState(State):

    def on_entry(self):
        possible_moves = self.ref["game"].possible_moves()
        current_choice = self.ref['choices_so_far'][-1]
        self.ref['kivy'].center_message.text = "animating user"
        done = any([chlist==self.ref['choices_so_far'] for chlist in possible_moves])
        if done:
            self.ref["game"].play_move(self.ref['choices_so_far'])
            self.ref["choices_so_far"] = []
            self.change_state("ai_thinking")
        else:
            self.ref['kivy'].center_message.text ="landed in store. play again."
            self.change_state("wait_for_pit")

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
        self.ref['kivy'].center_message.text = "animating {}".format(self.ref['ai_choices'])
        self.ref['game'].play_move(self.ref['ai_choices'])
        move_hand = Animation(pos_hint=(400, 300))+Animation(pos_hint=(500, 0))
        move_hand.bind(on_complete = self.done_moving_hand)
        move_hand.start(self.ref['kivy'].user_hand)

    def done_moving_hand(self, sequence, widget):
        if self.ref['game'].is_over():
            self.change_state("eog")
        else:
            self.change_state('start_user_turn')

    def on_exit(self):
        display_board(self.ref['game'].board, self.ref['kivy'])

class EndOfGameDisplayState(State):
    pass


if __name__=='__main__':
    game = KalahGame()
    machine.bind_reference("game", game)
    machine.bind_reference("settings", settings)
    machine.register_state(StartUserTurn("start_user_turn"))
    machine.register_state(PendingStartState("pending_start"))
    machine.register_state(InitGameState("init_game"))
    machine.register_state(WaitForPitButtons("wait_for_pit"))
    machine.register_state(AnitmateUserChoiceState("animate_user"))
    machine.register_state(AIThinkingState("ai_thinking"))
    machine.register_state(AnimateAIChoicesState("animate_ai"))
    machine.register_state(EndOfGameDisplayState("eog"))
    machine.start("pending_start")
    MancalaApp().run()
