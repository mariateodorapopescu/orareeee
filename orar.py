from __future__ import annotations
import sys
import yaml
from copy import deepcopy
from utils import pretty_print_timetable
from random import shuffle, seed, randint
import random
from math import sqrt, log
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

def __get_aviable_actions__(state, profi, sali, zile, intervale, materii, poate):
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
                                                        overlap = True # verific sa nu fie aceeasi persoana in doua locuri diferite in acelasi timp
                                                        break
                                            if not overlap and not overh:
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

def __get_capacity_conflicts__(board):
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
    for zi in board:
        for ore in board[zi]:
            for sala in board[zi][ore]:
                if len(board[zi][ore][sala]) >= 1:
                    vector_caracteristic[board[zi][ore][sala][1]] += sali[sala]['Capacitate']
    for i in vector_caracteristic:
        if vector_caracteristic[i] < courses[i]:
            nr += 1
    return nr

def __get_overlap_conflicts__(board):
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
# the timetable generator part
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
def __is_final__(state):
    '''
    For me, the final state is the one in which all students have where to stay\n
    Args:\n
    - state - {string: {(int, int): {string: (string, string)}}} with the timetable with 
        {day: {(start, end): {room: (teacher, course)}}}
    '''
    return __get_capacity_conflicts__(state) == 0
    
def hill_climbing(initial_state, actions, profi, permisiuni, cobai, max_iters):
    '''
    A modified version from the HC laboratory
    '''
    current_state = deepcopy(initial_state)
    best_conflicts = __get_all_conflicts__(current_state, profi, permisiuni)
    best_state = deepcopy(current_state)
    for _ in range(max_iters):
        current_conflicts = __get_all_conflicts__(current_state, profi, permisiuni)
        okok = get_aviable_actions(current_state, actions, cobai)
        if okok == []:
            break
        index = randint(0, len(okok) - 1)
        action = okok[index]
        vecin = deepcopy(current_state)
        move = __aply_move__(action, vecin)
        confl = __get_all_conflicts__(vecin, profi, permisiuni)
        if current_conflicts < best_conflicts:
            best_conflicts = current_conflicts
        else:
            # __undo_move__(current_state, action)
            best_state = deepcopy(vecin)
            best_conflicts = confl
            current_state = deepcopy(vecin)
    return best_state

def hill_climbing1(initial_state, profi, permisiuni, max_iters, sali, zile, intervale, materii):
    '''
    A modified version from the HC laboratory
    '''
    current_state = deepcopy(initial_state)
    best_conflicts = __get_all_conflicts__(current_state, profi, permisiuni)
    best_state = deepcopy(current_state)
    for _ in range(max_iters):
        current_conflicts = __get_all_conflicts__(current_state, profi, permisiuni)
        okok = __get_aviable_actions__(current_state, profi, sali, zile, intervale, materii, permisiuni)
        if okok == []:
            break
        index = randint(0, len(okok) - 1)
        action = okok[index]
        vecin = deepcopy(current_state)
        move = __aply_move__(action, vecin)
        # if is_valid
        confl = __get_all_conflicts__(vecin, profi, permisiuni)
        if current_conflicts < best_conflicts: 
            best_conflicts = current_conflicts
        else:
            # __undo_move__(current_state, action)
            best_state = deepcopy(vecin)
            best_conflicts = confl
            current_state = deepcopy(vecin)
    return best_state
# --------------------------------------------------------------------------------------
# mcts
def print_tree(tree, indent = 0):
    if not tree:
        return
    tab = "".join(" " * indent)
    print("%sN = %d, Q = %f" % (tab, tree[N], tree[Q]))
    for a in tree[ACTIONS]:
        print("%s %d ==> " % (tab, a))
        print_tree(tree[ACTIONS][a], indent + 3)
                 
def init_node(state, parent = None):
    '''
    I do not use classes, ok? So, the node and the tree ar as they are in the laboratory, 
    the tree is a dictonary with the state being the timetable aka 
    {day:{hours:{room: (teacher, subject)}}} and parent a timetable 
    from where STATE was generated / previous state aka the old version before 
    a move was made and with that move the timetable is the one I have right now.
    Actions is as it is in the lab state -> next-state
    '''
    return {'N': 0, 'Q': 0, 'STATE': state, 'PARENT': parent, 'ACTIONS': {}}

def select_action(node, c, profi, permisiuni):
    '''
    Takes an action aka (day, hour, room, teacher, subject) from the actions dictionary
    node[ACTIONS] = {{zi: {ora: {sala: (prof, materie)}}}: {zi: {ora: {sala: (prof, materie)}}}} - old lab
    new version -> orar : mutare optima ptr copil --> NUUU
    '''
    N_node = node[N]
    
    mutare_optima = None
    max_scor = float('-inf')
    mutare_optima = None

    for mutare, nod in node['ACTIONS'].items():
        if  node.get('N', 0) == 0: # asta da
            scor = float('inf')
        else:
            expandare = nod[Q] / nod[N] # ok
            explorare = c * sqrt(2 * log(N_node) / nod[N]) # okkk
            nconflicts = __get_all_conflicts__(nod[STATE], profi, permisiuni) # o sa pun in calcul si constraint-uri
            scor = expandare + explorare + nconflicts # oook
        if mutare_optima is None or scor < max_scor:
            mutare_optima = mutare # asta nu stiu de unde sa o iau, hai sa vedem
            max_scor = scor # la mine max scor e min scor
    return mutare_optima

def mcts(state0, budget, tree, opponent_s_action = None):
    '''
    Algoritmul MCTS (UCT)
    state0 - tabelul pentru care trebuie aleasă o acțiune/mutare/tuplu
    budget - numărul de iterații permis -> 10000 mainly, dat in main
    tree - un arbore din explorările anterioare, dacă există
    opponent_s_action - n-am mai modificat denumirea din lab, 
    dar asta e starea/tabelul precedent dacă există
    opponent_action = ORAR_VECHI, STARE_ANTERIOARA
    '''
    # DACĂ există un arbore construit anterior ȘI
    #   acesta are un copil ce corespunde starii anetrioare,
    # ATUNCI acel copil va deveni nodul de început pentru algoritm.
    # ALTFEL, arborele de start este un nod gol.
    
    if tree is not None and opponent_s_action in tree[ACTIONS]:
        tree = tree[ACTIONS][opponent_s_action]
    else:
        tree = init_node(init_state())
    # tree = None # TODO
    
    #---------------------------------------------------------------

    for x in range(budget):
        # Pornim procesul de selecție din nodul rădăcină / starea inițială
        node = tree
        state = state0
        # TODO <4>
        # Coborâm în arbore până când ajungem la o stare finală
        # sau la un nod cu acțiuni neexplorate.
        while not is_final(state):
            posibilitati = get_available_actions(state)
            if not all(mutare in node[ACTIONS] for mutare in posibilitati):
                break
            mutare_noua = select_action(node)
            node = node[ACTIONS][mutare_noua]
            state = apply_action(state, mutare_noua)
        
        #---------------------------------------------------------------
        
        # TODO <5>
        # Dacă am ajuns într-un nod care nu este final și din care nu s-au
        # `încercat` toate acțiunile, construim un nod nou.
        isok = get_available_actions(state)
        if not is_final(state) and isok is not None: 
            # alea de mai de sus se recicleaza pentrua  putea trece mai departe
            alta_mutare_noua = choice(isok) # se recicleaza ca merge pana la 2 nivele in arb
            state = apply_action(state, alta_mutare_noua)
            nod_nou = init_node(state, node)
            # acum trece mai departe
            if nod_nou is not None:
                node[ACTIONS][alta_mutare_noua] = nod_nou
                # aici se fac legaturile, ca sa se treaca mai departe
                nod_nou[PARENT] = node # pune head-ul current ca parinte
                # e gen ca si cum ai adauga un nod nod intr-o liste, ca la liste inlantuite
        
        #---------------------------------------------------------------
        
        # TODO <6>
        # Se simulează o desfășurare a jocului până la ajungerea într-o
        # starea finală. Se evaluează recompensa în acea stare.
        # state = state0 # de înlocuit cu node[STATE]
        while not is_final(state):
            posibilitati = get_available_actions(state)
            mutare = choice(posibilitati)
            state = apply_action(state, mutare)
            # break
        
        winner = is_final(state)
        if winner == state0[NEXT_PLAYER]:
            reward = 1
        elif winner == (3 - state0[NEXT_PLAYER]):
            reward = 0.0
        elif winner == 3:
            reward = 0.25
        else:
            reward = 0.5
        #---------------------------------------------------------------

        # TODO <7>
        # Se actualizează toate nodurile de la node către rădăcină:
        #  - se incrementează valoarea N din fiecare nod
        #  - pentru nodurile corespunzătoare acestui jucător, se adună recompensa la valoarea Q
        #  - pentru nodurile celelalte, valoarea Q se adună 1 cu minus recompensa
        while node:
            node[N] = node[N] + 1
            if state0[NEXT_PLAYER] == node[STATE][NEXT_PLAYER]:         
                node[Q] = node[Q] + reward
            else:
                node[Q] = node[Q] + (1 - reward)
            node = node[PARENT]
        #---------------------------------------------------------------

    if tree:
        final_action = select_action(tree, 0.0)
        return (final_action, tree[ACTIONS][final_action])
    # Acest cod este aici doar ca să nu dea erori testele mai jos; în mod normal tree nu trebuie să fie None
    if get_available_actions(state0):
        return (get_available_actions(state0)[0], init_node())
    return (0, init_node(state0))

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
    permisiuni = __get_teach_poate__(profi)

    longer = __generate_actions1__(profi, sali, zile, intervale)

    # array with (day, interval, room, teacher, course) tuples
    longer2 = __generate_actions123__(profi, sali, zile, intervale)
    
    N = 'N'
    Q = 'Q'
    STATE = 'STATE'
    PARENT = 'PARENT'
    ACTIONS = 'ACTIONS'
    
    # constanta care reglează raportul între explorare și exploatare (CP = 0 -> doar exploatare)
    CP = 1.0 / sqrt(2.0)
    
    if ok == 1:
        # we populate the timetable with all arrangements
        __populate_cobai2__(cobai, longer2)
        # state = hill_climbing(test, longer2, profi, permisiuni, cobai, sys.maxsize)
        state = hill_climbing1(test, profi, permisiuni, sys.maxsize,sali, zile, intervale, materii)
        print(pretty_print_timetable(state, filename))
    # if ok == 2:
        