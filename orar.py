from __future__ import annotations
import sys
import yaml
from typing import Callable
from copy import copy
from copy import deepcopy
from functools import reduce
import numpy as np
from utils import pretty_print_timetable
from random import choice, shuffle, seed, randint
import random
from math import sqrt, log
# imports
# --------------------------------------------------------------------------------------
# initialize things
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
# getters
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
# --------------------------------------------------------------------------------------
# generators of parts for timetable generator
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

def __generate_actions123__(profi, sali, zile, intervale):
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
    return actions

def __get__teach__number__(state, t):
    nr = 0
    for day in state:
        for hours in state[day]:
            for room in state[day][hours]:
                if state[day][hours][room] != () and len(state[day][hours][room]) >= 1:
                    if state[day][hours][room][0] == t:
                        nr += 1
    return nr

def __get_aviable_actions__(state, profi, sali, zile, intervale, materii, poate):
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
                    overh = False
                    nr = __get__teach__number__(state, t)
                    if nr > 7: # daca prof are mai mult de 7 intervale in orar
                        overh = True
                    for sub in materii:
                        if state[day][hours][room] == ():
                            if sub in profi[t]['Materii']: # proful preda materia aia
                                if sub in sali[room]['Materii']: # materia se face in sala aia
                                    if day in permisiuni[t]['zile_ok']: # proful poate in ziua aia
                                        if hours in permisiuni[t]['ore_ok']: # proful poate preda in orele alea
                                            overlap = False
                                            for room2 in sali:
                                                if room2 != room:
                                                    if state[day][hours][room2] != () and len(state[day][hours][room2]) >= 1 and state[day][hours][room2][0] == t:
                                                        overlap = True
                                                        break
                                            if not overlap and not overh:
                                                dummy = (day, hours, room, t, sub)
                                                actions.append(dummy)
    return actions

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
# --------------------------------------------------------------------------------------
# conflicts
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

# def __get_capacity_conflicts__(board):
#     '''
#     Checks whether all students have a seat in the rooms
#     Bullet 4 from hard constraints
#     '''
#     nr = 0
#     vector_caracteristic = {}
#     for i in materii:
#         vector_caracteristic[i] = 0
#     if board is not None and board[zi] is not None:
#         for zi in board:
#             for ore in board[zi]:
#                 for sala in board[zi][ore]:
#                     if len(board[zi][ore][sala]) >= 1:
#                         vector_caracteristic[board[zi][ore][sala][1]] += sali[sala]['Capacitate']
#     for i in vector_caracteristic:
#         if vector_caracteristic[i] < materii[i]:
#             nr += 1
#     return nr

def __get_capacity_conflicts__(board):
    '''
    Checks whether all students have a seat in the rooms
    Bullet 4 from hard constraints
    '''
    nr = 0
    vector_caracteristic = {}
    for i in materii:
        vector_caracteristic[i] = 0
    if board is not None:
        for zi in board:  # Move this loop up
            if board[zi] is not None:  # Now 'zi' is defined
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
    i = __get_hconflicts__(board, profi)
    j = __get_sconflicts__(board, permisiuni)
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
    if sched is not None and action[0] in sched and sched[action[0]] is not None and action[1] in sched[action[0]] and sched[action[0]][action[1]] is not None and action[2] in sched[action[0]][action[1]] and sched[action[0]][action[1]][action[2]] is not None:
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

# --------------------------------------------------------------------------------------
# algorithms part
# hill climbing
def is_final(state):
    '''
    For me, the final state is the one in which all students have where to stay
    '''
    return __get_capacity_conflicts__(state) == 0

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
        confl = __get_all_conflicts__(vecin, profi, permisiuni)
        if current_conflicts < best_conflicts: 
            best_conflicts = current_conflicts
        else:
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
        # ??? probabil o sa scap de ea, vedem
                 
def init_node(state, parent):
    '''
    I do not use classes, ok? So, the node and the tree ar as they are in the laboratory, 
    the tree is a dictonary with the state being the timetable aka 
    {day:{hours:{room: (teacher, subject)}}} and parent a timetable 
    from where STATE was generated / previous state aka the old version before 
    a move was made and with that move the timetable is the one I have right now.
    Actions is as it is in the lab state -> next-state
    '''
    return {N: 0, Q: 0, STATE: state, PARENT: parent, ACTIONS: {}}
    #  asta e gen nodul radacina

def select_action(node, c, profi, sali, permisiuni):
    '''
    Selectează acțiunea optimă dintr-un nod folosind algoritmul UCT.
    Args:
    - node: Nodul pentru care se face selecția acțiunii.
    - c: Parametrul de exploatare/exploare pentru algoritmul UCT.
    - profi: Dicționarul cu informații despre profesori.
    - sali: Dicționarul cu informații despre săli.
    - permisiuni: Dicționarul cu permisiuni pentru ore și zile pentru fiecare profesor.
    Returns:
    - Mutarea optimă (zi, interval, sală, profesor, materie).
    ------------------------------------------------------------------------------------
    A, gata. node[ACTIONS] e un dictionar in care e pusa o mutare 
    si gen urmatoarea chestie e un nod cu orarul rezultat cu mutarea aia 
    (desi mai simplu era daca era numai un nou orar si atat -> e si aai o varianta)
    '''

    N_node = node[N]

    mutare_optima = None
    max_scor = float('-inf')
    mutare_optima = None

    for mutare, nod in node[ACTIONS].items():
        if nod[N] == 0: # asta da
            scor = float('inf')
        else:
            expandare = nod[Q] / nod[N] # ok, 
            # ia gen nodul curent, state ul curent din nodul dat ca parametru 
            # si face calcule pe el
            explorare = c * sqrt(2 * log(N_node) / nod[N]) # okkk
            nconflicts = __get_all_conflicts__(nod[STATE], profi, permisiuni) 
            # o sa pun in calcul si constraint-uri
            scor = expandare + explorare + nconflicts # oook
        if mutare_optima is None or scor < max_scor: 
            # la mine e pe dos, scorul este numarul de toate tipurile
            # de conflicte si prin urmare cu cat sunt mai putine conflicte, 
            # cu atat scorul e mai bun, orarul e mai bun, este un fel de logica negativa
            mutare_optima = mutare # asta nu stiu de unde sa o iau, hai sa vedem 
            # -> mutarea ar trebui sa fie un tuplu, sau unde s-a pus un tuplu (prof, materie)
            max_scor = scor # la mine max scor e min scor
    return mutare_optima

def mcts(state0, budget, tree, opponent_s_action, zile, intervale, sali, profi, materii, permisiuni, c):
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
    #   acesta are un copil ce corespunde starii anterioare,
    # ATUNCI acel copil va deveni nodul de început pentru algoritm.
    # ALTFEL, arborele de start este un nod gol.
    
    if tree is not None and opponent_s_action in tree[ACTIONS]:
        tree = tree[ACTIONS][opponent_s_action]
    else:
        tree = init_node(__init_state__(zile, intervale, sali), None) # asta se lasa asa ca e algoritmul de generare in sine, 
        # chestia ce se modifica cred ca are loc mai sus, la select action

    #---------------------------------------------------------------
       
    for _ in range(budget):
        # Pornim procesul de selecție din nodul rădăcină / starea inițială
        # buget vine un fel de max_iter din hill_climbing
        node = tree
        state = state0
        # TODO <4>
        # Coborâm în arbore până când ajungem la o stare finală
        # sau la un nod cu acțiuni neexplorate.

        while not is_final(state):
            posibilitati = __get_aviable_actions__(state, profi, sali, zile, intervale, materii, permisiuni)
            if not all(mutare in node[ACTIONS] for mutare in posibilitati):
                break
            mutare_noua = select_action(node, c, profi, sali, permisiuni)
            node = node[ACTIONS][mutare_noua]
            unde = __aply_move__(mutare_noua, state)

        #---------------------------------------------------------------

        # TODO <5>
        # Dacă am ajuns într-un nod care nu este final și din care nu s-au
        # `încercat` toate acțiunile, construim un nod nou.
        isok = __get_aviable_actions__(state, profi, sali, zile, intervale, materii, permisiuni)
        if not is_final(state) and isok is not None: 
            # alea de mai de sus se recicleaza pentru a  putea trece mai departe
            alta_mutare_noua = choice(isok) # se recicleaza ca merge pana la 2 nivele in arb
            undee = __aply_move__(alta_mutare_noua, state)
            mutare_nouaa = select_action(node, c, profi, sali, permisiuni)
            nodd = node[ACTIONS].get(mutare_nouaa)
            if state is not None and mutare_nouaa is not None:
                undeee = __aply_move__(mutare_nouaa, state)
                # aici se fac legaturile, ca sa se treaca mai departe
                # nod_nou[PARENT] = node # pune head-ul current ca parinte
                # dar asta cu node[PARENT] am facut-o deja
                # e gen ca si cum ai adauga un nod nod intr-o liste, ca la liste inlantuite

        #---------------------------------------------------------------

        # TODO <6>
        # Se simulează o desfășurare a jocului până la ajungerea într-o
        # starea finală. Se evaluează recompensa în acea stare.
        # state = state0 # de înlocuit cu node[STATE]
        while not is_final(state):
            posibilitati = __get_aviable_actions__(state, profi, sali, zile, intervale, materii, permisiuni)
            mutare = choice(posibilitati) # asta e un rand index
            state = __aply_move__(mutare, state)
            # break

        #---------------------------------------------------------------

        # TODO <7>
        # Se actualizează toate nodurile de la node către rădăcină:
        #  - se incrementează valoarea N din fiecare nod
        #  - pentru nodurile corespunzătoare acestui jucător, se adună recompensa la valoarea Q
        #  - pentru nodurile celelalte, valoarea Q se adună 1 cu minus recompensa
        while node:
            node[N] += 1
            if state0 == node[STATE]:         
                node[Q] = node[Q] + __get_capacity_conflicts__(node[STATE])
            else:
                node[Q] += (1 -  __get_capacity_conflicts__(node[STATE]))
            node = node[PARENT]
        #---------------------------------------------------------------

    if tree:
        final_action = select_action(tree, 0.0, profi, sali, permisiuni)
        return (final_action, tree[ACTIONS][final_action])
    # Acest cod este aici doar ca să nu dea erori testele mai jos; în mod normal tree nu trebuie să fie None
    if __get_aviable_actions__(state0, profi, sali, zile, intervale, materii, permisiuni):
        return (__get_aviable_actions__(state0, profi, sali, zile, intervale, materii, permisiuni)[0], init_node())
    
    return (0, init_node(state0))

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
    if ok == 2:
        (action, tree) = mcts(test, 11, None, None, zile, intervale, sali, profi, materii, permisiuni, CP)
        print(action)
        if tree: print_tree(tree[PARENT])