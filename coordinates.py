import copy
import random

#################
#
# Coordinates used elsewhere in the program
#
# These are either contants or after init essentially behave as constants.
#
#################


SEED_SPOTS_TEMPLATE = [
    (-1,  1),
    ( 3, -2),
    ( 3,  2),
    ( 1, -2),
    (-1,  4),
    (-3, -1),
    (-2, -3),
    ( 1, -4),
    (-5, -3),
    ( 1,  2),
    (-3,  3),
    ( 2,  4),
    ( 6,  1),
    (-4,  2),
    (-1, -1),
    ( 3, -3),
    (-4, -4),
    ( 4,  4),
    (-2,  7),
    (-5, -2),
    (-2,  2),
    (-6,  1),
    (-2, -6),
    (-4,  5),
    ( 1,  5),
    ( 2, -1),
    ( 2, -6),
    (-5,  3),
    ( 4,  7),
    ( 4, -5)
]
SEED_SPOTS_TEMPLATE_LEN = len(SEED_SPOTS_TEMPLATE)


SEED_SPOTS_SCALED = []
for i in range(12 * 6 + 1):
    x, y = SEED_SPOTS_TEMPLATE[i % SEED_SPOTS_TEMPLATE_LEN]
    scaler = (75.0 / 7.0) * (1.0 + 0.1 * float(int(i / SEED_SPOTS_TEMPLATE_LEN) - 1))
    SEED_SPOTS_SCALED.append( (x * scaler, y * scaler) )
    # print (x * scaler, y * scaler)

PIT_ARRANGEMENT = []
for pit in range(14):
    new_list = []
    for x, y in SEED_SPOTS_SCALED:
        x = int(x + random.random() * 3.0)
        y = int(y + random.random() * 3.0)
        if pit % 4 == 0:
            new_list.append((x, y))
        elif pit % 4 == 1:
            new_list.append((y, x))
        elif pit % 4 == 2:
            new_list.append((-x, -y))
        else:
            new_list.append((-y, -x))
    PIT_ARRANGEMENT.append(new_list)


SEED_DICT = {}
for seed_num, seed_str in enumerate(["teal", "pebble", "black"]):
    SEED_DICT[seed_num] = {}
    SEED_DICT[seed_num]['images'] = []
    for index in range(1, 4):
        file_name = [
            'assets/img/seed-teal-0{}.png',
            'assets/img/seed-pebble-0{}.png',
            'assets/img/seed-black-0{}.png',
        ][seed_num]
        file_name = file_name.format(index)
        size = [
            (90, 90),
            (90, 90),
            (90, 90)
        ][seed_num]
        true_spot = (size[0]/2.0, size[1]/2.0)
        SEED_DICT[seed_num]['images'].append({
            'file': file_name,
            'size_fixed': size,
            'true_spot': true_spot
        })


HAND_FOCUS = [
    (300,   0),  # AI 1
    (150, 200),  # AI 2
    (500, 100),  # AI 3
    (300, 150),  # AI 4
    (250, 150),  # AI 5
    (400, 150),  # AI 6
    (450, 100),  # AI 7
    (400, 100),  # AI 8
    (150, 100),  # AI 9
    (360, 250),  # AI 10
    (310,  15),  # AI 11
    (100,  75),  # AI 12
]