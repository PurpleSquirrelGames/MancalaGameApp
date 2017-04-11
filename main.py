import thread
import random
import webbrowser
import pprint
from copy import copy
from kivy.app import App
from kivy.animation import Animation
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.garden.progressspinner import ProgressSpinner
from kivy.lang import Builder
from kivy.storage.jsonstore import JsonStore
from kivy.uix.image import Image
from kivy.uix.screenmanager import ScreenManager, Screen, NoTransition

from kivy.uix.floatlayout import FloatLayout

from fixedlayout import FixedLayout, FixedPopup, FixedRadioButtons, \
    FixedSimpleMenu, FixedSimpleMenuItem

from simplestate import StateMachine, State
from gameengine import KalahGame
from characters import AI_LIST
from coordinates import PIT_ARRANGEMENT, SEED_DICT, HAND_FOCUS

__version__ = '0.0.14'

pp = pprint.PrettyPrinter(indent=4)

machine = StateMachine(debug=True)

seeds = None
status_bar = None

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
    "best_level": -1
}

current = {
    'ai_viewed': 0,
    'first_time_flag': False,
    'allow_resume': False,
    'seed_sounds': {},
    'cheat': False
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
        app.root.screens[SETTINGS_OPPONENT_SCREEN].ids.start_game_wrapper.text =\
            "play\n{}".format(character['name'])
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
        set_current_sound_combo()
    if setting_name == "animation_speed_choice":
        settings["seed_drop_rate"] = 0.1 + value * 0.3
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

VOLS = [0.0, 0.25, 0.5, 1.0]


PLAY_IDX = 4

SEED_SOUNDS = {}
for board_num, board_str in enumerate(["walnut", "birch"]):
    SEED_SOUNDS[board_num] = {}
    for seed_num, seed_str in enumerate(["teal", "pebble", "black"]):
        SEED_SOUNDS[board_num][seed_num] = {}
        #
        #  add sounds to COMBO LIST
        #
        SEED_SOUNDS[board_num][seed_num] = {}
        for qty_num, qty_str in enumerate(["1", "2", "many"]):
            qty = (qty_num + 1) if qty_num < 2 else MANY
            SEED_SOUNDS[board_num][seed_num][qty] = {}
            for pit_type, pit_str in enumerate(["empty", "filled"]):
                file_name = "assets/audio/{}-{}-{}-{}.wav".format(
                    board_str,
                    seed_str,
                    qty_str,
                    pit_str
                )
                SEED_SOUNDS[board_num][seed_num][qty][pit_type] = file_name

SCOOP_SOUND = {}
for qty_num, qty_str in enumerate(["1", "2", "many"]):
    qty = (qty_num + 1) if qty_num < 2 else MANY
    SCOOP_SOUND[qty] = []
    file_name = "assets/audio/scoop-{}.wav".format(qty_str)
    for _ in range(PLAY_IDX):
        SCOOP_SOUND[qty].append(SoundLoader.load(file_name))
    SCOOP_SOUND[qty].append(0)


def set_current_sound_combo():
    global settings
    global SEED_SOUNDS
    global current

    sounds = current['seed_sounds']
    ref = SEED_SOUNDS[settings['board_choice']][settings['seed_choice']]

    for qty in [1, 2, MANY]:
        sounds[qty] = {}
        for pit_type in [0, 1]:
            file_name = ref[qty][pit_type]
            sounds[qty][pit_type] = []
            for _ in range(PLAY_IDX):
                sounds[qty][pit_type].append(SoundLoader.load(file_name))
            sounds[qty][pit_type].append(0)


set_current_sound_combo()

# done_sound = SoundLoader.load("assets/audio/ding-ai-done.wav")
waiting_for_player_sound = SoundLoader.load("assets/audio/tin-wait-for-player.wav")
reward_sound = SoundLoader.load("assets/audio/tada-level-up.wav")

#   playing the ai_done_sound() causes a crash after a difficult AI level, I do not know why.
# def play_ai_done_sound():
#     done_sound.volume = VOLS[settings['notification_volume']]
#     done_sound.play()


def play_waiting_for_player():
    waiting_for_player_sound.volume = VOLS[settings['notification_volume']]
    waiting_for_player_sound.play()


def play_reward_sound():
    reward_sound.volume = VOLS[settings['notification_volume']]
    reward_sound.play()


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
        {},  # 0, nobody
        {"pos": (500, -500)},       # 1 user
        {"pos": (500, 1080+500)}     # 2 ai
    ]

    PITS = [
        {"pos": PARKED     },  #  0, hand
        {"pos": (420,  300), "out-pos": (420,  250)},  #  1
        {"pos": (636,  300), "out-pos": (636,  250)},  #  2
        {"pos": (852,  300), "out-pos": (852,  250)},  #  3
        {"pos": (1068, 300), "out-pos": (1068, 250)},  #  4
        {"pos": (1284, 300), "out-pos": (1284, 250)},  #  5
        {"pos": (1500, 300), "out-pos": (1500, 250)},  #  6
        {"pos": (1716, 480), "out-pos": (1716, 480)},  #  7 user store
        {"pos": (1500, 760), "out-pos": (1500, 810)},  #  8
        {"pos": (1284, 760), "out-pos": (1284, 810)},  #  9
        {"pos": (1068, 760), "out-pos": (1068, 810)},  # 10
        {"pos": (852,  760), "out-pos": (852,  810)},  # 11
        {"pos": (636,  760), "out-pos": (636,  810)},  # 12
        {"pos": (420,  760), "out-pos": (420,  810)},  # 13
        {"pos": (204,  600), "out-pos": (220,  600)}   # 14 ai store
    ]

    LOWER_LABEL = 30
    UPPER_LABEL = 1080 - 100 - 30

    def pushed_pit(self, pit):
        machine.input("pushed_pit", pit)

    def toggle_message_bar(self):
        global status_bar
        status_bar.toggle_hide()


cheat_spin = []


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
        if ai_chosen > (settings['best_level'] + 1):
            self.ids.choose_ai.background_normal = 'assets/img/invisible.png'
            self.ids.choose_ai.text = ""
            n = AI_LIST[settings['best_level'] + 1]
            msg = "You must first defeat {} ({}) ".format(n['name'], settings['best_level'] + 2)
            if ai_chosen > settings['best_level'] + 2:
                m = AI_LIST[ai_chosen - 1]
                msg += "through {} ({}) ".format(m['name'], ai_chosen)
            # msg += "to play {}.".format(c['name'])
            self.ids.choose_msg.text = msg
        elif ai_chosen == settings['ai_chosen']:
            self.ids.choose_msg.text = "You are currently playing this opponent."
            self.ids.choose_ai.background_normal = 'assets/img/blank-wood-button.png'
            self.ids.choose_ai.text = "(current)"
        else:
            self.ids.choose_msg.text = ""
            self.ids.choose_ai.background_normal = 'assets/img/blank-wood-button.png'
            self.ids.choose_ai.text = "Choose"

    def previous_ai(self):
        global cheat_spin
        current['ai_viewed'] = (current['ai_viewed'] - 1) % 12
        self._update_details(current['ai_viewed'])
        if cheat_spin and cheat_spin[-1] == ">":
            cheat_spin.append("<")
        else:
            cheat_spin = []

    def choose_ai(self):
        global settings
        global current
        global cheat_spin
        if cheat_spin == [">", ">", ">", "<", ">", ">", ">", "<"]:
            current['cheat'] = True
            self.ids.choose_ai.text = "cheat"
        cheat_spin = []
        if (current['ai_viewed'] <= (settings['best_level'] + 1)) or current['cheat']:
            update_setting("ai_chosen", current['ai_viewed'])

    def next_ai(self):
        global cheat_spin
        current['ai_viewed'] = (current['ai_viewed'] + 1) % 12
        self._update_details(current['ai_viewed'])
        cheat_spin.append(">")

    def launch_url(self):
        webbrowser.open('https://www.youtube.com/watch?v=iSJk6CYsf6c')


class SettingsRulesScreen(Screen):
    pass


class SettingsScreenScreen(Screen):

    global settings

    def launch_url(self, value):
        # TODO: look at settings and send the right lookup
        if settings["board_choice"] == 0:       # walnut
            if settings["seed_choice"] == 0:    # w teal
                webbrowser.open('https://www.amazon.com/dp/B01CKHM4WC')
            elif settings["seed_choice"] == 1:  # w tumbled pebbles
                webbrowser.open('https://www.amazon.com/dp/B01CKI1DLY')
            else:                               # w river stones
                webbrowser.open('https://www.amazon.com/dp/B01CKHQ4GO')
        else:                                   # birch
            if settings["seed_choice"] == 0:    #  w teal
                webbrowser.open('https://www.amazon.com/dp/B01IRS81CU')
            elif settings["seed_choice"] == 1:  #  w tumbled pebbles
                webbrowser.open('https://www.amazon.com/dp/B01IRSJGVA')
            else:                               #  w river stones
                webbrowser.open('https://www.amazon.com/dp/B01IRPHFJI')


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
        Window.bind(on_keyboard=self.on_key)
        self.MENU_POPUPS = [
            self.root.screens[SETTINGS_RULES_SCREEN].ids.game_choice_popup,
            self.root.screens[SETTINGS_RULES_SCREEN].ids.who_first_popup,
            self.root.screens[SETTINGS_RULES_SCREEN].ids.seeds_per_house_selection_popup,
            self.root.screens[SETTINGS_RULES_SCREEN].ids.capture_rule_popup,
            self.root.screens[SETTINGS_RULES_SCREEN].ids.eog_rule_popup,
            self.root.screens[SETTINGS_SCREEN_SCREEN].ids.board_choice_popup,
            self.root.screens[SETTINGS_SCREEN_SCREEN].ids.background_popup,
            self.root.screens[SETTINGS_SCREEN_SCREEN].ids.seed_choice_popup,
            self.root.screens[SETTINGS_SCREEN_SCREEN].ids.animation_speed_popup,
            self.root.screens[SETTINGS_SOUND_SCREEN].ids.notification_volume_popup,
            self.root.screens[SETTINGS_SOUND_SCREEN].ids.seed_volume_popup
        ]

    def need_to_escape_menu(self):
        ''' if any menu screen is open; then close it. '''
        open_popup_found = False
        for popup in self.MENU_POPUPS:
            if popup.active:
                popup.active = False
                open_popup_found = True
        return open_popup_found

    def on_key(self, window, key, *args):
        if key == 27:  # Esc on PC, Back on Android
            if self.need_to_escape_menu():
                return True
            if current['allow_resume']:
                self.resume_game()
            else:
                self.start_new_game()
            return True
        return False

    def resume_game(self):
        if not current['allow_resume']:
            return
        self.root.current = "game_screen"

    def start_new_game(self):
        self.root.current = "game_screen"
        self.root.screens[GAME_SCREEN].ids.eog_new_game_button.active = False
        save_game(force_new_game=True)
        current['first_time_flag'] = False
        enable_resume_game()
        machine.input("request_new_game")

    def upgrade_opponent(self):
        global settings
        update_setting("ai_chosen", settings['best_level'] + 1)
        self.start_new_game()


##############################
#
#  ANIMATION
#
##############################

STATUS_FULL_LOCATION = (330, 460)
STATUS_MIN_LOCATION = (0, 0)
STATUS_OFFSCREEN_LOCATION = (4000, 4000)


class StatusBar(object):

    def __init__(self, display):
        self.display = display
        self.text = ""
        self.want_visible = True
        self.is_done = False
        self._move_board(self.want_visible)

    def _move_board(self, force_show=False):
        if force_show:
            self.display.message_background.pos_fixed = STATUS_FULL_LOCATION
            self.display.center_message.text = self.text
        elif self.is_done:
            self.display.message_background.pos_fixed = STATUS_OFFSCREEN_LOCATION
            if self.want_visible:
                self.display.message_down_button.pos_fixed = STATUS_OFFSCREEN_LOCATION
            self.display.center_message.text = ""
            self.display.message_down_button.text = ""
        elif self.want_visible:
            self.display.message_background.pos_fixed = STATUS_FULL_LOCATION
            self.display.message_down_button.pos_fixed = STATUS_FULL_LOCATION
            self.display.center_message.text = self.text
            self.display.message_down_button.text = "V"
        else:
            self.display.message_background.pos_fixed = STATUS_OFFSCREEN_LOCATION
            self.display.message_down_button.pos_fixed = STATUS_MIN_LOCATION
            self.display.center_message.text = ""
            self.display.message_down_button.text = "*" if self.wait_on_player else ""

    def toggle_hide(self):
        if self.want_visible:
            self.want_visible = False
        else:
            self.want_visible = True
        self._move_board()

    def say(self, text, wait_on_player=False, force_show=False):
        self.wait_on_player = wait_on_player
        self.text = text
        self.is_done = False
        self._move_board(force_show=force_show)

    def done(self):
        self.wait_on_player = True
        self.text = ""
        self.is_done = True
        self._move_board()


class Seeds(object):

    global HAND

    def __init__(self, display):
        self.board = [[] for x in xrange(15)]
        self.seed_ref = []
        for index in range(6 * 12):
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
        hand.spot_fixed = (300, 1500 - 128)
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
        global HAND_FOCUS
        self.ai_hand.source = "assets/img/ai-hand-{}.png".format(rank)
        self.ai_face.source = "assets/img/ai-pic-{}.png".format(rank)
        i = int(rank) - 1
        self.ai_hand.spot_fixed = HAND_FOCUS[i]
        # self.ai_hand.size_fixed = (100, 100)  # toggle to force recalc
        # self.ai_hand.size_fixed = (600, 1500)

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
        if seed_count == 0:
            return
        for _ in range(seed_count):
            seed = self.board[pit].pop()
            self.board[HAND].append(seed)
            self._move(seed, HAND)
        scoop_size = seed_count if seed_count < 3 else MANY
        sf = SCOOP_SOUND[scoop_size]
        sf[PLAY_IDX] = (sf[PLAY_IDX] + 1) % PLAY_IDX
        current = sf[PLAY_IDX]
        sf[current].volume = VOLS[settings['seed_volume']]
        sf[current].play()

    def drop(self, pit, count):
        global current
        global settings
        pit_type = FILLED_PIT if self.board[pit] else EMPTY_PIT
        for _ in range(count):
            seed = self.board[HAND].pop()
            self.board[pit].append(seed)
            self._move(seed, pit)
        drop_size = count if count < 3 else MANY
        sf = current['seed_sounds'][drop_size][pit_type]
        sf[PLAY_IDX] = (sf[PLAY_IDX] + 1) % PLAY_IDX
        i = sf[PLAY_IDX]
        sf[i].volume = VOLS[settings['seed_volume']]
        sf[i].play()

    def _move(self, seed, pit):
        pos_fixed = GameScreen.PITS[pit]['pos']
        index = len(self.board[pit]) - 1
        x = pos_fixed[X] + PIT_ARRANGEMENT[pit - 1][index][X]
        if pit in [7, 14]:
            y = pos_fixed[Y] + PIT_ARRANGEMENT[pit - 1][index][Y] * 3
        else:
            y = pos_fixed[Y] + PIT_ARRANGEMENT[pit - 1][index][Y]
        seed.pos_fixed = (int(x), int(y))


def animate_ai_start(display):
    global seeds
    a = Animation(pos_fixed=(230, 400)) + Animation(pos_fixed=(234, 400), duration=2.0)
    a.bind(on_complete=animate_ai_start_finished)
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
        if player == USER:
            self.hand = seeds.user_hand
        else:
            self.hand = seeds.ai_hand
        self.play_one_step(None, None)

    def play_one_step(self, sequence, widget):
        if self.idx < len(self.animation_steps):
            # CLEAN UP AFTER LAST STEP
            action = self.last_step.get('action')
            pit = self.last_step.get('loc')
            count = self.last_step.get('count')
            if action == "scoop":
                self.board[pit] = 0
                seeds.scoop(pit)
            elif action == "drop":
                self.board[pit] += count
                seeds.drop(pit, count)
            elif action == "drop_all":
                self.board[pit] += count
                seeds.drop(pit, count)
            elif action == "steal":
                pass
            elif action == "game_over":
                pass
            elif action == "normal_move":
                pass
            elif action == "home":
                pass
            # ACT ON NEW STEP
            step = self.animation_steps[self.idx]
            action = step['action']
            pit = step.get('loc')
            count = step.get('count')
            hand_animation = None # everything is timed by hand movement
            if step['action'] == "scoop":
                hand_animation = Animation(
                    pos_fixed=GameScreen.PITS[pit]["pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action'] == "drop":
                hand_animation = Animation(
                    pos_fixed=GameScreen.PITS[pit]["pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action'] == "drop_all":
                hand_animation = Animation(
                    pos_fixed=GameScreen.PITS[pit]["pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action'] == "steal":
                status_bar.say("Capture!")
            elif step['action'] == "game_over":
                status_bar.say("Handling End of Game")
            elif step['action'] == "setting_up":
                if self.restoration:
                    status_bar.say("Restoring Game")
                else:
                    status_bar.say("Setting Up Board")
            elif step['action'] == "normal_move":
                status_bar.done()
                hand_animation = Animation(
                    pos_fixed=GameScreen.PITS[pit]["out-pos"],
                    duration=settings['seed_drop_rate'],
                    t='in_out_sine'
                )
            elif step['action'] == "home":
                status_bar.done()
                hand_animation = Animation(
                    pos_fixed=GameScreen.HANDS[self.nplayer]['pos'],
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
            hand_animation.bind(on_complete=self.play_one_step)
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
        global status_bar
        seeds = Seeds(self.ref["kivy"])
        status_bar = StatusBar(self.ref["kivy"])


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
                self.animation = HandSeedAnimation(
                    AI, board_prior, self.ref['kivy'], restoration=True
                )
            else:
                self.ref["game"].reset_board()
                self.animation = HandSeedAnimation(AI, board_prior, self.ref['kivy'])
            enable_resume_game()
        return self.same_state

    def input(self, input_name, *args, **kwargs):
        if input_name == "animation_done":
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
        if self.ref["game"].nplayer == 1:
            status_bar.say("Choose a house.", wait_on_player=True)
            self.ref["game"].usermove_start_simulation()
            self.ref["possible_user_moves"] = self.ref["game"].possible_moves()
            return self.change_state("wait_for_pit")
        return self.change_state("ai_thinking")

    def input(self, input_name, *args, **kwargs):
        if input_name == "request_new_game":
            self.change_state("init_game")


class WaitForPitButtons(State):

    def on_entry(self):
        play_waiting_for_player()
        display_board(self.ref['game'].board, self.ref['kivy'])

    def input(self, input_name, *args, **kwargs):
        if input_name == "pushed_pit":
            pit = args[0]
            index = len(self.ref['choices_so_far'])
            valid_move = any(
                grab(chlist, index) == pit for chlist in self.ref["possible_user_moves"]
            )
            if valid_move:
                status_bar.say("Playing house {}".format(pit))
                self.ref['choices_so_far'].append(pit)
                self.change_state("animate_user")
            else:
                status_bar.say("Cannot play empty house. Try again.")
        if input_name == "request_new_game":
            self.change_state("init_game")


class AnitmateUserChoiceState(State):

    def on_entry(self):
        board_prior = copy(self.ref["game"].board)
        self.ref["game"].usermove_simulate_choice(self.ref['choices_so_far'])
        self.animation = HandSeedAnimation(USER, board_prior, self.ref['kivy'])

    def input(self, input_name, *args, **kwargs):
        if input_name == "animation_done":
            possible_moves = self.ref["possible_user_moves"]
            done = any([chlist == self.ref['choices_so_far'] for chlist in possible_moves])
            if done:
                self.ref["game"].usermove_finish_simulation()
                self.ref["game"].animated_play_move(self.ref['choices_so_far'])
                return self.change_state("start_turn")
            status_bar.say("Landed in store. Play again.", wait_on_player=True)
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
        status_bar.say("{} is thinking.".format(character["name"]))
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
        # play_ai_done_sound()
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
        global settings
        global AI_LIST

        save_game()
        winner = self.ref['game'].get_winner()
        msg = ["Tie Game.", "You won!", "{} won.".format(character["name"])][winner]
        status_bar.say(msg, force_show=True)
        self.ref["kivy"].eog_new_game_button.active = True
        if (winner == USER) or current['cheat']:
            if settings['ai_chosen'] > settings['best_level']:
                best_level = settings['ai_chosen']
                update_setting('best_level', best_level)
                n = AI_LIST[best_level]
                pmsg = "Congratulations!\n\n"
                if winner == AI:
                    pmsg = "Congratulations cheater!\n\n"
                pmsg += "You have successfully defeated {}.\n".format(n['name'])
                if best_level < 11:
                    m = AI_LIST[best_level + 1]
                    pmsg += "You can now play {}, a smarter opponent.".format(m['name'])
                    self.ref["kivy"].next_opponent_popup.active = True
                    self.ref["kivy"].next_opponent_button.text = "Play {}".format(m['name'])
                else:
                    pmsg += "You have won the game!\n"
                    pmsg += "For more challenge, let the opponent go first."
                self.ref["kivy"].progress_message_popup.active = True
                self.ref["kivy"].progress_message.text = pmsg
                play_reward_sound()

    def input(self, input_name, *args, **kwargs):
        if input_name == "request_new_game":
            self.change_state("init_game")

    def on_exit(self):
        self.ref["kivy"].next_opponent_popup.active = False
        self.ref["kivy"].progress_message_popup.active = False


if __name__ == '__main__':
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
