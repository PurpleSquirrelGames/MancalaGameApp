import thread
import random
import webbrowser
from copy import copy
from kivy.app import App
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.factory import Factory 
from kivy.garden.progressspinner import ProgressSpinner
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition
from kivy.uix.widget import Widget 

from kivy.uix.floatlayout import FloatLayout

from fixedlayout import FixedLayout, FixedPopup, FixedRadioButtons, \
    FixedSimpleMenu, FixedSimpleMenuItem

from simplestate import StateMachine, State
from gameengine import KalahGame
from characters import AI_LIST
from coordinates import PIT_ARRANGEMENT, SEED_DICT

__version__ = '0.0.14'

machine = StateMachine(debug=True)

seeds = None

storage = JsonStore('mancala.json')

USER = 1
AI = 2

PARKED = (2000, 2000)
HAND = 0

X = 0
Y = 1

#############################
#
#  SETTINGS
#
#############################

settings = {
    "ai_chosen": 0,
    "who_plays_first": 0,
    "first_player": USER,
    "seeds_per_house_selection": 1,
    "seeds_per_house": 4,
    "capture_rule": 0,
    "eog_rule": 0,
    "animation_speed_choice": 1,
    "seed_drop_rate": 0.4,
    "board_choice": 0,
    "background": 0,
    "seed_choice": 0,
    "notification_volume": 2,
    "seed_volume": 2,
    "best_level": 0
}

current = {
    'ai_viewed': 0,
    'first_time_flag': False,
    'allow_resume': False
}

if storage.exists('settings'):
    settings = storage.get('settings')
else:
    storage.put('settings', **settings)
    current['first_time_flag'] = True

current['ai_viewed'] = settings['ai_chosen']

character = AI_LIST[settings['ai_chosen']]

visual_settings = {
    "who_plays_first": [
        "You",
        "Opponent (AI)"
    ],
    "seeds_per_house_selection": [
        "3",
        "4",
        "5",
        "6"
    ],
    "capture_rule": [
        "Capture if opposite house has seeds",
        "Always capture (even if opposite empty)",
        "Never allow capture"
    ],
    "eog_rule": [
        "Move seeds to the store/Kalaha on that side",
        "Move seeds to the player with empty houses",
        "Move seeds to the player that ended the game",
        "Leave the seeds in the houses"
    ],
    "board_choice": [
        "Walnut",
        "Birch"
    ],
    "background": [
        "Green Linen",
        "White Table"
    ],
    "seed_choice": [
        "Teal Green Glass Gems",
        "Tumbled Pebbles",
        "Black River Rock"
    ],
    "animation_speed_choice": [
        "Fast",
        "Medium",
        "Slow"
    ],
    "notification_volume": [
        "Mute",
        "Soft",
        "Medium",
        "Loud"
    ],
    "seed_volume": [
        "Mute",
        "Soft",
        "Medium",
        "Loud"
    ]
}

def update_setting(setting_name, value):
    global settings
    global visual_settings
    global character
    global app
    global seeds

    # yes, this routine IS called even without a real change
    if value == settings[setting_name]:
        change_seen = False
    else:
        change_seen = True
        settings[setting_name] = value

    if setting_name == "ai_chosen":
        settings["ai_chosen"] = value
        character = AI_LIST[value]
        seeds.change_ai_pictures("{:02d}".format(character['index']))
        if change_seen:
            disable_resume_game()
    if setting_name == "who_plays_first":
        if value == 0:
            settings["first_player"] = USER
        else:
            settings["first_player"] = AI
        app.root.screens[SETTINGS_RULES_SCREEN].ids.rules_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
        if change_seen:
            disable_resume_game()
    if setting_name == "seeds_per_house_selection":
        settings["seeds_per_house"] = value + 3
        app.root.screens[SETTINGS_RULES_SCREEN].ids.rules_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
        if change_seen:
            disable_resume_game()
    if setting_name == "capture_rule":
        app.root.screens[SETTINGS_RULES_SCREEN].ids.rules_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
        if change_seen:
            disable_resume_game()
    if setting_name == "eog_rule":
        app.root.screens[SETTINGS_RULES_SCREEN].ids.rules_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
        if change_seen:
            disable_resume_game()
    if setting_name == "seed_choice":
        seeds.change_picture()
        app.root.screens[SETTINGS_SCREEN_SCREEN].ids.screen_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
    if setting_name == "board_choice":
        app.root.screens[SETTINGS_SCREEN_SCREEN].ids.screen_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
    if setting_name == "background":
        app.root.screens[SETTINGS_SCREEN_SCREEN].ids.screen_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
    if setting_name in ["board_choice", "background"]:
        wood = ["walnut", "birch"][settings["board_choice"]]
        color = ["green", "white"][settings["background"]]
        filename = 'assets/img/{}-board-{}.png'.format(wood, color)
        app.root.screens[GAME_SCREEN].ids.board_image.source = filename
    if setting_name == "animation_speed_choice":
        settings["seed_drop_rate"] = 0.1 + value*0.3
        app.root.screens[SETTINGS_SCREEN_SCREEN].ids.screen_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
    if setting_name == "notification_volume":
        app.root.screens[SETTINGS_SOUND_SCREEN].ids.sound_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
    if setting_name == "seed_volume":
        app.root.screens[SETTINGS_SOUND_SCREEN].ids.sound_screen_menu.\
            set_text(setting_name, visual_settings[setting_name][value])
    storage.put('settings', **settings)


def save_game(force_new_game=False):
    global machine
    global game

    game_state = {}
    if machine.get_state() not in ["pending_start", "init_game", "eog"]:
        if not force_new_game:
            game_state["active_game"] = True
        else:
            game_state["active_game"] = False
    else:
        game_state["active_game"] = False
    game_state["board"] = game.board
    game_state["turn"] = game.nplayer
    storage.put('game_state', **game_state)

def restore_game():
    global game

    game.restoration = False
    if not storage.exists('game_state'):
        return
    game_state = storage.get('game_state')
    if not game_state['active_game']:
        return
    game.board = game_state['board']
    game.nplayer = game_state['turn']
    game.restoration = True

def enable_resume_game():
    global current
    p = "assets/img/blank-wood-button.png"
    t = "Resume"
    app.root.screens[SETTINGS_OPPONENT_SCREEN].ids.resume_game.background_normal = p
    app.root.screens[SETTINGS_RULES_SCREEN].ids.resume_game.background_normal = p
    app.root.screens[SETTINGS_SCREEN_SCREEN].ids.resume_game.background_normal = p
    app.root.screens[SETTINGS_SOUND_SCREEN].ids.resume_game.background_normal = p
    app.root.screens[SETTINGS_OPPONENT_SCREEN].ids.resume_game.text = t
    app.root.screens[SETTINGS_RULES_SCREEN].ids.resume_game.text = t
    app.root.screens[SETTINGS_SCREEN_SCREEN].ids.resume_game.text = t
    app.root.screens[SETTINGS_SOUND_SCREEN].ids.resume_game.text = t
    current['allow_resume'] = True

def disable_resume_game():
    global current
    p = "assets/img/invisible.png"
    app.root.screens[SETTINGS_OPPONENT_SCREEN].ids.resume_game.background_normal = p
    app.root.screens[SETTINGS_RULES_SCREEN].ids.resume_game.background_normal = p
    app.root.screens[SETTINGS_SCREEN_SCREEN].ids.resume_game.background_normal = p
    app.root.screens[SETTINGS_SOUND_SCREEN].ids.resume_game.background_normal = p
    app.root.screens[SETTINGS_OPPONENT_SCREEN].ids.resume_game.text = ""
    app.root.screens[SETTINGS_RULES_SCREEN].ids.resume_game.text = ""
    app.root.screens[SETTINGS_SCREEN_SCREEN].ids.resume_game.text = ""
    app.root.screens[SETTINGS_SOUND_SCREEN].ids.resume_game.text = ""
    current['allow_resume'] = False

def generically_apply_settings():
    global settings

    for key in settings:
        update_setting(key, settings[key])
    if current['allow_resume']:
        enable_resume_game()
    else:
        disable_resume_game()


##############################
#
#  KIVY SOUNDS & BACKGROUNDS
#
##############################

WALNUT = 0
BIRCH = 1

TEAL = 0
PEBBLE = 1
BLACK = 2

SOUND_FILE = 0
SEED_FILE = 1

MANY = 3

EMPTY_PIT = 0
FILLED_PIT = 1

VOL_MUTE = 0
VOL_SOFT = 1
VOL_MEDIUM = 2
VOL_LOUD = 3

PLAY_IDX = 4

COMBO_LIST = {}
for board_num, board_str in enumerate(["walnut", "birch"]):
    COMBO_LIST[board_num] = {}
    for seed_num, seed_str in enumerate(["teal", "pebble", "black"]):
        COMBO_LIST[board_num][seed_num] = {}
        #
        #  add sounds to COMBO LIST
        #
        COMBO_LIST[board_num][seed_num][SOUND_FILE] = {}
        for qty_num, qty_str in enumerate(["1", "2", "many"]):
            qty = (qty_num+1) if qty_num<2 else MANY
            COMBO_LIST[board_num][seed_num][SOUND_FILE][qty] = {}
            for pit_type, pit_str in enumerate(["empty", "filled"]):
                file_name = "assets/audio/{}-{}-{}-{}.wav".format(
                    board_str,
                    seed_str,
                    qty_str,
                    pit_str
                )
                COMBO_LIST[board_num][seed_num][SOUND_FILE][qty][pit_type] = []
                for _ in range(PLAY_IDX):
                    COMBO_LIST[board_num][seed_num][SOUND_FILE][qty][pit_type].\
                        append(SoundLoader.load(file_name))
                COMBO_LIST[board_num][seed_num][SOUND_FILE][qty][pit_type].append(0)

SCOOP_SOUND = {}
for qty_num, qty_str in enumerate(["1", "2", "many"]):
    qty = (qty_num+1) if qty_num<2 else MANY
    SCOOP_SOUND[qty] = []
    file_name = "assets/audio/scoop-{}.wav".format(qty_str)
    for _ in range(PLAY_IDX):
        SCOOP_SOUND[qty].append(SoundLoader.load(file_name))
    SCOOP_SOUND[qty].append(0)                            

##############################
#
#  KIVY CLASSES
#
##############################

GAME_SCREEN = 0
SETTINGS_OPPONENT_SCREEN = 1
SETTINGS_RULES_SCREEN = 2
SETTINGS_SCREEN_SCREEN = 3
SETTINGS_SOUND_SCREEN = 4

class GameScreen(Screen):
    global machine

    HANDS = [
        {}, # 0, nobody
        {"pos": (500, -300)},       # 1 user
        {"pos": (500, 1080+300)}     # 2 ai
    ]

    PITS = [
        {"pos": PARKED     }, #  0, hand
        {"pos": (420,  300), "out-pos": (420,  250)}, #  1
        {"pos": (636,  300), "out-pos": (636,  250)}, #  2
        {"pos": (852,  300), "out-pos": (852,  250)}, #  3
        {"pos": (1068, 300), "out-pos": (1068, 250)}, #  4
        {"pos": (1284, 300), "out-pos": (1284, 250)}, #  5
        {"pos": (1500, 300), "out-pos": (1500, 250)}, #  6
        {"pos": (1716, 480), "out-pos": (1716, 480)}, #  7 user store
        {"pos": (1500, 760), "out-pos": (1500, 810)}, #  8
        {"pos": (1284, 760), "out-pos": (1284, 810)}, #  9
        {"pos": (1068, 760), "out-pos": (1068, 810)}, # 10
        {"pos": (852,  760), "out-pos": (852,  810)}, # 11
        {"pos": (636,  760), "out-pos": (636,  810)}, # 12
        {"pos": (420,  760), "out-pos": (420,  810)}, # 13
        {"pos": (204,  600), "out-pos": (220,  600)}  # 14 ai store
    ]

    LOWER_LABEL = 30
    UPPER_LABEL = 1080-100-30

    def pushed_pit(self, pit):
        machine.input("pushed_pit", pit)

class SettingsOpponentScreen(Screen):

    global settings
    global character
    global AI_LIST
    global current

    def on_parent(self, instance, value):
        self._update_details(settings['ai_chosen'])
    
    def _update_details(self, ai_chosen):
        c = AI_LIST[ai_chosen]
        self.ids.ai_description.text = c['desc']
        self.ids.ai_play_style.text = "[i]" + c['tagline'] + "[/i]"
        self.ids.ai_name.text = c['name']
        self.ids.ai_rank.text = format("{} of 12").format(c['rank'])
        self.ids.ai_face_image.source = "assets/img/ai-pic-{:02d}.png".format(c['index'])
        if ai_chosen > settings['best_level']:
            self.ids.choose_ai.background_normal = 'assets/img/invisible.png'
            self.ids.choose_ai.text = ""
            n = AI_LIST[settings['best_level']]
            msg = "You must first defeat {} ({}) ".format(n['name'], settings['best_level'] + 1)
            if ai_chosen > settings['best_level'] + 1:
                m = AI_LIST[ai_chosen - 1]
                msg += "through {} ({}) ".format(m['name'], ai_chosen)
            # msg += "to play {}.".format(c['name'])
            self.ids.choose_msg.text = msg
        elif ai_chosen==settings['ai_chosen']:
            self.ids.choose_msg.text = "You are currently playing this opponent."
            self.ids.choose_ai.background_normal = 'assets/img/blank-wood-button.png'
            self.ids.choose_ai.text = ""
        else:
            self.ids.choose_msg.text = ""
            self.ids.choose_ai.background_normal = 'assets/img/blank-wood-button.png'
            self.ids.choose_ai.text = "Choose"

    def previous_ai(self):
        current['ai_viewed'] = (current['ai_viewed'] - 1) % 12
        self._update_details(current['ai_viewed'])

    def choose_ai(self):
        update_setting("ai_chosen", current['ai_viewed'])

    def next_ai(self):
        current['ai_viewed'] = (current['ai_viewed'] + 1) % 12
        self._update_details(current['ai_viewed'])

    def launch_url(self):
        webbrowser.open('https://www.youtube.com/watch?v=iSJk6CYsf6c')


class SettingsRulesScreen(Screen):
    pass


class SettingsScreenScreen(Screen):

    def launch_url(self, value):
        # TODO: look at settings and send the right lookup
        webbrowser.open('https://www.amazon.com/Mancala-Walnut-Stones-Purple-Squirrel/dp/B01CKHQ4GO')


class SettingsSoundScreen(Screen):
    pass


class AppScreenManager(ScreenManager):
    pass

class MancalaApp(App):

    global current

    def build(self):
        presentation = Builder.load_file('mancala.kv')
        return presentation

    def on_start(self):
        machine.bind_reference("kivy", self.root.screens[GAME_SCREEN].ids)
        if current['first_time_flag']:
            self.root.current = "settings_opponent_screen"
        machine.change_state("init_game")
        generically_apply_settings()

    def resume_game(self):
        if not current['allow_resume']:
            return
        self.root.current = "game_screen"

    def start_new_game(self):
        self.root.current = "game_screen"
        self.root.screens[GAME_SCREEN].ids.eog_new_game_button.active = False # ?
        save_game(force_new_game=True)
        current['first_time_flag'] = False
        enable_resume_game()
        machine.input("request_new_game")


##############################
#
#  ANIMATION
#
##############################

class Seeds(object):

    global HAND

    def __init__(self, display):
        self.board = [[] for x in xrange(15)]
        self.seed_ref = []
        for index in range(6*12):
            seed = Image()
            seed.id = "seed,{}".format(index)
            seed_pic = random.choice(SEED_DICT[settings['seed_choice']]['images'])
            seed.source = seed_pic['file']
            seed.pos_fixed = (2000, 2000)
            seed.spot_fixed = seed_pic['true_spot']
            seed.size_fixed = seed_pic['size_fixed']
            display.game_screen_root.add_widget(seed)
            self.board[HAND].append(seed)
            self.seed_ref.append(seed)
        hand = Image()
        hand.id = "user_hand"
        hand.source = "assets/img/user-hand-01.png"
        hand.pos_fixed = GameScreen.HANDS[USER]['pos']
        hand.spot_fixed = (300, 1500-128)
        hand.size_fixed = (600, 1500)
        display.game_screen_root.add_widget(hand)
        self.user_hand = hand
        hand = Image()
        hand.id = "ai_hand"
        hand.source = "assets/img/ai-hand-01.png"
        hand.pos_fixed = GameScreen.HANDS[AI]['pos']
        hand.spot_fixed = (340, 128)
        hand.size_fixed = (600, 1500)
        display.game_screen_root.add_widget(hand)
        self.ai_hand = hand
        face = Image()
        face.id = "ai_picture"
        face.source = "assets/img/ai-pic-01.png"
        face.pos_fixed = (0, 1080)
        face.size_fixed = (300, 300)
        self.ai_face = face
        display.game_screen_root.add_widget(face)
        self.display = display

    def change_ai_pictures(self, rank):
        self.ai_hand.source = "assets/img/ai-hand-{}.png".format(rank)
        self.ai_face.source = "assets/img/ai-pic-{}.png".format(rank)


    def change_picture(self):
        for s in self.seed_ref:
            seed_pic = random.choice(SEED_DICT[settings['seed_choice']]['images'])
            s.source = seed_pic['file']
            s.true_spot = seed_pic['true_spot']
            s.size_fixed = seed_pic['size_fixed']

    def scoop(self, pit):
        global SCOOP_SOUND
        global settings
        seed_count = len(self.board[pit])
        if seed_count==0:
            return
        for _ in range(seed_count):
            seed = self.board[pit].pop()
            self.board[HAND].append(seed)
            self._move(seed, HAND)
        scoop_size = seed_count if seed_count<3 else MANY
        sf = SCOOP_SOUND[scoop_size]
        sf[PLAY_IDX] = (sf[PLAY_IDX] + 1) % PLAY_IDX
        current = sf[PLAY_IDX]
        sf[current].volume = settings['seed_volume']*0.3
        sf[current].play()

    def drop(self, pit, count):
        global COMBO_LIST
        global settings
        pit_type = FILLED_PIT if self.board[pit] else EMPTY_PIT
        for _ in range(count):
            seed = self.board[HAND].pop()
            self.board[pit].append(seed)
            self._move(seed, pit)
        drop_size = count if count<3 else MANY
        sf = COMBO_LIST[settings['board_choice']][settings['seed_choice']]
        sf = sf[SOUND_FILE][drop_size]
        sf = sf[pit_type]
        sf[PLAY_IDX] = (sf[PLAY_IDX] + 1) % PLAY_IDX
        current = sf[PLAY_IDX]
        sf[current].volume = settings['seed_volume']*0.3
        sf[current].play()

    def _move(self, seed, pit):
        pos_fixed = GameScreen.PITS[pit]['pos']
        index = len(self.board[pit]) - 1
        x = pos_fixed[X] + PIT_ARRANGEMENT[pit-1][index][X]
        if pit in [7, 14]:
            y = pos_fixed[Y] + PIT_ARRANGEMENT[pit-1][index][Y] * 3
        else:
            y = pos_fixed[Y] + PIT_ARRANGEMENT[pit-1][index][Y]
        seed.pos_fixed = (int(x), int(y))


def animate_ai_start(display):
    global seeds
    a = Animation(pos_fixed = (230, 400)) + Animation(pos_fixed=(234, 400), duration=2.0)
    a.bind(on_complete = animate_ai_start_finished)
    a.start(seeds.ai_face)

def animate_ai_start_finished(*args, **kwargs):
    machine.input("animation_done")

def animate_ai_end(display):
    a = Animation(pos_fixed=(0, 1080))
    a.start(seeds.ai_face)

class HandSeedAnimation(object):

    global seeds
    global settings

    def __init__(self, player, board, display, restoration=False):
        self.restoration = restoration
        self.nplayer = player
        self.idx = 0
        self.board = copy(board)
        self.display = display
        self.animation_steps = game.animate
        self.animation_steps.append({"action": "home"})
        # print self.animation_steps
        self.last_step = {}
        if player==USER:
            self.hand = seeds.user_hand
        else:
            self.hand = seeds.ai_hand
        self.play_one_step(None, None)

    def play_one_step(self, sequence, widget):
        if self.idx<len(self.animation_steps):
            # CLEAN UP AFTER LAST STEP
            action = self.last_step.get('action')
            pit = self.last_step.get('loc')
            count = self.last_step.get('count')
            if action=="scoop":
                self.board[pit] = 0
                seeds.scoop(pit)
            elif action=="drop":
                self.board[pit] += count
                seeds.drop(pit, count)
            elif action=="drop_all":
                self.board[pit] += count
                seeds.drop(pit, count)
            elif action=="steal":
                pass
            elif action=="game_over":
                pass
            elif action=="normal_move":
                pass
            elif action=="home":
                pass
            # ACT ON NEW STEP
            step = self.animation_steps[self.idx]
            action = step['action']
            pit = step.get('loc')
            count = step.get('count')
            hand_animation = None # everything is timed by hand movement
            if step['action']=="scoop":
                hand_animation = Animation(
                    pos_fixed=GameScreen.PITS[pit]["pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action']=="drop":
                hand_animation = Animation(
                    pos_fixed=GameScreen.PITS[pit]["pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action']=="drop_all":
                hand_animation = Animation(
                    pos_fixed=GameScreen.PITS[pit]["pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action']=="steal":
                self.display.center_message.text = "Capture!"
            elif step['action']=="game_over":
                self.display.center_message.text = "Handling End of Game"
            elif step['action']=="setting_up":
                if self.restoration:
                    self.display.center_message.text = "Restoring Game"
                else:
                    self.display.center_message.text = "Setting Up Board"
            elif step['action']=="normal_move":
                self.display.center_message.text = ""
                hand_animation = Animation(
                    pos_fixed=GameScreen.PITS[pit]["out-pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action']=="home":
                self.display.center_message.text = ""
                hand_animation = Animation(
                    pos_fixed = GameScreen.HANDS[self.nplayer]['pos'],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            # update_numbers
            display_board(self.board, self.display)
            if not hand_animation:
                if step['action'] in ['setting_up']:
                    duration = 0.1
                else:
                    duration = 1.0
                hand_animation = Animation(pos_fixed=self.hand.pos_fixed, duration=duration)
            hand_animation.bind(on_complete = self.play_one_step)
            hand_animation.start(self.hand)
            self.idx += 1
            self.last_step = step
        else:
            machine.input("animation_done")


##############################
#
#  SIMPLE STATE CLASSES
#
##############################

class PendingStartState(State):
    
    global settings

    def on_exit(self):
        global seeds
        seeds = Seeds(self.ref["kivy"])

class InitGameState(State):

    def on_entry(self):
        global current

        self.ref['kivy'].wait_on_ai.stop_spinning()
        board_prior = copy(self.ref["game"].board)
        if current['first_time_flag']:
            print "FIRST TIME"
        else:
            restore_game()
            if self.ref["game"].restoration:
                self.ref["game"].reset_board(restoration=True)
                self.ref["game"].restoration = False
                self.animation = HandSeedAnimation(AI, board_prior, self.ref['kivy'], restoration=True)
            else:
                self.ref["game"].reset_board()
                self.animation = HandSeedAnimation(AI, board_prior, self.ref['kivy'])
            enable_resume_game()
        return self.same_state

    def input(self, input_name, *args, **kwargs):
        if input_name=="animation_done":
            return self.change_state("start_turn")
        if input_name == "request_new_game":
            self.change_state("init_game")


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
        save_game()
        self.ref["choices_so_far"] = []
        self.ref["ai_choices"] = []
        if self.ref["game"].is_over():
            return self.change_state("eog")
        if self.ref["game"].nplayer==1:
            self.ref["kivy"].center_message.text = "Choose a house."
            self.ref["game"].usermove_start_simulation()
            self.ref["possible_user_moves"] = self.ref["game"].possible_moves()
            return self.change_state("wait_for_pit")
        return self.change_state("ai_thinking")

    def input(self, input_name, *args, **kwargs):
        if input_name == "request_new_game":
            self.change_state("init_game")

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
        if input_name == "request_new_game":
            self.change_state("init_game")

class AnitmateUserChoiceState(State):

    def on_entry(self):
        board_prior = copy(self.ref["game"].board)
        self.ref["game"].usermove_simulate_choice(self.ref['choices_so_far'])
        self.animation = HandSeedAnimation(USER, board_prior, self.ref['kivy'])

    def input(self, input_name, *args, **kwargs):
        if input_name=="animation_done":
            possible_moves = self.ref["possible_user_moves"]
            done = any([chlist==self.ref['choices_so_far'] for chlist in possible_moves])
            if done:
                self.ref["game"].usermove_finish_simulation()
                self.ref["game"].animated_play_move(self.ref['choices_so_far'])
                return self.change_state("start_turn")
            self.ref['kivy'].center_message.text ="landed in store. play again."
            return self.change_state("wait_for_pit")
        if input_name == "request_new_game":
            self.change_state("init_game")

    def on_exit(self):
        display_board(self.ref['game'].board, self.ref['kivy'])


def get_ai_move():
    global game
    global machine
    choices = game.get_move()
    machine.input("ai_move", choices)


class AIThinkingState(State):
    
    def on_entry(self):
        global character
        self.ref['kivy'].center_message.text = "{} is thinking.".format(character["name"])
        self.ref['kivy'].wait_on_ai.start_spinning()
        self.ref['kivy'].spinner_background.active = True
        self.animation_finished = False
        self.thinking_finished = False
        animate_ai_start(self.ref["kivy"])
        thread.start_new_thread(get_ai_move, ())

    def input(self, input_name, *args, **kwargs):
        if input_name == "ai_move":
            self.thinking_finished = True
            self.ref["ai_choices"] = args[0]
        if input_name == "request_new_game":
            self.change_state("init_game")
        if input_name == "animation_done":
            self.animation_finished = True
        if self.animation_finished and self.thinking_finished:
            self.change_state("animate_ai")            

    def on_exit(self):
        animate_ai_end(self.ref["kivy"])
        self.ref["kivy"].wait_on_ai.stop_spinning()
        self.ref['kivy'].spinner_background.active = False

class AnimateAIChoicesState(State):

    def on_entry(self):
        board_prior = copy(self.ref['game'].board)
        self.ref['game'].animated_play_move(self.ref['ai_choices'])
        self.animation = HandSeedAnimation(AI, board_prior, self.ref['kivy'])

    def input(self, input_name, *args, **kwargs):
        if input_name == "animation_done":
            self.change_state('start_turn')
        if input_name == "request_new_game":
            self.change_state("init_game")

    def on_exit(self):
        display_board(self.ref['game'].board, self.ref['kivy'])

class EndOfGameDisplayState(State):

    def on_entry(self):
        save_game()
        winner = self.ref['game'].get_winner()    
        self.ref["kivy"].center_message.text = \
            ["Tie Game.", "You won!", "AI won."][game.get_winner()]
        self.ref["kivy"].eog_new_game_button.active = True

    def input(self, input_name, *args, **kwargs):
        if input_name == "request_new_game":
            self.change_state("init_game")


if __name__=='__main__':
    game = KalahGame(settings)
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
    app = MancalaApp()
    app.run()
