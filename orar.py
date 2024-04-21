from __future__ import annotations
import yaml
from typing import Callable
from copy import copy
from copy import deepcopy
from functools import reduce
import numpy as np
import random
# imports

# reader
data = None
with open("dummy.yaml") as stream:
    try:
        data = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
        
#parser
materii = data['Materii']
intervale = data['Intervale']
profi = data['Profesori']
sali = data['Sali']
zile = data['Zile']

# taken from MCTS laboratory, decided to start with it, idk why
# tried to adapt it to me
HEIGHT, WIDTH = len(intervale), len(zile)
TIMETABLE, NEXT_VERSION = 0, 1

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

# print initial state / the TIMETABLE cnt state
def __print_state__(states, TIMETABLE):
    print(states[TIMETABLE])
    
# __print_state__(states, TIMETABLE)
# print()
# print("--------------------------------------------")
# print()

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
def __get_teach_poate__(zile, intervale, profi):
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
                        for ore in range (start, end, 2):
                            endd = ore + 2
                            interv = (start, endd)
                            ore_ok.append(interv)
                    else:
                        ore_ok.append((start, end))
                else:
                    zile_ok.append(j)
                teach[i]['ore_ok'] = ore_ok
                teach[i]['zile_ok'] = zile_ok
    return teach

permisiuni = __get_teach_poate__(zile, intervale, profi)

# I will have some random functions, with no utility, like this one, 
# this generates all possible actions from the lists of days, intervals, teachers 
# in order to satisfact the constraints of days and intervals for teachers
def __generate_actions1__(materii, profi, sali):
    actions = []
    for i in profi:
        ore_ok = []
        zile_ok = []
        materii_prof = []
        for j in profi[i]['Constrangeri']:
            e_ora = 0
            if '!' not in j:
                for char in j:
                    if char.isdigit():
                        e_ora = 1
                        break
                if e_ora:
                    start, end = map(int, j.split('-'))
                    if start == 8:
                        j='0'+j
                    if (end - start) > 2:
                        for ore in range (start, end, 2):
                            endd = ore + 2
                            if ore == 8:
                                oree = '0'+str(ore)
                            else:
                                oree = str(ore)
                            interv = oree + '-' + str(endd)
                            ore_ok.append(interv)
                    else:
                        ore_ok.append(j)
                else:
                    zile_ok.append(j)
        for j in profi[i]['Materii']:
            materii_prof.append(j)
        # nume = None
        # nume = ''.join(char for char in i if char.isupper())
        for j in materii_prof:
            for k in ore_ok:
                for l in zile_ok:
                    for m in sali:
                        if j in sali[m]['Materii']:
                            for n in materii:
                                dummy = (l, k, j, m, i)
                                actions.append(dummy)
    good_actions = sorted(list(set(actions)), key=lambda x: (x[0], x[1], x[2]))
    return good_actions
longer = __generate_actions1__(materii, profi, sali)

# just teach and subject
def __generate_actions2__(profi):
    actions = []
    for i in profi:
        for j in profi[i]['Materii']:
            dummy = (j, i)
            actions.append(dummy)
    return actions

actions = __generate_actions2__(profi)

def __populate_cobai__(cobai, actions):
    for i in actions:
        start, end = map(int, i[1].split('-'))
        intv = (start, end)
        # oh darling, wrong keys
        cobai[i[0]][str(intv)][i[3]].append((i[2], i[4]))
        
__populate_cobai__(cobai, longer)
print(cobai)

# gets the overlaps that occure in a dict
def __get_overlaps__(cobai):
    overlaps = []
    nr = 0
    for zi in cobai:
        for ore in cobai[zi]:
            for sala1 in cobai[zi][ore]:
                for sala2 in cobai[zi][ore]:
                    for tuplu1 in cobai[zi][ore][sala1]:
                        for tuplu2 in cobai[zi][ore][sala2]:
                            if tuplu1 != tuplu2 and tuplu1[1] == tuplu2[1]:
                                overlaps.append((zi, ore, tuplu1[1]))
                                nr += 1
                    break
    return nr, overlaps

conflicts, overlaps = __get_overlaps__(cobai)

def __where__(action, sched, permisiuni, cobai):
    positions = []
    pos = []
    for day in sched:
        for interval in cobai[day]:
            for room in cobai[day][interval]:
                for tuplu in cobai[day][interval][room]:
                    if action[1] in tuplu and sched[day][interval][room] == ():
                        positions.append((day, interval, room))
    for posi in positions:
        #oh, darling, wrong keys
        ok = 0
        for ceva in permisiuni[action[1]]['ore_ok']:
            if str(ceva) == str(posi[1]):
                ok += 1
        if posi[0] in permisiuni[action[1]]['zile_ok']:
            ok += 1
        if ok == 2:
            pos.append(posi)
    return pos

def __all_actions__(actions, permisiuni):
    evryting = []
    everything = []
    for materie, cineva in actions:
        nr = len(permisiuni[cineva]['zile_ok']) * len(permisiuni[cineva]['ore_ok'])
        for _ in range(nr):
            evryting.append((materie, cineva))
    return evryting

all_actions = __all_actions__(actions, permisiuni)

def __get_all_possible_places__(all_actions, permisiuni, cobai, sched):
    idk = {}
    for act in all_actions:
        idk[act] = []
        dummy = __where__(act, sched, permisiuni, cobai)
        idk[act] = dummy
    return idk

evriuere = __get_all_possible_places__(all_actions, permisiuni, cobai, sched)
