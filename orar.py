from __future__ import annotations
import sys
import yaml
from typing import Callable
from copy import copy
from copy import deepcopy
from functools import reduce
import numpy as np
from utils import pretty_print_timetable
from random import shuffle, seed, randint
import random
# imports
# --------------------------------------------------------------------------------------
# formatting
# merge
def __my_pretty_print__(Any):
    '''
    My pretty print for testing purposes
    '''
    print()
    print(Any)
    print()
    print("--------------------------------------------")
# --------------------------------------------------------------------------------------
# initialize things, make the background, let's say
# merge
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

# discutabil
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
# --------------------------------------------------------------------------------------
# T/F
# merge
def right_day_interval(teacher, action, permisiuni):
    '''
    Action is a longer card that consists of (day, interval, room, teacher, subject) and
    we verify on day, interval, room if the teacher can teach
    '''
    if action[0] in permisiuni[teacher]['zile_ok'] and action[1] in permisiuni[teacher]['ore_ok']:
        return True
    return False

# merge
def right_room(room, action, sali):
    '''
    Action is a longer card that consists of (day, interval, room, teacher, subject) and
    we verify on action if room is suitable for that subject
    '''
    return action[4] in sali[action[2]]['Materii']

# merge
def right_teacher(teacher, action, profi):
    return action[3] in profi[teacher]['Materii']
# --------------------------------------------------------------------------------------
# getters
# merge, desi e discutabil
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
# meh
def __get_teach_table__(board, teacher, zile, intervale, sali):
    '''
    Trying to achieve the bonus bullet, but it's just a thought...
    Makes a timetable for each teacher in order to see the breaks
    '''
    table = {}
    table = __init_state__(zile, intervale, sali)
    for zi in board:
        for ore in board[zi]:
            for sala in board[zi][ore]:
                if teacher in board[zi][ore][sala]:
                    table[zi][ore][sala] = board[zi][ore][sala]
    return table
# --------------------------------------------------------------------------------------
# generators of parts for timetable generator
# merge
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
                            dummy = (k, l, m, i, j)
                            actions.append(dummy)
    good_actions = sorted(list(set(actions)), key=lambda x: (x[0], x[1], x[2]))
    return good_actions

# merge x 2
def __generate_actions1__(profi, sali, zile, intervale):
    ''' 
    Generates all possible actions from the lists of days, intervals, teachers
    in order to satisfact the constraints of days, intervals 
    and their own subjects with rooms for each subject for teachers
    '''
    actions = []
    for zi in zile:
        for ore in intervale:
            for sala in sali:
                for teach in profi:
                    for materie in materii:
                        dummy = (zi, ore, sala, teach, materie)
                        actions.append(dummy)
    return actions

# discutabil
def __generate_actions2__(profi):
    '''
    Generates "cards" of teachers and the subject of teach
    in order to put a card in the right place, acording to the constraints
    Bullet 2 from hard constraints
    '''
    actions = []
    for i in profi:
        for j in profi[i]['Materii']:
            dummy = (i, j)
            actions.append(dummy)
    return actions

# discutabil -> nici nu stiu dk o folosesc -> O S-O FOLOSESC!
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
                    if len(actionn) >= 4 and actionn[4] == tuplu[1] and actionn[3] == tuplu[0] and sched[day][interval][room] == ():
                        positions.append((day, interval, room))
    return positions

# discutabil
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
                    if len(action) >= 2 and action[0] == tuplu[0] and action[1] == tuplu[1] and sched[day][interval][room] == ():
                        positions.append((day, interval, room))
    return positions

# discutabil x 2
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

# discutabil x 3
def __get_all_possible_places2__(all_actions, cobai, sched):
    '''
    Generate all possible "moves"/places to put 
    all the "cards" (teacher, course)
    '''
    idk = {}
    for act in all_actions:
        idk[act] = []
        dummy = __where21__(act, sched, cobai)
        idk[act] = dummy
    return idk
# --------------------------------------------------------------------------------------
# conflicts
# mainly all are used
def __get__pref_conflicts__(sched, permisiuni):
    '''
    Checks soft permissions without the !Pauza constraint
    Bullets 1, 2, 3 from soft constraints
    '''
    nr = 0
    for zi in sched:
        for ore in sched[zi]:
            for sala in sched[zi][ore]:
                if len(sched[zi][ore][sala]) >= 1 and zi in permisiuni[sched[zi][ore][sala][0]]['zile_ok']:
                    for tupl in permisiuni[sched[zi][ore][sala][0]]['ore_ok']:
                        if str(tupl) != ore:
                            nr += 1
    return nr

# da!
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

def __get_overh_conflicts__(board, profi):
    '''
    Returns the number of teachers that have more than 7 intervals 
    -> it is a constraint, actually, so returns the number of 
    this type of conflicts
    '''
    nr = 0
    teach = {}
    for t in profi:
        teach[t] = 0
    for zi in board:
        for ore in board[zi]:
            for sali in board[zi][ore]:
                if len(board[zi][ore][sali]) >= 1:
                    teach[board[zi][ore][sali][0]] += 1
    for t in teach:
        if teach[t] > 7:
            nr += 1
    return nr

def __get_hconflicts__(board, profi):
    '''
    Get number of hard conflicts
    '''
    nr = 0
    i = __get_capacity_conflicts__(board)
    j = __get_overlap_conflicts__(board)
    k = __get_overh_conflicts__(board, profi)
    nr += i
    nr += j
    nr += k
    return nr

def __get_sconflicts__(board, permisiuni):
    '''
    Get number of soft conflicts
    '''
    nr = 0
    i = __get__pref_conflicts__(board, permisiuni)
    nr += i
    return nr

def __get_all_conflicts__(board, profi, permisiuni):
    '''
    Get number of all types of conflicts
    '''
    nr = 0
    conflicts = []
    i = __get_hconflicts__(board, profi)
    j = __get_sconflicts__(board, permisiuni)
    nr += i
    nr += j
    return nr
# --------------------------------------------------------------------------------------
# the timetable generator part
# generate from a list
def __make_move__(sched, profi, cobai):
    places = []
    acts = __generate_actions2__(profi)
    all_acts = __all_actions2__(acts)
    index1 = randint(0, len(all_acts)-1)
    an_action = all_acts[index1]
    all_acts.remove(an_action)
    places = __where21__(an_action, sched, cobai)
    index2 = randint(0, len(places)-1)
    a_place = places[index2]
    sched[a_place[0]][a_place[1]][a_place[2]] = an_action
    dummy = (a_place[0], a_place[1], a_place[2])
    return dummy

# vedem
def __aply_move__(action, sched):
    '''
    Just puts a longer card in timetable. No more shorter cards
    '''
    dummy = ()
    if sched[action[0]][action[1]][action[2]] == ():
        sched[action[0]][action[1]][action[2]] = (action[3], action[4])
        dummy = (action[0], action[1], action[2])
    return dummy

def __undo_move__(sched, move):
    sched[move[0]][move[1]][move[2]] = ()
# --------------------------------------------------------------------------------------
# generate from a timetable with all possibilities
def __populate_cobai2__(cobai, actions):
    '''
    Here is generated a whole timetable, but with all constraints not satisfied \n
    Basically, is a timetable with all possible arrangements/with all possibilities \n
    On its basis we satisfact/choose what to put in the right timetable
    '''
    for i in actions:
        cobai[i[0]][i[1]][i[2]].append((i[3], i[4]))

def get_aviable_actions(state, longer, cobai):
    '''
    Here are generated all possible places for a long tuple of
    (day, interval, room, teacher, subject) in an array.
    '''
    idk = []
    for tuplee in longer:
        if state[tuplee[0]][tuplee[1]][tuplee[2]] == () and (tuplee[3], tuplee[4]) in cobai[tuplee[0]][tuplee[1]][tuplee[2]]:
            idk.append(tuplee)
    return idk

# --------------------------------------------------------------------------------------
# algorithms part
# hill climbing

def is_final(state):
    '''
    For me, the final state is the one in which all students have where to stay
    '''
    return __get_capacity_conflicts__(state) == 0
    
def hill_climbing(initial_state, actions, profi, cobai, max_iters):
    '''
    A modified version from the HC laboratory
    '''
    current_state = deepcopy(initial_state)
    current_conflicts = __get_hconflicts__(current_state, profi)
    best_conflicts = current_conflicts
    best_state = deepcopy(current_state)
    for _ in range(max_iters):
        current_conflicts = __get_hconflicts__(current_state, profi)
        okok = get_aviable_actions(current_state, actions, cobai)
        if okok == []:
            break
        index = randint(0, len(okok) - 1)
        action = okok[index]
        vecin = deepcopy(current_state)
        move = __aply_move__(action, vecin)
        confl = __get_hconflicts__(vecin, profi)
        current_conflicts = __get_hconflicts__(current_state, profi)
        if current_conflicts < best_conflicts:
            best_conflicts = current_conflicts
        else:
            # __undo_move__(current_state, action)
            best_state = deepcopy(vecin)
            best_conflicts = confl
            current_state = deepcopy(vecin)
    return best_state

def random_restart_hill_climbing(initial, max_restarts, run_max_iters, actions, profi):
    '''
    I tried something but it didn't work.
    '''
    total_iters, total_states = 0, 0
    state = deepcopy(initial)
    for _ in range(max_restarts):
        stare_curr = hill_climbing(state, actions, profi, run_max_iters)
        total_iters += 1
        total_states += 1
        if ok:
            break
        else:
            state = stare_curr
    return state

# --------------------------------------------------------------------------------------
# main
if __name__ == "__main__":
    ok = 0
    if len(sys.argv) < 3:
        print("Please provide algo + input.")
    else:
        if sys.argv[1] == "hc":
            ok = 1
        else:
            if sys.argv[1] == "mcts":
                ok = 2
            else:
                print("Please provide right algo")
    filename = "inputs/" + sys.argv[2]
    # my reader
    data = None
    with open(filename) as stream:
        try:
            data = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            
    #parser, because 'duh!
    materii = data['Materii']
    intervale1 = data['Intervale']
    profi = data['Profesori']
    sali = data['Sali']
    zile = data['Zile']
    intervale = [eval(i) for i in intervale1]

    # initialises the state machine let's call it
    states = []

    # we will foreever have an empty timetable
    vesnic_gol = __init_state__(zile, intervale, sali)

    # we start with this
    test = __init_state__(zile, intervale, sali)

    # on the basis of cobai we generate timetables
    cobai = __init_cobai__(zile, intervale, sali)

    # each teacher has preferances
    permisiuni = __get_teach_poate__(profi)

    longer = __generate_actions1__(profi, sali, zile, intervale)

    # array with (day, interval, room, teacher, course) tuples
    longer2 = __generate_actions12__(profi, sali, zile, intervale)

    # array with (teacher, course_taught_by_that_teacher) tuple aka 'card'
    actions = __generate_actions2__(profi)

    # it stores as many 'cards' as many days and intervals for every teacher
    all_actions = __all_actions2__(actions)

    # it stores all the possible places for (teacher, subject) card, 
    # where can be put in timetable
    evriuere = __get_all_possible_places2__(all_actions, cobai, vesnic_gol)

    if ok == 1:
        # we populate the timetable with all arrangements
        __populate_cobai2__(cobai, longer)
        state = hill_climbing(test, longer, profi, cobai, 10000)
        print(pretty_print_timetable(state, filename))