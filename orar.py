import yaml

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

# test to see if parsed correctly
# print(intervale)
# print("capacitati sali: " + str(materii.values()))
# print(profi['Andreea Dinu']['Constrangeri'])
# print(sali['EG324']['Capacitate'])
# print(zile)

# now I need to define a state
# a state is the timetable itself, which is a 2d-multi-d array, 
# with day interval and each 'cell' is a dict of tuples pairs like room and tuple teacher - subject
# something like this orar['day']['interval'] = {'room': ('teacher', 'subject')}

# acum am luat labul de MCTS si il modific =P

HEIGHT, WIDTH = len(intervale), len(zile)
TIMETABLE, NEXT_VERSION = 0, 1
# initialize state
def __init_state__():
    state = {}
    state[TIMETABLE] = {}
    for ziua in zile:
        state[TIMETABLE][ziua] = {}
        for interval in intervale:
            state[TIMETABLE][ziua][interval] = {'room': None, 'teacher': None, 'subject': None}
    return state

# print initial state
def __print_state__(state, TIMETABLE):
    print(state[TIMETABLE])
    
state = __init_state__()
# __print_state__(state, TIMETABLE)

def __generate_actions__(materii, intervale, profi, sali, zile):
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
        nume = None
        nume = ''.join(char for char in i if char.isupper())
        for j in materii_prof:
            for k in ore_ok:
                for l in zile_ok:
                    for m in sali:
                        if j in sali[m]['Materii']:
                            for n in materii:
                                dummy = (l, k, j, m, nume)
                                actions.append(dummy)
    good_actions = sorted(list(set(actions)), key=lambda x: (x[0], x[1], x[2]))
    return good_actions
                    
actions = __generate_actions__(materii, intervale, profi, sali, zile)
# now I generated all possibilities, but the rooms and students are not well put together
# print(actions)

def __possible_arranjaments__(actions, WIDTH, HEIGHT):
    possibilities = [[[] for _ in range(WIDTH)] for _ in range(HEIGHT)]
    for i in actions:
        col, lin = 0, 0
        if i[0] == 'Luni':
            col = 0
        elif i[0] == 'Marti':
            col = 1
        elif i[0] == 'Miercuri':
            col = 2
        elif i[0] == 'Joi':
            col = 3
        else:
            col = 4

        if i[1] == '08-10':
            lin = 0
        elif i[1] == '10-12':
            lin = 1
        elif i[1] == '12-14':
            lin = 2
        elif i[1] == '14-16':
            lin = 3
        elif i[1] == '16-18':
            lin = 4
        else:
            lin = 5

        dummy = (i[2], i[4], i[3])
        possibilities[lin][col].append(dummy)
    return possibilities
        
possibilities = __possible_arranjaments__(actions, WIDTH, HEIGHT)

def __get_overlaps__(possibilities, sali):
    overlaps = []
    for index_i, i in enumerate(possibilities):
        # ia pe zile
        for index_j, j in enumerate(possibilities[index_i]):
            for l in sali:
                nr = 0
                for k in j:
                    if l in k:
                        nr += 1
                if nr >= 2:
                    dummy = (l, index_j, index_i)
                    overlaps.append(dummy)
    return overlaps

overlaps = __get_overlaps__(possibilities, sali, WIDTH, HEIGHT)

def __get_aviable_actions__(possibilities, overlaps):
    orarele = [[[[] for _ in range(WIDTH)] for _ in range(HEIGHT)] for _ in range(100)]
    return orarele

from copy import deepcopy
from functools import reduce

# Funcție ce întoarce starea în care se ajunge prin aplicarea unei acțiuni
def __apply_action__(state, action, where):
    # acum sa vedem cam ce inseamna o actiune
    # o actiune poate fi pui materia cutare cu proful cutare la ora cutare in ziua cutare
    # deci, action e (materie, prof), where e celula din tabel, adica zi si interval orar
    # sala cred ca se va pune dupa
    # if-ul cu action e destul de dubios, trebuie modificat
    if action >= len(state[TIMETABLE]) or 0 not in state[TIMETABLE][action]:
        print("Action " + str(action) + " is not valid.")
        return None
    new_timetable = deepcopy(state[TIMETABLE])
    new_timetable[action][new_timetable[action].index(0,0)] = state[NEXT_VERSION]
    return (new_timetable, 3 - state[NEXT_VERSION])

# Funcție ce verifică dacă o stare este finală
# def is_final(state):
#     # Verificăm dacă matricea este plină
#     if not any([0 in col for col in state[BOARD]]): return 3
#     # Jucătorul care doar ce a mutat ar putea să fie câștigător
#     player = 3 - state[NEXT_PLAYER]
    
#     ok = lambda pos: all([state[BOARD][c][r] == player for (r, c) in pos])
#     # Verificăm verticale
#     for row in range(HEIGHT):
#         for col in range(WIDTH - 4):
#             if ok([(row, col + i) for i in range(4)]): return player
#     # Verificăm orizontale
#     for col in range(WIDTH):
#         for row in range(HEIGHT-4):
#             if ok([(row + i, col) for i in range(4)]): return player
#     # Verificăm diagonale
#     for col in range(WIDTH-4):
#         for row in range(HEIGHT-4):
#             if ok([(row + i, col+i) for i in range(4)]): return player
#     for col in range(WIDTH-4):
#         for row in range(HEIGHT-4):
#             if ok([(row + i, col+4-i) for i in range(4)]): return player
#     return False
# # Ajungem la o stare finală oarecare și o afișăm.
# from random import choice

# rand_state = init_state()
# print(rand_state)
# while not is_final(rand_state):
#     actions = get_available_actions(rand_state)
#     if not actions:
#         break
#     action = choice(get_available_actions(rand_state))
#     rand_state = apply_action(rand_state, action)

# print_state(rand_state)
# print("Învingător: %s" % (name[is_final(rand_state)]))
# # Exemplu: Se afișează starea obținută prin aplicarea unor acțiuni
# all_actions = [1, 2, 1, 3, 1, 4, 2, 5]
# some_state = reduce(apply_action, all_actions, init_state())
# print_state(some_state)
# print("Învingător: %s" % (name[is_final(some_state)]))

# # Constante

# N = 'N'
# Q = 'Q'
# STATE = 'state'
# PARENT = 'parent'
# ACTIONS = 'actions'

# def print_tree(tree, indent = 0):
#     if not tree:
#         return
#     tab = "".join(" " * indent)
#     print("%sN = %d, Q = %f" % (tab, tree[N], tree[Q]))
#     for a in tree[ACTIONS]:
#         print("%s %d ==> " % (tab, a))
#         print_tree(tree[ACTIONS][a], indent + 3)
        
# # Funcție ce întoarce un nod nou,
# # eventual copilul unui nod dat ca argument
# def init_node(state, parent = None):
#     return {N: 0, Q: 0, STATE: state, PARENT: parent, ACTIONS: {}}

# from math import sqrt, log

# # constanta care reglează raportul între explorare și exploatare (CP = 0 -> doar exploatare)
# CP = 1.0 / sqrt(2.0)

# # Funcție ce alege o acțiune dintr-un nod
# def select_action(node, c = CP):
#     N_node = node[N]
    
#     mutare_optima = None
#     max_scor = float('-inf')

#     for mutare, nod in node[ACTIONS].items():
#         if nod[N] == 0:
#             scor = float('inf')
#         else:
#             expandare = nod[Q] / nod[N]
#             explorare = c * sqrt(2 * log(N_node) / nod[N])
#             scor = expandare + explorare
#             # print(scor)
#         # python e ciudat la if uri =))
#         # if-ul trebuia invers, adica conditiile din if puse invers
#         if mutare_optima is None or scor > max_scor:
#             mutare_optima = mutare
#             max_scor = scor
#         # print(max_scor)
#     # TODO <2>
#     # Se caută acțiunea a care maximizează expresia:
#     # Q_a / N_a  +  c * sqrt(2 * log(N_node) / N_a)
#     return mutare_optima

# # Scurtă testare
# test_root = {N: 6, Q: 0.75, PARENT: None, ACTIONS: {}}
# test_root[ACTIONS][3] = {N: 4, Q: 0.9, PARENT: test_root, ACTIONS: {}}
# test_root[ACTIONS][5] = {N: 2, Q: 0.1, PARENT: test_root, ACTIONS: {}}

# print(select_action(test_root, CP))  # ==> 5 (0.8942 < 0.9965)
# print(select_action(test_root, 0.3)) # ==> 3 (0.50895 > 0.45157)

# # Algoritmul MCTS (UCT)
# #  state0 - starea pentru care trebuie aleasă o acțiune
# #  budget - numărul de iterații permis / numărul de noduri care va fi construit
# #  tree - un arbore din explorările anterioare, dacă există
# #  opponent_s_action - ultima acțiune a adversarului, dacă există

# def mcts(state0, budget, tree, opponent_s_action = None):
#     # TODO <3>
#     # DACĂ există un arbore construit anterior ȘI
#     #   acesta are un copil ce corespunde ultimei acțiuni a adversarului,
#     # ATUNCI acel copil va deveni nodul de început pentru algoritm.
#     # ALTFEL, arborele de start este un nod gol.
#     if tree is not None and tree[opponent_s_action] in tree[ACTIONS]:
#         tree = tree[ACTIONS][opponent_s_action]
#     else:
#         tree = init_node(init_state())
#     # tree = None # TODO
    
#     #---------------------------------------------------------------

#     for x in range(budget):
#         # Pornim procesul de selecție din nodul rădăcină / starea inițială
#         node = tree
#         state = state0
#         # TODO <4>
#         # Coborâm în arbore până când ajungem la o stare finală
#         # sau la un nod cu acțiuni neexplorate.
#         while not is_final(state):
#             posibilitati = get_available_actions(state)
#             if not all(mutare in node[ACTIONS] for mutare in posibilitati):
#                 break
#             mutare_noua = select_action(node)
#             node = node[ACTIONS][mutare_noua]
#             state = apply_action(state, mutare_noua)
        
#         #---------------------------------------------------------------
        
#         # TODO <5>
#         # Dacă am ajuns într-un nod care nu este final și din care nu s-au
#         # `încercat` toate acțiunile, construim un nod nou.
#         isok = get_available_actions(state)
#         if not is_final(state) and isok is not None: 
#             # alea de mai de sus se recicleaza pentrua  putea trece mai departe
#             alta_mutare_noua = choice(isok) # se recicleaza ca merge pana la 2 nivele in arb
#             state = apply_action(state, alta_mutare_noua)
#             nod_nou = init_node(state, node)
#             # acum trece mai departe
#             if nod_nou is not None:
#                 node[ACTIONS][alta_mutare_noua] = nod_nou
#                 # aici se fac legaturile, ca sa se treaca mai departe
#                 nod_nou[PARENT] = node # pune head-ul current ca parinte
#                 # e gen ca si cum ai adauga un nod nod intr-o liste, ca la liste inlantuite
        
#         #---------------------------------------------------------------
        
#         # TODO <6>
#         # Se simulează o desfășurare a jocului până la ajungerea într-o
#         # starea finală. Se evaluează recompensa în acea stare.
#         # state = state0 # de înlocuit cu node[STATE]
#         while not is_final(state):
#             posibilitati = get_available_actions(state)
#             mutare = choice(posibilitati)
#             state = apply_action(state, mutare)
#             # break
        
#         winner = is_final(state)
#         if winner == state0[NEXT_PLAYER]:
#             reward = 1
#         elif winner == (3 - state0[NEXT_PLAYER]):
#             reward = 0.0
#         elif winner == 3:
#             reward = 0.25
#         else:
#             reward = 0.5
#         #---------------------------------------------------------------

#         # TODO <7>
#         # Se actualizează toate nodurile de la node către rădăcină:
#         #  - se incrementează valoarea N din fiecare nod
#         #  - pentru nodurile corespunzătoare acestui jucător, se adună recompensa la valoarea Q
#         #  - pentru nodurile celelalte, valoarea Q se adună 1 cu minus recompensa
#         while node:
#             node[N] = node[N] + 1
#             if state0[NEXT_PLAYER] == node[STATE][NEXT_PLAYER]:         
#                 node[Q] = node[Q] + reward
#             else:
#                 node[Q] = node[Q] + (1 - reward)
#             node = node[PARENT]
#         #---------------------------------------------------------------

#     if tree:
#         final_action = select_action(tree, 0.0)
#         return (final_action, tree[ACTIONS][final_action])
#     # Acest cod este aici doar ca să nu dea erori testele mai jos; în mod normal tree nu trebuie să fie None
#     if get_available_actions(state0):
#         return (get_available_actions(state0)[0], init_node())
#     return (0, init_node(state0))

# # Testare MCTS
# (action, tree) = mcts(init_state(), 20, None, None)
# print(action)
# if tree: print_tree(tree[PARENT]) # Trebuie ca arborele să fie destul de echilibrat, nu dezechilibrat

# def play_games(games_no, budget1, budget2, verbose = False):
#     # Efortul de căutare al jucătorilor
#     budget = [budget1, budget2]
    
#     score = {p: 0 for p in name}
        
#     for i in range(games_no):
#         # Memoriile inițiale
#         memory = [None, None]
        
#         # Se desfășoară jocul
#         state = init_state()
#         last_action = None
    
#         while state and not is_final(state):
#             p = state[NEXT_PLAYER] - 1
#             (action, memory[p]) = mcts(state, budget[p], memory[p], last_action)
#             state = apply_action(state, action)
#             last_action = action
        
#         # Cine a câștigat?
#         if(state):
#             winner = is_final(state)
#             score[name[winner]] += + 1
        
#         # Afișăm
#         if verbose and state:
#             print_state(state)
#             if winner == 3: print("Remiză.")
#             else: print("A câștigat %s" % name[winner])

#     # Afișează scorul final
#     if verbose:
#         print("Scor final: %s." % (str(score)))
#     return score

# # play_games(N, BR, BA, VERBOSE) - rulează N jocuri, cu bugetele BR pt ROȘU și BA pt ALBASTRU
# # TODO: rulați pentru câte 5 jocuri:
# play_games(5, 2, 30, True) # ne așteptăm să câștige ALBASTRU
# play_games(5, 30, 2, True) # ne așteptăm să câștige ROȘU

# # TODO: rulați pentru câte 20 de jocuri:
# ngames = 0
# print(f"Rezultate pentru câte {ngames} de jocuri (ROȘU / ALBASTRU / REMIZĂ):")
# print("Buget mic | Buget mare | avantaj ALBASTRU | avantaj ROȘU")
# for small, big in [(2, 30), (5, 30), (10, 30), (20, 20)]:
#     print(f"{small : >5}     | {big : >6}     |", end = "")
#     score = play_games(ngames, small, big, False)
#     print("{:>16}".format(f"{score[name[RED]]} / {score[name[BLUE]]} / {score[name[DRAW]]}"), end = "  |")
#     score = play_games(ngames, big, small, False)
#     print("{:>12}".format(f"{score[name[RED]]} / {score[name[BLUE]]} / {score[name[DRAW]]}"), end = "  |")
#     print()
    
    
#     # Dimensiunile matricei
# HEIGHT, WIDTH = len(intervale), len(zile)

# # Pozițiile din tuplul ce constituie o stare
# BOARD, NEXT_PLAYER = 1, 0 # nuj ce sa fac cu player-ul deocamdata
# INTERVAL, ZI = intervale[0], zile[0]

# # Jucătorii
# RED, BLUE, DRAW = 1, 2, 3
# name = ["", "ROȘU", "ALBASTRU", "REMIZĂ"]

# # Funcție ce întoarce o stare inițială
# def init_state():
#     return ([[0 for row in range(HEIGHT)] for col in range(WIDTH)], RED)

# # Funcție ce afișează o stare
# def print_state(state):
#     for row in range(HEIGHT-1, -1, -1):
#         ch = " RA"
#         l = map(lambda col: ch[state[BOARD][col][row]], range(WIDTH))
#         print("|" + "".join(l) + "|")
#     print("+" + "".join("-" * WIDTH) + "+")
#     print("Urmează: %d - %s" % (state[NEXT_PLAYER], name[state[NEXT_PLAYER]]))

# # Se afișează starea inițială a jocului
# print("Starea inițială:")
# print_state(init_state())

# # Funcție ce întoarce acțiunile valide dintr-o stare dată
# def get_available_actions(state):
#     # TODO <1>
#     valid_action = []
#     board = state[0]
#     #print(board)
#     j = 0
#     for i in board:
#         #print(i[-1])
#         if i[-1] == 0:
#             valid_action.append(j)
#         j += 1

#     return valid_action

# from copy import deepcopy
# from functools import reduce

# # Funcție ce întoarce starea în care se ajunge prin aplicarea unei acțiuni
# def apply_action(state, action):
#     if action >= len(state[BOARD]) or 0 not in state[BOARD][action]:
#         print("Action " + str(action) + " is not valid.")
#         return None
#     new_board = deepcopy(state[BOARD])
#     new_board[action][new_board[action].index(0,0)] = state[NEXT_PLAYER]
#     return (new_board, 3 - state[NEXT_PLAYER])


# # Se afișează starea la care se ajunge prin aplicarea unor acțiuni
# somestate = reduce(apply_action, [3, 4, 3, 2, 2, 6, 3, 3, 3, 3], init_state())
# print_state(somestate)
# get_available_actions(somestate)

# # Funcție ce verifică dacă o stare este finală
# def is_final(state):
#     # Verificăm dacă matricea este plină
#     if not any([0 in col for col in state[BOARD]]): return 3
#     # Jucătorul care doar ce a mutat ar putea să fie câștigător
#     player = 3 - state[NEXT_PLAYER]
    
#     ok = lambda pos: all([state[BOARD][c][r] == player for (r, c) in pos])
#     # Verificăm verticale
#     for row in range(HEIGHT):
#         for col in range(WIDTH - 4):
#             if ok([(row, col + i) for i in range(4)]): return player
#     # Verificăm orizontale
#     for col in range(WIDTH):
#         for row in range(HEIGHT-4):
#             if ok([(row + i, col) for i in range(4)]): return player
#     # Verificăm diagonale
#     for col in range(WIDTH-4):
#         for row in range(HEIGHT-4):
#             if ok([(row + i, col+i) for i in range(4)]): return player
#     for col in range(WIDTH-4):
#         for row in range(HEIGHT-4):
#             if ok([(row + i, col+4-i) for i in range(4)]): return player
#     return False
# # Ajungem la o stare finală oarecare și o afișăm.
# from random import choice

# rand_state = init_state()
# print(rand_state)
# while not is_final(rand_state):
#     actions = get_available_actions(rand_state)
#     if not actions:
#         break
#     action = choice(get_available_actions(rand_state))
#     rand_state = apply_action(rand_state, action)

# print_state(rand_state)
# print("Învingător: %s" % (name[is_final(rand_state)]))
# # Exemplu: Se afișează starea obținută prin aplicarea unor acțiuni
# all_actions = [1, 2, 1, 3, 1, 4, 2, 5]
# some_state = reduce(apply_action, all_actions, init_state())
# print_state(some_state)
# print("Învingător: %s" % (name[is_final(some_state)]))

# # Constante

# N = 'N'
# Q = 'Q'
# STATE = 'state'
# PARENT = 'parent'
# ACTIONS = 'actions'

# def print_tree(tree, indent = 0):
#     if not tree:
#         return
#     tab = "".join(" " * indent)
#     print("%sN = %d, Q = %f" % (tab, tree[N], tree[Q]))
#     for a in tree[ACTIONS]:
#         print("%s %d ==> " % (tab, a))
#         print_tree(tree[ACTIONS][a], indent + 3)
        
# # Funcție ce întoarce un nod nou,
# # eventual copilul unui nod dat ca argument
# def init_node(state, parent = None):
#     return {N: 0, Q: 0, STATE: state, PARENT: parent, ACTIONS: {}}

# from math import sqrt, log

# # constanta care reglează raportul între explorare și exploatare (CP = 0 -> doar exploatare)
# CP = 1.0 / sqrt(2.0)

# # Funcție ce alege o acțiune dintr-un nod
# def select_action(node, c = CP):
#     N_node = node[N]
    
#     mutare_optima = None
#     max_scor = float('-inf')

#     for mutare, nod in node[ACTIONS].items():
#         if nod[N] == 0:
#             scor = float('inf')
#         else:
#             expandare = nod[Q] / nod[N]
#             explorare = c * sqrt(2 * log(N_node) / nod[N])
#             scor = expandare + explorare
#             # print(scor)
#         # python e ciudat la if uri =))
#         # if-ul trebuia invers, adica conditiile din if puse invers
#         if mutare_optima is None or scor > max_scor:
#             mutare_optima = mutare
#             max_scor = scor
#         # print(max_scor)
#     # TODO <2>
#     # Se caută acțiunea a care maximizează expresia:
#     # Q_a / N_a  +  c * sqrt(2 * log(N_node) / N_a)
#     return mutare_optima

# # Scurtă testare
# test_root = {N: 6, Q: 0.75, PARENT: None, ACTIONS: {}}
# test_root[ACTIONS][3] = {N: 4, Q: 0.9, PARENT: test_root, ACTIONS: {}}
# test_root[ACTIONS][5] = {N: 2, Q: 0.1, PARENT: test_root, ACTIONS: {}}

# print(select_action(test_root, CP))  # ==> 5 (0.8942 < 0.9965)
# print(select_action(test_root, 0.3)) # ==> 3 (0.50895 > 0.45157)

# # Algoritmul MCTS (UCT)
# #  state0 - starea pentru care trebuie aleasă o acțiune
# #  budget - numărul de iterații permis / numărul de noduri care va fi construit
# #  tree - un arbore din explorările anterioare, dacă există
# #  opponent_s_action - ultima acțiune a adversarului, dacă există

# def mcts(state0, budget, tree, opponent_s_action = None):
#     # TODO <3>
#     # DACĂ există un arbore construit anterior ȘI
#     #   acesta are un copil ce corespunde ultimei acțiuni a adversarului,
#     # ATUNCI acel copil va deveni nodul de început pentru algoritm.
#     # ALTFEL, arborele de start este un nod gol.
#     if tree is not None and tree[opponent_s_action] in tree[ACTIONS]:
#         tree = tree[ACTIONS][opponent_s_action]
#     else:
#         tree = init_node(init_state())
#     # tree = None # TODO
    
#     #---------------------------------------------------------------

#     for x in range(budget):
#         # Pornim procesul de selecție din nodul rădăcină / starea inițială
#         node = tree
#         state = state0
#         # TODO <4>
#         # Coborâm în arbore până când ajungem la o stare finală
#         # sau la un nod cu acțiuni neexplorate.
#         while not is_final(state):
#             posibilitati = get_available_actions(state)
#             if not all(mutare in node[ACTIONS] for mutare in posibilitati):
#                 break
#             mutare_noua = select_action(node)
#             node = node[ACTIONS][mutare_noua]
#             state = apply_action(state, mutare_noua)
        
#         #---------------------------------------------------------------
        
#         # TODO <5>
#         # Dacă am ajuns într-un nod care nu este final și din care nu s-au
#         # `încercat` toate acțiunile, construim un nod nou.
#         isok = get_available_actions(state)
#         if not is_final(state) and isok is not None: 
#             # alea de mai de sus se recicleaza pentrua  putea trece mai departe
#             alta_mutare_noua = choice(isok) # se recicleaza ca merge pana la 2 nivele in arb
#             state = apply_action(state, alta_mutare_noua)
#             nod_nou = init_node(state, node)
#             # acum trece mai departe
#             if nod_nou is not None:
#                 node[ACTIONS][alta_mutare_noua] = nod_nou
#                 # aici se fac legaturile, ca sa se treaca mai departe
#                 nod_nou[PARENT] = node # pune head-ul current ca parinte
#                 # e gen ca si cum ai adauga un nod nod intr-o liste, ca la liste inlantuite
        
#         #---------------------------------------------------------------
        
#         # TODO <6>
#         # Se simulează o desfășurare a jocului până la ajungerea într-o
#         # starea finală. Se evaluează recompensa în acea stare.
#         # state = state0 # de înlocuit cu node[STATE]
#         while not is_final(state):
#             posibilitati = get_available_actions(state)
#             mutare = choice(posibilitati)
#             state = apply_action(state, mutare)
#             # break
        
#         winner = is_final(state)
#         if winner == state0[NEXT_PLAYER]:
#             reward = 1
#         elif winner == (3 - state0[NEXT_PLAYER]):
#             reward = 0.0
#         elif winner == 3:
#             reward = 0.25
#         else:
#             reward = 0.5
#         #---------------------------------------------------------------

#         # TODO <7>
#         # Se actualizează toate nodurile de la node către rădăcină:
#         #  - se incrementează valoarea N din fiecare nod
#         #  - pentru nodurile corespunzătoare acestui jucător, se adună recompensa la valoarea Q
#         #  - pentru nodurile celelalte, valoarea Q se adună 1 cu minus recompensa
#         while node:
#             node[N] = node[N] + 1
#             if state0[NEXT_PLAYER] == node[STATE][NEXT_PLAYER]:         
#                 node[Q] = node[Q] + reward
#             else:
#                 node[Q] = node[Q] + (1 - reward)
#             node = node[PARENT]
#         #---------------------------------------------------------------

#     if tree:
#         final_action = select_action(tree, 0.0)
#         return (final_action, tree[ACTIONS][final_action])
#     # Acest cod este aici doar ca să nu dea erori testele mai jos; în mod normal tree nu trebuie să fie None
#     if get_available_actions(state0):
#         return (get_available_actions(state0)[0], init_node())
#     return (0, init_node(state0))

# # Testare MCTS
# (action, tree) = mcts(init_state(), 20, None, None)
# print(action)
# if tree: print_tree(tree[PARENT]) # Trebuie ca arborele să fie destul de echilibrat, nu dezechilibrat

# def play_games(games_no, budget1, budget2, verbose = False):
#     # Efortul de căutare al jucătorilor
#     budget = [budget1, budget2]
    
#     score = {p: 0 for p in name}
        
#     for i in range(games_no):
#         # Memoriile inițiale
#         memory = [None, None]
        
#         # Se desfășoară jocul
#         state = init_state()
#         last_action = None
    
#         while state and not is_final(state):
#             p = state[NEXT_PLAYER] - 1
#             (action, memory[p]) = mcts(state, budget[p], memory[p], last_action)
#             state = apply_action(state, action)
#             last_action = action
        
#         # Cine a câștigat?
#         if(state):
#             winner = is_final(state)
#             score[name[winner]] += + 1
        
#         # Afișăm
#         if verbose and state:
#             print_state(state)
#             if winner == 3: print("Remiză.")
#             else: print("A câștigat %s" % name[winner])

#     # Afișează scorul final
#     if verbose:
#         print("Scor final: %s." % (str(score)))
#     return score

# # play_games(N, BR, BA, VERBOSE) - rulează N jocuri, cu bugetele BR pt ROȘU și BA pt ALBASTRU
# # TODO: rulați pentru câte 5 jocuri:
# play_games(5, 2, 30, True) # ne așteptăm să câștige ALBASTRU
# play_games(5, 30, 2, True) # ne așteptăm să câștige ROȘU

# # TODO: rulați pentru câte 20 de jocuri:
# ngames = 0
# print(f"Rezultate pentru câte {ngames} de jocuri (ROȘU / ALBASTRU / REMIZĂ):")
# print("Buget mic | Buget mare | avantaj ALBASTRU | avantaj ROȘU")
# for small, big in [(2, 30), (5, 30), (10, 30), (20, 20)]:
#     print(f"{small : >5}     | {big : >6}     |", end = "")
#     score = play_games(ngames, small, big, False)
#     print("{:>16}".format(f"{score[name[RED]]} / {score[name[BLUE]]} / {score[name[DRAW]]}"), end = "  |")
#     score = play_games(ngames, big, small, False)
#     print("{:>12}".format(f"{score[name[RED]]} / {score[name[BLUE]]} / {score[name[DRAW]]}"), end = "  |")
#     print()
    