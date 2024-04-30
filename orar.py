from __future__ import annotations
import sys
import yaml
from copy import deepcopy
from utils import pretty_print_timetable
from random import randint
from math import sqrt, log, ceil
import time
import matplotlib.pyplot as plt

# imports
# --------------------------------------------------------------------------------------
# initialize things
def __init_state__(days, intervals, rooms):
    '''
    Initialize state
    A state is a whole timetable of this type {str : {(int, int) : {str : (str, str)}}}
    Bullet 1 from task satisfied -> just one subject per room, no array\n
    Args:\n
    - days - [string], with days \n
    - intervals - [(int, int)] with hour intervals \n
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers
    '''
    state = {}
    for idx_i, i in enumerate(days):
        state[i] = {}
        for idx_j, j in enumerate(intervals):
            state[i][j] = {}
            for idx_k, k in enumerate(rooms):
                state[i][j][k] = ()
    return state
# --------------------------------------------------------------------------------------
# getters
def __get_teach_poate__(teachers):
    '''
    Generates all the intervals in which a teacher can teach.
    Bullets 1, 2, 3 from soft constraints\n
    Args:\n
    - teachers - {string: {'Materii': [string], 'Constrangeri': }} 
        - what teachers are there, what they teach and their preferences
    '''
    teach = {}
    for i in teachers:
        good_intervals = []
        days_ok = []
        teach[i] = {}
        for j in teachers[i]['Constrangeri']:
            hour = 0
            if '!' not in j:
                for char in j:
                    if char.isdigit():
                        hour = 1
                        break
                if hour:
                    start, end = map(int, j.split('-'))
                    if (end - start) > 2:
                        for hourss in range(start, end, 2):
                            endd = hourss + 2
                            interv = (hourss, endd)
                            good_intervals.append(interv)
                        if end % 2 != 0:
                            good_intervals.append((end - 2, end))
                    else:
                        good_intervals.append((start, end))
                else:
                    days_ok.append(j)
                teach[i]['good_intervals'] = good_intervals
                teach[i]['days_ok'] = days_ok
    return teach

def __get_min_max_room_subject__(rooms, courses):
    '''
    Returns a dictionary with minum and maximum number of rooms per subject\n
    Args:
    - courses - {string: int}, with subject and number of students enrolled in \n
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers
    '''
    dictt = {}
    for subject in courses:
        dictt[subject] = {}
        mini = 9999
        maxi = 0
        for room in rooms:
            if subject in rooms[room]['Materii']:
                if mini > rooms[room]['Capacitate']:
                    mini = rooms[room]['Capacitate']
                if maxi < rooms[room]['Capacitate']:
                    maxi = rooms[room]['Capacitate']
        dictt[subject]['Min'] = ceil(courses[subject] / maxi)
        dictt[subject]['Max'] = ceil(courses[subject] / mini)
    return dictt

def __get_nr_subjects__(state, subject):
    '''
    Finds the number of times a subject appears on the timetable\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}} \n
    - subject - string
    '''
    nr = 0
    for day in state:
        for hours in state[day]:
            for room in state[day][hours]:
                if state[day][hours][room] is not None and state[day][hours][room] != () and len(state[day][hours][room]) >= 2:
                    if state[day][hours][room][1] == subject:
                        nr += 1
    return nr

def __get_nr_hours__(state, prof):
    '''
    Finds the intervals a teacher teaches in the whole timetable generated at a certain point\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}} \n
    - teacher: string
    '''
    nr = 0
    for day in state:
        for hours in state[day]:
            for room in state[day][hours]:
                if state[day][hours][room] is not None and state[day][hours][room] != () and len(
                        state[day][hours][room]) >= 2:
                    if state[day][hours][room][0] == prof:
                        nr += 1
    return nr

def __get_min_subject__(courses):
    '''
    Finds the subject with the minimum number of students enrolled in\n
    Args:\n
    - courses - {string: int}, with subject and number of students enrolled in
    '''
    mini = 9999
    minii = None
    for subject in courses:
        if mini > courses[subject]:
            mini = courses[subject]
            minii = subject
    return minii

def __how_many__(state, courses, rooms):
    '''
    Finds how many students are enrolled in a subject at a certain time from the whole timetable\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}} \n
    - courses - {string: int}, with subject and number of students enrolled in\n
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers
    '''
    dictt = {}
    for subject in courses:
        dictt[subject] = 0
    if state != {} and state is not None:
        for day in state:
            if state[day] != {} and state[day] is not None:
                for hours in state[day]:
                    if state[day][hours] != {} and state[day][hours] != {}:
                        for room in state[day][hours]:
                            if state[day][hours][room] is not None and state[day][hours][room] != () and len(state[day][hours][room]) >= 2:
                                dictt[state[day][hours][room][1]] += rooms[room]['Capacitate']
    return dictt
# --------------------------------------------------------------------------------------
# checkers -> to see if rooms fullfilled etc
def __ok__(state, subject, rooms, courses):
    '''
    Checks whether a subject has at least as many rooms as the maximum number of rooms at a certain point in timetable\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}} \n
    - subject - string\n
    - courses - {string: int}, with subject and number of students enrolled in'n
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers
    '''
    dictt = __get_min_max_room_subject__(rooms, courses)
    return __get_nr_subjects__(state, subject) >= dictt[subject]['Max']

def __done__(state, prof):
    '''
    Checks whether a teacher has their norm of 14h\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}} \n
    - prof - string
    '''
    return __get_nr_hours__(state, prof) < 7

def __acoperit_minim__(state, courses, rooms):
    '''
    Checks whether the subject with the least students enrolled in has all the students enrolled in\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}}
    - courses - {string: int}, with subject and number of students enrolled in
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers
    '''
    subject = __get_min_subject__(courses)
    nr = 0
    if state != {} and state is not None:
        for day in state:
            if state[day] != {} and state[day] is not None:
                for hours in state[day]:
                    if state[day][hours] is not None and state[day][hours] != {}:
                        for room in state[day][hours]:
                            if state[day][hours][room] is not None and state[day][hours][room] != () and len(state[day][hours][room]) >= 2:
                                if state[day][hours][room][1] == subject:
                                    nr += rooms[room]['Capacitate']
    return nr >= courses[subject]
# --------------------------------------------------------------------------------------
# generators
def __get_available_actions__(state, teachers, rooms, days, intervals, courses, permissions):
    '''
    Generate all the possible actions/moves/combinations at a certain point in timetable 
    in order to complete the timetable according to the restrictions\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}}\n
    - courses - {string: int}, with subject and number of students enrolled in\n
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers\n
    - teachers - {string: {'Materii': [string], 'Constrangeri': }} 
        - what teachers are there, what they teach and their preferences\n
    - days - [string], with days \n
    - intervals - [(int, int)] with hour intervals \n
    - permissions - [(string, (int, int), string, string, string)] - [(day, interval, room, teacher, subject)] 
        - array with all possible moves to put in the timetable
    '''
    actions = []
    min_subject = max(courses, key=courses.get)
    total_students_min_subject = courses[min_subject]
    for day in days:
        for hours in intervals:
            for room in rooms:
                for t in teachers:
                    if __done__(state, t):  
                        for subject in courses:
                            if state[day][hours][room] == ():
                                if subject in teachers[t]['Materii']:  
                                    if subject in rooms[room]['Materii']:  
                                        if day in permissions[t]['days_ok']:  
                                            if hours in permissions[t]['good_intervals']:  
                                                if not __ok__(state, subject, rooms, courses):  
                                                    if not __acoperit_minim__(state, courses, rooms): 
                                                        if __get_nr_subjects__(state, subject) < total_students_min_subject:
                                                            overlap = False
                                                            for room2 in rooms:
                                                                if room2 != room:
                                                                    if state[day][hours][room2] != () and len(
                                                                            state[day][hours][room2]) >= 1 and \
                                                                            state[day][hours][room2][0] == t:
                                                                        overlap = True  
                                                                        break
                                                            if not overlap:
                                                                dummy = (day, hours, room, t, subject)
                                                                actions.append(dummy)
    return actions

def __get_available_actions1__(state, profi, sali, zile, intervale, materii, permisiuni):
    ''' 
    Generates all possible actions from the lists of days, intervals, teachers
    in order to satisfact the constraints of days, intervals 
    and their own subjects with rooms for each subject for teachers
    Bullets 2, 5, 6 from hard constraints
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}}\n
    - courses - {string: int}, with subject and number of students enrolled in\n
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers\n
    - teachers - {string: {'Materii': [string], 'Constrangeri': }} 
        - what teachers are there, what they teach and their preferences\n
    - days - [string], with days \n
    - intervals - [(int, int)] with hour intervals \n
    - permissions - [(string, (int, int), string, string, string)] - [(day, interval, room, teacher, subject)] 
        - array with all possible moves to put in the timetable
    '''
    actions = []
    for sub in materii:
        for room in sali:
            for t in profi:
                for hours in intervale:
                    for day in zile:
                        if state[day][hours][room] == ():
                            if sub in profi[t]['Materii']: # proful preda materia aia
                                if sub in sali[room]['Materii']: # materia se face in sala aia
                                    if day in permisiuni[t]['days_ok']: # proful poate in ziua aia
                                        if hours in permisiuni[t]['good_intervals']: # proful poate preda in orele alea
                                            overlap = False
                                            for room2 in sali:
                                                if room2 != room:
                                                    if state[day][hours][room2] != () and len(state[day][hours][room2]) >= 1 and state[day][hours][room2][0] == t:
                                                        overlap = True # verific sa nu fie aceeasi persoana in doua locuri diferite in acelasi timp
                                                        break
                                            if not overlap:
                                                dummy = (day, hours, room, t, sub)
                                                actions.append(dummy)
    return actions

def __apply_action__(action, state):
    '''
    Just puts a longer card in timetable. No mhourss shorter cards\n
    Args:\n
    - action - (string, (int, int), string, string, string) - (day, interval, room, teacher, subject) - move/possibility/match/card\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}
    '''
    dummy = ()
    if state[action[0]][action[1]][action[2]] == ():
        state[action[0]][action[1]][action[2]] = (action[3], action[4])
        dummy = (action[0], action[1], action[2])
    return dummy
# --------------------------------------------------------------------------------------
# conflicts
def __constr__(state, permisiuni, rooms, teachers, courses):
    nr = 0
    flagg = False
    # daca toate materiile au toti studentii inrolati/loc
    dictionaryy = __how_many__(state, courses, rooms)
    for mat in dictionaryy:
        if dictionaryy[mat] < courses[mat]:
            flagg = True
            print("Nu se acopera materia " + mat)
    if flagg:
        nr += 1
    if state is not None and state != {}:
        for day in state:
            if state[day] is not None and state[day] != {}:
                for hours in state[day]:
                    if state[day][hours] is not None and state[day][hours] != {}:
                        for room in state[day][hours]:
                            if state[day][hours][room] is not None and state[day][hours][room] != () and len(state[day][hours][room]) >= 2:
                                (teacher, subject) = state[day][hours][room]
                                if state[day][hours][room] != ():
                                    if __get_nr_hours__(state, subject) > 7: # daca proful are mai mult de 7 intrevale, vezi functia de mai sus
                                        nr += 1
                                        print(teacher + " are mai mult de 7 intervale")
                                    if subject not in teachers[teacher]['Materii']: # proful nu preda materia aia
                                        nr += 1
                                        print(teacher + " nu preda materia " + subject)
                                    if subject not in rooms[room]['Materii']: # materia nu se face in sala aia
                                        nr += 1
                                        print(subject + " nu se face in sala " + room)
                                    if day not in permisiuni[teacher]['days_ok']: # proful nu poate in ziua aia
                                        nr += 1
                                        print(teacher + " nu poate in ziua " + day)
                                    if hours not in permisiuni[teacher]['good_intervals']: # proful nu poate preda in orele alea
                                        nr += 1
                                        print(teacher + " nu poate in orele " + str(hours))
                                    for room2 in rooms:
                                        if room2 != room:
                                            if state[day][hours][room2] != () and len(state[day][hours][room2]) >= 1 and state[day][hours][room2][0] == teacher:
                                                nr += 1
                                                print(teacher + " preda in doua sali diferite ")
                                              
    # intr-un interval orar si intr-o sala se sustine o singura materie de catre un singur profesor
    # -> din modul de constructie/generare -> dictionar in dictionar in dictionar -> chei unice
    
    # intr-un interval orar, un profesor tine o singura materie, intr-o singura sala
    # -> din modul de constructie/generare -> desi e tuplu de 2 elemente
    
    # o sala permite intr-un interval orar prezenta unui numar de studenti
    # mai mic sau egal decat capacitatea ei maxima -> din modul de constructie 
    # -> cand am numarat, am luat calupuri de cate <capacitate sala> de studenti

    return nr

def __get__pref_conflicts__(state, permissions):
    '''
    Checks soft permissions without the !Pauza constraint
    Bullets 1, 2, 3 from soft constraints\n 
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}\n
    - permissions - [(string, (int, int), string, string, string)] - [(day, interval, room, teacher, subject)] 
        - array with all possible moves to put in the timetable
    '''
    nr = 0
    for zi in state:
        for hourss in state[zi]:
            for sala in state[zi][hourss]:
                if len(state[zi][hourss][sala]) >= 1 and state[zi][hourss][sala][0] is not None and zi in permissions[state[zi][hourss][sala][0]]['days_ok']:
                    for tupl in permissions[state[zi][hourss][sala][0]]['good_intervals']:
                        if str(tupl) != hourss:
                            nr += 1
    return nr

def __get_capacity_conflicts__(state):
    '''
    Checks whether all students have a seat in the rooms
    Bullet 4 from hard constraints\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}\n
    '''
    nr = 0
    vector_caracteristic = {}
    for i in courses:
        vector_caracteristic[i] = 0
    for zi in state:
        for hourss in state[zi]:
            for sala in state[zi][hourss]:
                if len(state[zi][hourss][sala]) >= 1:
                    vector_caracteristic[state[zi][hourss][sala][1]] += rooms[sala]['Capacitate']
    for i in vector_caracteristic:
        if vector_caracteristic[i] < courses[i]:
            nr += 1
    return nr

def __get_overlap_conflicts__(state):
    '''
    Checks to see if a teacher is NOT in two different places in the same time
    Bullet 1 from hard constraints\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}\n
    '''
    nr = 0
    for zi in state:
        for hourss in state[zi]:
            for sala1 in state[zi][hourss]:
                for sala2 in state[zi][hourss]:
                    if sala1 != sala2:
                        if len(state[zi][hourss][sala1]) >= 1 and len(state[zi][hourss][sala2]) >= 1 and state[zi][hourss][sala1][0] == state[zi][hourss][sala2][0]:
                            nr += 1
                break
    return nr

def __get_overh_conflicts__(state, teachers):
    '''
    Returns the number of teachers that have mhourss than 7 intervals 
    -> it is a constraint, actually, so returns the number of 
    this type of conflicts\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}\n
    - teachers - {string: {'Materii': [string], 'Constrangeri': }} 
        - what teachers are there, what they teach and their preferences\n
    '''
    nr = 0
    teach = {}
    for t in teachers:
        teach[t] = 0
    for zi in state:
        for hourss in state[zi]:
            for rooms in state[zi][hourss]:
                if len(state[zi][hourss][rooms]) >= 2 and state[zi][hourss][rooms][0] is not None:
                    teach[state[zi][hourss][rooms][0]] += 1
    for t in teach:
        if teach[t] > 7:
            nr += 1
    return nr

def __get_hconflicts__(state, teachers):
    '''
    Get number of hard conflicts\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}\n
    - teachers - {string: {'Materii': [string], 'Constrangeri': }} 
        - what teachers are there, what they teach and their preferences\n
    '''
    nr = 0
    i = __get_capacity_conflicts__(state)
    j = __get_overlap_conflicts__(state)
    k = __get_overh_conflicts__(state, teachers)
    nr += i
    nr += j
    nr += k
    return nr

def __get_sconflicts__(state, permissions):
    '''
    Get number of soft conflicts\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}\n
    - permissions - [(string, (int, int), string, string, string)] - [(day, interval, room, teacher, subject)] 
        - array with all possible moves to put in the timetable
    '''
    nr = 0
    i = __get__pref_conflicts__(state, permissions)
    nr += i
    return nr

def __get_all_conflicts__(state, teachers, permissions):
    '''
    Get number of all types of conflicts\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}\n
    - teachers - {string: {'Materii': [string], 'Constrangeri': }} 
        - what teachers are there, what they teach and their preferences\n
    - permissions - [(string, (int, int), string, string, string)] - [(day, interval, room, teacher, subject)] 
        - array with all possible moves to put in the timetable
    '''
    nr = 0
    i = __get_hconflicts__(state, teachers)
    j = __get_sconflicts__(state, permissions)
    nr += i
    nr += j
    return nr
# --------------------------------------------------------------------------------------
# algorithms part
# hill climbing
def __is_final__(state):
    '''
    For me, the final state is the one in which all students have where to stay\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}
    '''
    return __get_capacity_conflicts__(state) == 0

def __hill_climbing__(initial_state, teachers, permissions, max_iters, rooms, days, intervals, courses):
    '''
    Implements a hill climbing algorithm to optimize a schedule by reducing conflicts.\n
    Args:\n
    - initial_state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}}\n
    - courses - {string: int}, with subject and number of students enrolled in\n
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers\n
    - teachers - {string: {'Materii': [string], 'Constrangeri': }} 
        - what teachers are there, what they teach and their preferences\n
    - days - [string], with days \n
    - intervals - [(int, int)] with hour intervals \n
    - permissions - [(string, (int, int), string, string, string)] - [(day, interval, room, teacher, subject)] 
        - array with all possible moves to put in the timetable
    - max_iters - int - how many times to try to generate a new timetable from 0
    '''
    nr = 0
    current_state = deepcopy(initial_state)
    best_conflicts = __get_all_conflicts__(current_state, teachers, permissions)
    best_state = deepcopy(current_state)
    for _ in range(max_iters):
        current_conflicts = __get_all_conflicts__(current_state, teachers, permissions)
        okok = __get_available_actions__(current_state, teachers, rooms, days, intervals, courses, permissions)
        if okok == [] or okok is None:
            break
        index = randint(0, len(okok) - 1)
        action = okok[index]
        vecin = deepcopy(current_state)
        move = __apply_action__(action, vecin)
        nr += 1
        confl = __get_all_conflicts__(vecin, teachers, permissions)
        if current_conflicts < best_conflicts: 
            best_conflicts = current_conflicts
        else:
            best_state = deepcopy(vecin)
            best_conflicts = confl
            current_state = deepcopy(vecin)
    return best_state, nr

# --------------------------------------------------------------------------------------
# mcts
def __get_available_actions1__(state, profi, sali, zile, intervale, materii, permisiuni):
    ''' 
    Generates all possible actions from the lists of days, intervals, teachers
    in order to satisfact the constraints of days, intervals 
    and their own subjects with rooms for each subject for teachers
    Bullets 2, 5, 6 from hard constraints
    '''
    actions = []
    for day in zile:
        for hours in intervale:
            for room in sali:
                for t in profi:
                    for sub in materii:
                        if state[day][hours][room] == ():
                            if sub in profi[t]['Materii']: # proful preda materia aia
                                if sub in sali[room]['Materii']: # materia se face in sala aia
                                    if day in permisiuni[t]['days_ok']: # proful poate in ziua aia
                                        if hours in permisiuni[t]['good_intervals']: # proful poate preda in orele alea
                                            overlap = False
                                            for room2 in sali:
                                                if room2 != room:
                                                    if state[day][hours][room2] != () and len(state[day][hours][room2]) >= 1 and state[day][hours][room2][0] == t:
                                                        overlap = True
                                                        break
                                            if not overlap:
                                                dummy = (day, hours, room, t, sub)
                                                actions.append(dummy)
    return actions
                 
def __init_node__(state, parent):
    '''
    Initializes a new node for the Monte Carlo Tree Search algorithm.
    Args:
    - state: The state represented by the node.
    - parent: The parent node of the current node.
    Returns:
    - The initialized node.
    '''
    return {'N': 0, 'Q': 0, 'STATE': state, 'PARENT': parent, 'ACTIONS': {}}

def __select_action__(node, c, profi, sali, permisiuni):
    '''
    Implements a monte carlo tree search algorithm to optimize a schedule by reducing conflicts.\n
    Args:\n
    - opponent_s_action - - {string: {(int, int): {string: (string, string)}}} - next state
    - tree - a collection of nodes - {'N': number of iters, 'Q': quality/score, 'STATE': timetable/state(up), 'PARENT': parent node with previous state, 'ACTIONS': {nodes with next states}}\n
        - node['ACTIONS'] = {move: next node with next state after that move}\n
    - c - float - constant\n
    - state0 - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}}\n
    - courses - {string: int}, with subject and number of students enrolled in\n
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers\n
    - teachers - {string: {'Materii': [string], 'Constrangeri': }} 
        - what teachers are there, what they teach and their preferences\n
    - days - [string], with days \n
    - intervals - [(int, int)] with hour intervals \n
    - permissions - [(string, (int, int), string, string, string)] - [(day, interval, room, teacher, subject)] 
        - array with all possible moves to put in the timetable
    - buget - int - how many times to try to generate a new timetable from 0
    '''

    N_node = node['N']

    mutare_optima = None
    max_scor = float('-inf')
    mutare_optima = None

    for mutare, nod in node['ACTIONS'].items():
        if  node.get('N', 0) == 0: # asta da
            scor = float('inf')
        else:
            expandare = node.get('Q', 0) /  node.get('N', 0)
            explorare = c * sqrt(2 * log(N_node) /  node.get('N', 0))
            nconflicts = __get_all_conflicts__(nod['STATE'], profi, permisiuni) 
            scor = expandare + explorare + nconflicts
        if mutare_optima is None or scor < max_scor: 
            mutare_optima = mutare 
            max_scor = scor
    return mutare_optima

def __mcts__(state0, budget, tree, opponent_s_action, zile, intervale, sali, profi, materii, permisiuni, c):
    nr = 0
    if tree is not None and opponent_s_action in tree['ACTIONS']:
        tree = tree['ACTIONS'][opponent_s_action]
    else:
        tree = __init_node__(__init_state__(zile, intervale, sali), None)

    for _ in range(budget):
        node = tree
        state = deepcopy(state0)

        while not __is_final__(state):
            new_state = deepcopy(node['STATE'])
            posibilitati = __get_available_actions1__(new_state, profi, sali, zile, intervale, materii, permisiuni)
            if not all(mutare in node['ACTIONS'] for mutare in posibilitati):
                break
            mutare_noua = __select_action__(node, c, profi, sali, permisiuni)
            new_state = __apply_action__(mutare_noua, new_state)
            node['ACTIONS'][mutare_noua] = new_state
            node = node['ACTIONS'][mutare_noua]

        isok = __get_available_actions1__(new_state, profi, sali, zile, intervale, materii, permisiuni)
        if not __is_final__(new_state) and isok is not None: 
            index = randint(0, len(isok) - 1)
            alta_mutare_noua = isok[index]
            ceva = __apply_action__(alta_mutare_noua, new_state)
            node['ACTIONS'][alta_mutare_noua] = new_state
            node = node['ACTIONS'][alta_mutare_noua]
            
        while not __is_final__(new_state) and posibilitati != [] and posibilitati is not None:
            posibilitati = __get_available_actions1__(new_state, profi, sali, zile, intervale, materii, permisiuni)
            if posibilitati != [] and posibilitati is not None:
                indexx = randint(0, len(posibilitati) - 1)
                mutare = posibilitati[indexx]
                undeeee = __apply_action__(mutare, new_state)
                nr += 1

        while node:
            if node:
                node['N'] = node.get('N', 0) + 1
                if state0 == node.get('STATE', 0):
                    node['Q'] = node.get('Q', 0) + 1
                else:
                    node['Q'] = node.get('Q', 0) - 1
                    node = node.get('PARENT', 0)

    if tree:
        final_action = __select_action__(tree, c, profi, sali, permisiuni)
        return (final_action, tree['ACTIONS'][final_action], nr)

    return (0, __init_node__(state0, None), nr)

# --------------------------------------------------------------------------------------
# main
start_time = time.time()
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
                if sys.argv[1] == "all":
                    ok = 3
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
    courses = data['Materii']
    intervals1 = data['Intervale']
    teachers = data['Profesori']
    rooms = data['Sali']
    days = data['Zile']
    intervals = [eval(i) for i in intervals1]

    # we start with this
    test = __init_state__(days, intervals, rooms)

    # each teacher has preferances
    permissions = __get_teach_poate__(teachers)
    
    # constanta care reglează raportul între explorare și exploatare (CP = 0 -> doar exploatare)
    CP = 1.0 / sqrt(2.0)
    
    if ok == 1:
        # we populate the timetable with all arrangements
        orar, nr_stari = __hill_climbing__(test, teachers, permissions, sys.maxsize, rooms, days, intervals, courses)
        end_time1 = time.time()
        print(nr_stari)
        print(__get_all_conflicts__(orar, teachers, permissions))
        print(__how_many__(orar, courses, rooms))
        print(end_time1 - start_time)
        print("------------------------------------------------------------------------------------------------------")
        print(pretty_print_timetable(orar, filename))
    if ok == 2:
        cv, tree, nr_stari = __mcts__(test, 11, None, None, days, intervals, rooms, teachers, courses, permissions, CP)
        end_time2 = time.time()
        orar = {}
        if 'Luni' in tree:
            orar['Luni'] = tree['Luni']
        if 'Marti' in tree:
            orar['Marti'] = tree['Marti']
        if 'Miercuri' in tree:
            orar['Miercuri'] = tree['Miercuri']
        if 'Joi' in tree:
            orar['Joi'] = tree['Joi']
        if 'Vineri' in tree:
            orar['Vineri'] = tree['Vineri']
        print(nr_stari)
        print(__get_all_conflicts__(orar, teachers, permissions))
        print(__how_many__(orar, courses, rooms))
        print(end_time2 - start_time)
        print("------------------------------------------------------------------------------------------------------")
        print(pretty_print_timetable(orar, filename))
    if ok == 3:
        # we populate the timetable with all arrangements
        orar1, nr_stari1 = __hill_climbing__(test, teachers, permissions, sys.maxsize, rooms, days, intervals, courses)
        end_time21 = time.time()
        # print(nr_stari1)
        confl1 = __constr__(orar1, permissions, rooms, teachers, courses)
        # print(__get_all_conflicts__(orar1, teachers, permissions))
        print(__how_many__(orar1, courses, rooms))
        time1 = end_time21 - start_time
        print(confl1)
        # print("------------------------------------------------------------------------------------------------------")
        print(pretty_print_timetable(orar1, filename))
        print("------------------------------------------------------------------------------------------------------")
        cv1, tree1, nr_stari2 = __mcts__(test, 11, None, None, days, intervals, rooms, teachers, courses, permissions, CP)
        end_time22 = time.time()
        orar2 = {}
        if 'Luni' in tree1:
            orar2['Luni'] = tree1['Luni']
        if 'Marti' in tree1:
            orar2['Marti'] = tree1['Marti']
        if 'Miercuri' in tree1:
            orar2['Miercuri'] = tree1['Miercuri']
        if 'Joi' in tree1:
            orar2['Joi'] = tree1['Joi']
        if 'Vineri' in tree1:
            orar2['Vineri'] = tree1['Vineri']
        confl2 = __constr__(orar2, permissions, rooms, teachers, courses)
        print(__how_many__(orar2, courses, rooms))
        print(confl2)
        time2 = end_time22 - start_time
        # print("------------------------------------------------------------------------------------------------------")
        print(pretty_print_timetable(orar2, filename))
        
        # Grafic timp de executie
        plt.bar(["HC", "MCTS"], [time1, time2])
        plt.xlabel('Algoritm')
        plt.ylabel('Timp')
        plt.title('Comparatie timp')
        plt.savefig('timp.png')
        plt.close()
        
        # Grafic constrangeri
        plt.bar(["HC", "MCTS"], [confl1, confl2])
        plt.xlabel('Algoritm')
        plt.ylabel('Numar conflicte')
        plt.title('Comparatie conflicte')
        plt.savefig('confl.png')
        plt.close()
        
        # Grafic numar stari
        plt.bar(["HC", "MCTS"], [nr_stari1, nr_stari2])
        plt.xlabel('Algoritm')
        plt.ylabel('Numar stari')
        plt.title('Comparatie numar stari')
        plt.savefig('stari.png')
        plt.close()