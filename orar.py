from __future__ import annotations
import yaml
from typing import Callable
from copy import copy
from copy import deepcopy
from functools import reduce
import numpy as np
from utils import pretty_print_timetable
from random import shuffle, seed, randint
# imports

# reader, beacuse I have not seen utils.py until a certian moment, shame on me
data = None
with open("dummy.yaml") as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        
#parser
materii = data['Materii']
intervale1 = data['Intervale']
profi = data['Profesori']
sali = data['Sali']
zile = data['Zile']
intervale = [eval(i) for i in intervale1]

def __my_pretty_print__(Any):
    '''
    My pretty print for testing purposes
    '''
    print()
    print(Any)
    print()
    print("--------------------------------------------")

def __init_state__(zile, intervale, sali):
    '''
    Initialize state
    A state is a whole timetable of this type {str : {(int, int) : {str : (str, str)}}}
    Bullet 1 from task satisfied -> just one subject per room, no array
    '''
    sched = {}
    for idx_i, i in enumerate(zile):
        sched[i] = {}
        for idx_j, j in enumerate(intervale):
            sched[i][j] = {}
            for idx_k, k in enumerate(sali):
                sched[i][j][k] = ()
    return sched

# initialises the state machine let's call it
states = []

# we will foreever have an empty timetable
vesnic_gol = __init_state__(zile, intervale, sali)

def __init_cobai__(zile, intervale, sali):
    '''
    Initializes the 'timetable' in which we put all the possible arrangements \n
    Instead of having just a tuple per room, we have an array with 
    all the possibile classes that can be held there
    '''
    sched = {}
    for idx_i, i in enumerate(zile):
        sched[i] = {}
        for idx_j, j in enumerate(intervale):
            sched[i][j] = {}
            for idx_k, k in enumerate(sali):
                sched[i][j][k] = [] # instead of having a single tuple, we should have all 
                # the possibilities of tech and subject so we can make generations
    return sched

cobai = __init_cobai__(zile, intervale, sali)

def __get_teach_poate__(profi):
    '''
    Genereates all the intervals in which a teacher can teach \n
    Soft constraints, we'll fix it later \n
    First we have to deal with the hard/logistical ones
    Bullets 1, 2, 3 from soft constraints
    '''
    teach = {}
    for i in profi:
        ore_ok = []
        zile_ok = []
        teach[i] = {}
        for j in profi[i]['Constrangeri']:
            e_ora = 0
            if '!' not in j:
                for char in j:
                    if char.isdigit():
                        e_ora = 1
                        break
                if e_ora:
                    start, end = map(int, j.split('-'))
                    if (end - start) > 2:
                        for ore in range(start, end-2, 2):
                            endd = ore + 2
                            interv = (ore, endd)
                            ore_ok.append(interv)
                    else:
                        ore_ok.append((start, end))
                else:
                    zile_ok.append(j)
                teach[i]['ore_ok'] = ore_ok
                teach[i]['zile_ok'] = zile_ok
    return teach

permisiuni = __get_teach_poate__(profi)

def __generate_actions12__(profi, sali, zile, intervale):
    ''' 
    Generates all possible actions from the lists of days, intervals, teachers
    in order to satisfact the constraints of days, intervals 
    and their own subjects with rooms for each subject for teachers
    Bullets 2, 5, 6 from hard constraints
    '''
    actions = []
    for i in profi:
        materii_prof = []
        for j in profi[i]['Materii']:
            materii_prof.append(j)
        for j in materii_prof:
            for k in zile:
                for l in intervale:
                    for m in sali:
                        if str(j) in sali[m]['Materii']:
                            dummy = (k, l, j, m, i)
                            actions.append(dummy)
    good_actions = sorted(list(set(actions)), key=lambda x: (x[0], x[1], x[2]))
    return good_actions
longer2 = __generate_actions12__(profi, sali, zile, intervale)

def __generate_actions2__(profi):
    '''
    Generates "cards" of teachers and the subject of teach
    in order to put a card in the right place, acording to the constraints
    Bullet 2 from hard constraints
    '''
    actions = []
    for i in profi:
        for j in profi[i]['Materii']:
            dummy = (j, i)
            actions.append(dummy)
    return actions

actions = __generate_actions2__(profi)

def __populate_cobai2__(cobai, actions):
    '''
    Here is generated a whole timetable, but with all constraints not satisfied \n
    Basically, is a timetable with all possible arrangements/with all possibilities \n
    On its basis we satisfact/choose what to put in the right timetable
    '''
    for i in actions:
        cobai[i[0]][i[1]][i[3]].append((i[4], i[2]))
        
# we populate the timetable with all arrangements
__populate_cobai2__(cobai, longer2)

def __get__pref_conflicts__(sched):
    '''
    Checks soft permissions without the !Pauza constraint
    Bullets 1, 2, 3 from soft constraints
    '''
    nr = 0
    for zi in sched:
        for ore in sched[zi]:
            for sala in sched[zi][ore]:
                if zi in permisiuni[sched[zi][ore][sala][0]]['zile_ok']:
                    for tupl in permisiuni[sched[zi][ore][sala][0]]['ore_ok']:
                        if str(tupl) != ore:
                            nr += 1
    return nr

def __get_capacity_conflicts__(board):
    '''
    Checks whether all students have a seat in the rooms
    Bullet 4 from hard constraints
    '''
    nr = 0
    vector_caracteristic = {}
    for i in materii:
        vector_caracteristic[i] = 0
    for zi in board:
        for ore in board[zi]:
            for sala in board[zi][ore]:
                if len(board[zi][ore][sala]) >= 1:
                    vector_caracteristic[board[zi][ore][sala][1]] += sali[sala]['Capacitate']
    for i in vector_caracteristic:
        if vector_caracteristic[i] < materii[i]:
            nr += 1
    return nr

def __get_overlap_conflicts__(board):
    '''
    Checks to see if a teacher is NOT in two different places in the same time
    Bullet 1 from hard constraints
    '''
    nr = 0
    for zi in board:
        for ore in board[zi]:
            for sala1 in board[zi][ore]:
                for sala2 in board[zi][ore]:
                    if sala1 != sala2:
                        if len(board[zi][ore][sala1]) >= 1 and len(board[zi][ore][sala2]) >= 1 and board[zi][ore][sala1][0] == board[zi][ore][sala2][0]:
                            nr += 1
                break
    return nr

def __where2__(actionn, sched, cobai):
    '''
    On a longer form of a "card"/possibile arrangement 
    (day, interval, room, teacher, subject) tuple show where to put it in the timetable,
    according to the timetable with all the possibilities 
    and the empty slots in the timetable right now.
    '''
    positions = []
    for day in sched:
        for interval in cobai[day]:
            for room in cobai[day][interval]:
                for tuplu in cobai[day][interval][room]:
                    if len(actionn) >= 4 and actionn[2] == tuplu[1] and actionn[4] == tuplu[0] and sched[day][interval][room] == ():
                        positions.append((day, interval, room))
    return positions

def __where21__(action, sched, cobai):
    '''
    On a shorter form of a "card"/possibile arrangement 
    (teacher, subject) tuple show where to put it in the timetable,
    according to the timetable with all the possibilities 
    and the empty slots in the timetable right now.
    '''
    positions = []
    for day in sched:
        for interval in cobai[day]:
            for room in cobai[day][interval]:
                for tuplu in cobai[day][interval][room]:
                    if len(action) >= 2 and action[0] == tuplu[1] and action[1] == tuplu[0] and sched[day][interval][room] == ():
                        positions.append((day, interval, room))
    return positions

def __all_actions2__(actions):
    '''
    Now, generating for each teacher and their subject (teacher, subject) "card" 
    all possible days and intervals without satisfying the prefferances 
    with days and intervals just to be sure to fullfill the rooms and timetable.
    Of course, some teachers may have more then 7 intervals, 
    but this restriction will be fullfilled in a separate function.
    '''
    evryting = []
    everything = []
    for materie, cineva in actions:
        nr = len(zile) * len(intervale)
        for _ in range(nr):
            evryting.append((materie, cineva))
    return evryting

# it stores as many cards as many days and intervals for every teacher
all_actions = __all_actions2__(actions)

def __get_all_possible_places2__(all_actions, cobai, sched):
    '''
    Generate all possible "moves"/places to put all the "cards"
    Quite uninspired as it should have been a dictionary ;_;
    (only now do I see it) 
    '''
    idk = {}
    for act in all_actions:
        idk[act] = []
        dummy = __where21__(act, sched, cobai)
        idk[act] = dummy
    return idk

# it stores all the possible places for (teacher, subject) card, 
# where can be put in timetable
evriuere = __get_all_possible_places2__(all_actions, cobai, vesnic_gol)

def __rand_shuffle_gen1__(sched, cobai):
    '''
    1st verion of generating a timetable, by shuffling 
    the test timetable (cobai) with everything in it
    In time I realised that there can be other ways of generating a timetable, 
    see 2nd version. This one does not satisfy any restiction. =(
    '''
    orar_nou = deepcopy(sched)
    for zi in orar_nou:
        for interval in orar_nou[zi]:
            for sala in orar_nou[zi][interval]:
                if orar_nou[zi][interval][sala] == ():
                    if cobai[zi][interval][sala] != []:
                        if randint(0, 1) == 0:
                            orar_nou[zi][interval][sala] = cobai[zi][interval][sala][randint(0, len(cobai[zi][interval][sala]) - 1)]
                        else:
                            shuffle(cobai[zi][interval][sala])
                            orar_nou[zi][interval][sala] = cobai[zi][interval][sala].pop(0)
    return orar_nou

# orar_nou = __rand_shuffle_gen__(sched, cobai)

def __let_s_see__(sched, cobai):
    '''
    This one is an unhappy try of mine for generating reliable timetables,
    until I moved to the algorithms
    '''
    idk = None
    nr = 2
    while nr != 0:
        orar_nou = __rand_shuffle_gen1__(sched, cobai)
        # nr = __compute_conflicts__(orar_nou)
        if nr == 0:
            idk = orar_nou
    return idk

# for the time I tried to generate a good timetable
# idkk = __let_s_see__(sched, cobai)
# print(idkk)

# for the time I descovered pretty_printing thing in utils.py and tested it
# filename = f'inputs/orar_mic_exact.yaml'
filename = f'dummy.yaml'
# print(pretty_print_timetable(idkk, filename))

# def __hai_ca_da__(sched, cobai):
    # '''
    # This one is an unhappy try of mine for generating reliable timetables,
    # until I moved to the algorithms
    # '''
#     idk = []
#     for _ in range(100):
#         hbrnm = __let_s_see__(sched, cobai)
#         print(hbrnm)
#         idk.append(hbrnm)
#     return idk
                
# nuj_fra = __hai_ca_da__(sched, cobai)
# print(nuj_fra)