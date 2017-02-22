from kivy.app import App
from kivy.clock import Clock
from kivy.factory import Factory 
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
        self.ref["game"].reset_board()
        if self.ref["settings"]["user_first_player"]:
            self.ref["kivy"].center_message.text = "Player, choose a house."
            self.change_state("wait_for_pit")
        else:
            self.change_state("ai_thinking")

    def on_exit(self):
        self.ref["choices_so_far"] = []

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
            #print count, pit_id, kivy_ids[pit_id].text

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
            self.change_state("wait_for_pit")

    def on_exit(self):
        display_board(self.ref['game'].board, self.ref['kivy'])

class AIThinkingState(State):
    
    def on_entry(self):
        self.ref['kivy'].center_message.text = "AI is thinking"
        self.ref['ai_choices'] = self.ref['game'].get_move()
        self.change_state("animate_ai")

class AnimateAIChoicesState(State):

    def on_entry(self):
        self.ref['kivy'].center_message.text = "animating {}".format(self.ref['ai_choices'])
        self.ref['game'].play_move(self.ref['ai_choices'])
        self.change_state('wait_for_pit')

    def on_exit(self):
        display_board(self.ref['game'].board, self.ref['kivy'])

class EndOfGameDisplayState(State):
    pass


if __name__=='__main__':
    game = KalahGame()
    machine.bind_reference("game", game)
    machine.bind_reference("settings", settings)
    machine.register_state(PendingStartState("pending_start"))
    machine.register_state(InitGameState("init_game"))
    machine.register_state(WaitForPitButtons("wait_for_pit"))
    machine.register_state(AnitmateUserChoiceState("animate_user"))
    machine.register_state(AIThinkingState("ai_thinking"))
    machine.register_state(AnimateAIChoicesState("animate_ai"))
    machine.register_state(EndOfGameDisplayState("eog"))
    machine.start("pending_start")
    MancalaApp().run()
