from __future__ import annotations
import sys
import yaml
from copy import deepcopy
from utils import pretty_print_timetable
from random import randint
from math import sqrt, log, ceil
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

def get_nr_hours(state, prof):
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

def get_min_subject(courses):
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

def get_max_subject(courses):
    '''
    Finds the subject with the maximum number of students enrolled in\n
    Args:\n
    - courses - {string: int}, with subject and number of students enrolled in
    '''
    mini = 0
    minii = None
    for subject in courses:
        if mini < courses[subject]:
            mini = courses[subject]
            minii = subject
    return minii

def get_total_students(courses, min_subject):
    '''
    Finds the total number of students enrolled in all subjects\n
    Args:\n
    - courses - {string: int}, with subject and number of students enrolled in\n
    - min_subject - string
    '''
    total_students = 0
    for subject, nr_stud in courses.items():
        if subject == min_subject:
            total_students += nr_stud
    return total_students

def how_many(state, courses, rooms):
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
def gata(state, subject, rooms, courses):
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

def donee(state, prof):
    '''
    Checks whether a teacher has their norm of 14h\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}} \n
    - prof - string
    '''
    return get_nr_hours(state, prof) < 7

def acoperit_minim(state, courses, rooms):
    '''
    Checks whether the subject with the least students enrolled in has all the students enrolled in\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}}
    - courses - {string: int}, with subject and number of students enrolled in
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers
    '''
    subject = get_min_subject(courses)
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

def all_subjects_fulfilled(state, courses, rooms):
    '''
    Checks whether all subjects have all the students enrolled in\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}}
    - courses - {string: int}, with subject and number of students enrolled in
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers
    '''
    total_students = {subject: 0 for subject in courses}
    for day in state:
        for hours in state[day]:
            for room in state[day][hours]:
                if state[day][hours][room] is not None and state[day][hours][room] != () and len(state[day][hours][room]) >= 2:
                    subject = state[day][hours][room][1]
                    total_students[subject] += rooms[room]['Capacitate']
    for subject, required_students in courses.items():
        if total_students[subject] < required_students:
            return False
    return True
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
                    if donee(state, t):  
                        for subject in courses:
                            if state[day][hours][room] == ():
                                if subject in teachers[t]['Materii']:  
                                    if subject in rooms[room]['Materii']:  
                                        if day in permissions[t]['days_ok']:  
                                            if hours in permissions[t]['good_intervals']:  
                                                if not gata(state, subject, rooms, courses):  
                                                    if not acoperit_minim(state, courses, rooms): 
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

def __aply_move__(action, state):
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
def is_final(state):
    '''
    For me, the final state is the one in which all students have where to stay\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}
    '''
    return __get_capacity_conflicts__(state) == 0

def hill_climbing(initial_state, teachers, permissions, max_iters, rooms, days, intervals, courses):
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
        move = __aply_move__(action, vecin)
        confl = __get_all_conflicts__(vecin, teachers, permissions)
        if current_conflicts < best_conflicts: 
            best_conflicts = current_conflicts
        else:
            best_state = deepcopy(vecin)
            best_conflicts = confl
            current_state = deepcopy(vecin)
    return best_state

# --------------------------------------------------------------------------------------
# mcts           
def init_node(state, parent):
    '''
    Initializes a new node for the Monte Carlo Tree Search algorithm.\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
    {day: {(start, end): {room: (teacher, course)}}}\n
    - node {'N': number of iters, 'Q': quality/score, 'STATE': timetable/state(up), 'PARENT': parent node with previous state, 'ACTIONS': {nodes with next states}}\n
        - node['ACTIONS'] = {move: next node with next state after that move}
    '''
    return {'N': 0, 'Q': 0, 'STATE': state, 'PARENT': parent, 'ACTIONS': {}}

def select_action(node, c, teachers, rooms, permissions):
    '''
    Selects the best move to put in the timetable -> taken from the laboratory\n
    Args:\n
    - node {'N': number of iters, 'Q': quality/score, 'STATE': timetable/state(up), 'PARENT': parent node with previous state, 'ACTIONS': {nodes with next states}}\n
        - node['ACTIONS'] = {move: next node with next state after that move}\n
    - c - float - constant\n
    - rooms - {string:{'Materii': , 'Capacitate': }} with room names and numbers\n
    - teachers - {string: {'Materii': [string], 'Constrangeri': }} 
        - what teachers are there, what they teach and their preferences\n
    - permissions - [(string, (int, int), string, string, string)] - [(day, interval, room, teacher, subject)] 
        - array with all possible moves to put in the timetable
    '''
    N_node = node['N']
    mutare_optima = None
    max_scor = float('-inf')
    mutare_optima = None
    for mutare, nod in node['ACTIONS'].items():
        if  node.get('N', 0) == 0:
            scor = float('inf')
        else:
            expandare = node.get('Q', 0) /  node.get('N', 0)
            explorare = c * sqrt(2 * log(N_node) /  node.get('N', 0))
            nconflicts = __get_all_conflicts__(nod['STATE'], teachers, permissions) 
            scor = expandare + explorare + nconflicts
        if mutare_optima is None or scor < max_scor: 
            mutare_optima = mutare
            max_scor = scor
    return mutare_optima

def mcts(state0, budget, tree, opponent_s_action, days, intervals, rooms, teachers, courses, permissions, c):
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
    if tree is not None and opponent_s_action in tree['ACTIONS']:
        tree = tree['ACTIONS'][opponent_s_action]
    else:
        tree = init_node(__init_state__(days, intervals, rooms), None)
    for _ in range(budget):
        node = tree
        state = deepcopy(state0)
        while not is_final(state):
            new_state = deepcopy(node['STATE'])
            posibilitati = __get_available_actions__(new_state, teachers, rooms, days, intervals, courses, permissions)
            if not all(mutare in node['ACTIONS'] for mutare in posibilitati):
                break
            mutare_noua = select_action(node, c, teachers, rooms, permissions)
            new_state = __aply_move__(mutare_noua, new_state)
            node['ACTIONS'][mutare_noua] = new_state
            node = node['ACTIONS'][mutare_noua]
        isok = __get_available_actions__(new_state, teachers, rooms, days, intervals, courses, permissions)
        if not is_final(new_state) and isok is not None: 
            index = randint(0, len(isok) - 1)
            alta_mutare_noua = isok[index]
            ceva = __aply_move__(alta_mutare_noua, new_state)
            node['ACTIONS'][alta_mutare_noua] = new_state
            node = node['ACTIONS'][alta_mutare_noua]
        while not is_final(new_state) and posibilitati != [] and posibilitati is not None:
            posibilitati = __get_available_actions__(new_state, teachers, rooms, days, intervals, courses, permissions)
            if posibilitati != [] and posibilitati is not None:
                indexx = randint(0, len(posibilitati) - 1)
                mutare = posibilitati[indexx]
                undeeee = __aply_move__(mutare, new_state)
        while node:
            if node:
                node['N'] = node.get('N', 0) + 1
                if state0 == node.get('STATE', 0):
                    node['Q'] = node.get('Q', 0) + 1
                else:
                    node['Q'] = node.get('Q', 0) - 1
                    node = node.get('PARENT', 0)
    if tree:
        final_action = select_action(tree, c, teachers, rooms, permissions)
        return (final_action, tree['ACTIONS'][final_action])

    return (0, init_node(state0, None))
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
        orar = hill_climbing(test, teachers, permissions, sys.maxsize, rooms, days, intervals, courses)
        print(how_many(orar, courses, rooms))
        print("------------------------------------------------------------------------------------------------------")
        print(pretty_print_timetable(orar, filename))
    if ok == 2:
        cv, tree = mcts(test, 11, None, None, days, intervals, rooms, teachers, courses, permissions, CP)
        # if tree: print(enumerate(tree.values())[0])
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
        print(how_many(orar, courses, rooms))
        print("------------------------------------------------------------------------------------------------------")
        print(pretty_print_timetable(orar, filename))