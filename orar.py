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

# my pretty print
# print()
# print("--------------------------------------------")
# print()

# initialize state
def __init_state__(zile, intervale, sali):
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
sched = __init_state__(zile, intervale, sali)
states.append(sched)

# initialize timetable with all possibilities, on its basis i generate the rest
def __init_cobai__(zile, intervale, sali):
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

# this genereates all the intervals in which a teacher can teach
# tthis is soft constraint, we'll fix it later
# first we have to deal with the hard/logistical ones
def __get_teach_poate__(profi):
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

# I will have some random functions, with no utility, like this one, 
# this generates all possible actions from the lists of days, intervals, teachers 
# in order to satisfact the constraints of days and intervals for teachers
def __generate_actions12__(profi, sali, zile, intervale):
    actions = []
    for i in profi:
        materii_prof = []
        for j in profi[i]['Materii']:
            materii_prof.append(j)
        # nume = None
        # nume = ''.join(char for char in i if char.isupper())
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

# just teach and subject, no constraints =)
def __generate_actions2__(profi):
    actions = []
    for i in profi:
        for j in profi[i]['Materii']:
            dummy = (j, i)
            actions.append(dummy)
    return actions

actions = __generate_actions2__(profi)

def __populate_cobai2__(cobai, actions):
    for i in actions:
        cobai[i[0]][i[1]][i[3]].append((i[4], i[2]))
        
__populate_cobai2__(cobai, longer2)

def __get__conflicts__(sched):
    nr = 0
    for zi in sched:
        for ore in sched[zi]:
            for sala in sched[zi][ore]:
                # sched[zi][ore][sala][0] asta e prof
                # permisiuni[sched[zi][ore][sala][0]]
                if zi in permisiuni[sched[zi][ore][sala][0]]['zile_ok']:
                    for tupl in permisiuni[sched[zi][ore][sala][0]]['ore_ok']:
                        if str(tupl) != ore:
                            nr += 1
    return nr

# this is on a schedule, not a cobai, and is about the rooms
def __other_conflicts__(board):
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

# this is on a schedule, not a cobai, and is about the overlaps
def __compute_conflicts__(board):
    nr = 0
    for zi in board:
        for ore in board[zi]:
            for sala1 in board[zi][ore]:
                for sala2 in board[zi][ore]:
                    if sala1 != sala2:
                        if len(board[zi][ore][sala1]) >= 1 and len(board[zi][ore][sala2]) >= 1 and board[zi][ore][sala1][0] == board[zi][ore][sala2][0]:
                            nr += 1
                break
    num = __other_conflicts__(board)
    # nrr = __get__conflicts__(board)
    nr += num
    # nr += nrr
    return nr

def __where2__(actionn, sched, cobai):
    positions = []
    for day in sched:
        for interval in cobai[day]:
            for room in cobai[day][interval]:
                for tuplu in cobai[day][interval][room]:
                    if len(actionn) >= 4 and actionn[2] == tuplu[1] and actionn[4] == tuplu[0] and sched[day][interval][room] == ():
                        positions.append((day, interval, room))
    return positions

def __where21__(action, sched, cobai):
    positions = []
    for day in sched:
        for interval in cobai[day]:
            for room in cobai[day][interval]:
                for tuplu in cobai[day][interval][room]:
                    if len(action) >= 2 and action[0] == tuplu[1] and action[1] == tuplu[0] and sched[day][interval][room] == ():
                        positions.append((day, interval, room))
    return positions

def __all_actions2__(actions):
    evryting = []
    everything = []
    for materie, cineva in actions:
        nr = len(zile) * len(intervale)
        for _ in range(nr):
            evryting.append((materie, cineva))
    return evryting

all_actions = __all_actions2__(actions)

def __get_all_possible_places2__(all_actions, cobai, sched):
    idk = {}
    for act in all_actions:
        idk[act] = []
        dummy = __where21__(act, sched, cobai)
        idk[act] = dummy
    return idk

evriuere = __get_all_possible_places2__(all_actions, cobai, sched)

def __rand_shuffle_gen__(sched, cobai):
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
    idk = None
    nr = 2
    while nr != 0:
        orar_nou = __rand_shuffle_gen__(sched, cobai)
        nr = __compute_conflicts__(orar_nou)
        if nr == 0:
            idk = orar_nou
    return idk

# idkk = __let_s_see__(sched, cobai)
# print(idkk)

# filename = f'inputs/orar_mic_exact.yaml'
filename = f'dummy.yaml'
# print(pretty_print_timetable(idkk, filename))

# def __hai_ca_da__(sched, cobai):
#     idk = []
#     for _ in range(100):
#         hbrnm = __let_s_see__(sched, cobai)
#         print(hbrnm)
#         idk.append(hbrnm)
#     return idk
                
# nuj_fra = __hai_ca_da__(sched, cobai)
# print(nuj_fra)