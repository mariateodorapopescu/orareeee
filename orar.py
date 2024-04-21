from __future__ import annotations
import yaml
from typing import Callable
from copy import copy
from copy import deepcopy
from functools import reduce
import numpy as np
import random

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

def __generate_actions__(materii, profi, sali):
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
                    
actions = __generate_actions__(materii, profi, sali)
print(actions)

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

overlaps = __get_overlaps__(possibilities, sali)

# here the action is shorter
def __where__(action):
    positions = []
    for index_i, i in enumerate(possibilities):
        for index_j, j in enumerate(possibilities[index_i]):
            for k in j:
                if action[0] == k[0] and action[1] == k[1] and action[2] == k[2]:
                    dummy = (index_j, index_i)
                    positions.append(dummy)
    return positions


# here is the whole version of the action
# ('Luni', '08-10', 'DS', 'EG390', 'RG')
def __where_in_table1__(action, sched):
    positions = []
    for index_i, i in enumerate(sched):
        for index_j, j in enumerate(sched[i]):
            for k in j:
                if action[0] == index_i and action[1] == index_j and action[2] == k[0]:
                    if sched[action[0]][action[1]] == None or sched[action[0]][action[1]].get(action[3], None) == None:
                        dummy = (index_j, index_i)
                        positions.append(dummy)
    return positions

def __where_in_table__(action, sched):
    positions = []
    for day, intervals in sched.items():
        for interval, info in intervals.items():
            if action[0] == day and action[1] == interval and action[3] == info[0] and action[4] == info[1]:
                positions.append((day, interval))
    return positions

def __where2__(action, sched):
    positions = []
    for day, intervals in sched.items():
        for interval, info in intervals.items():
            if action[0] == day and action[1] == interval and action[3] == info[0] and action[4] == info[1]:
                positions.append((day, interval))
    return positions

sched = {}
schedk1= 'Luni'
sched[schedk1] = {}
schedk2 = '8-10'
sched[schedk1][schedk2] = {}
pos = []
pos = __where_in_table__(('Luni', '08-10', 'DS', 'EG390', 'RG'), sched)
print(pos)


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

def generate_schedule_dict(matrix, zile, intervale):
    schedule_dict = {}
    remain = [interval.copy() for interval in matrix]
    for idx, day in enumerate(zile):
        day_dict = {}
        for interval_idx, interval in enumerate(intervale):
            day_dict[interval] = {}
            for tuplu in matrix[interval_idx][idx]:
                day_dict[interval][tuplu[2]] = (tuplu[0], tuplu[1])
                remain[interval_idx][idx].remove(tuplu)
            if not remain[interval_idx][idx]:
                remain[interval_idx].pop(idx)
        schedule_dict[day] = day_dict
    return schedule_dict, remain

sched, remain = generate_schedule_dict(possibilities, zile, intervale)

def __compute_conflicts__(sched):
    conflicts = 0
    for day in sched:
        for interval in sched[day]:
            teachers = {}
            for subject in sched[day][interval]:
                teacher = sched[day][interval][subject][1]
                if teacher in teachers:
                    conflicts += 1
                    break
                else:
                    teachers[teacher] = True
    return conflicts

nr = __compute_conflicts__(sched)

def __generate__(matrix, zile, intervale, sched, remains):
    schedule_dict = sched
    remain = []
    for idx, day in enumerate(zile):
        for interval_idx, interval in enumerate(intervale):
            # Obținem o listă de indexuri randomizate pentru fiecare zi și interval
            indices = list(range(len(matrix[interval_idx][idx])))
            random.shuffle(indices)
            for index in indices:
                tuplu = matrix[interval_idx][idx][index]
                for room in schedule_dict[day][interval]:
                    if tuplu[2] == room and tuplu[0] == schedule_dict[day][interval][room][0] and tuplu[1] == schedule_dict[day][interval][room][1]:
                        schedule_dict[day][interval].pop(room, None)
                        if not schedule_dict[day][interval]:
                            schedule_dict[day].pop(interval, None)
                        break
                else:
                    remain.append(tuplu)
    return schedule_dict, remain

def __good_ones__(sched, remains):
    good_ones = []
    new_sched = sched.copy()
    new_remain = remains.copy()
    while __compute_conflicts__(new_sched) > 0:
        new_sched, new_remain = __generate__(possibilities, zile, intervale, new_sched, new_remain)
        good_ones.append(new_sched)
    return good_ones

class State:
    def __init__(
        self, 
        size: int, 
        orar: list[list[list[tuple]]] | None = None, 
        conflicts: int | None = None, 
        seed: int = 100
    ) -> None:
        
        self.size = size
        self.orar = orar if orar is not None else State.generate_orar(size, seed)
        self.nconflicts = conflicts if conflicts is not None \
            else State.__compute_conflicts(self.orar)
    
    def apply_move(self, action: tuple) -> 'State':
        day, interval, subject, room, teacher = action
        old_orar = self.orar
        new_orar = copy(self.orar)
        new_orar[interval][day].append((subject, teacher, room))
        _conflicts = self.nconflicts
        for i, day in enumerate(new_orar):
            for j, interval in enumerate(day):
                if interval:
                    overlaps = self.get_overlaps(new_orar)
                    _conflicts = len(overlaps)
        return State(self.size, new_orar, _conflicts)
    
    @staticmethod
    def generate_orar(size: int, seed: int) -> list[list[list[tuple]]]:
        random.seed(seed)
        orar = [[[] for _ in range(size)] for _ in range(size)]
        return orar
    
    @staticmethod
    def __compute_conflicts(orar: list[list[list[tuple]]]) -> int:
        conflicts = 0
        for day in orar:
            for interval in day:
                for subject1, teacher1, room1 in interval:
                    for subject2, teacher2, room2 in interval:
                        if room1 == room2 and teacher1 == teacher2:
                            conflicts += 1
        return conflicts
    
    def get_overlaps(self, orar: list[list[list[tuple]]]) -> list[tuple]:
        overlaps = []
        for idx, day in enumerate(orar):
            for interval in day:
                for room in sali:
                    nr = 0
                    for subject, teacher, room_ in interval:
                        if room == room_:
                            nr += 1
                    if nr >= 2:
                        overlaps.append((room, idx, interval))
        return overlaps
    
    def conflicts(self) -> int:
        return self.nconflicts
    
    def is_final(self) -> bool:
        return self.nconflicts == 0
    
    def get_next_states(self, actions: list[tuple]) -> list['State']:
        return [self.apply_move(action) for action in actions]
    
    def __str__(self) -> str:
        display = ''
        for day, intervals in zip(zile, self.orar):
            display += f"{day}\n"
            for interval, data in zip(intervale, intervals):
                display += f"{interval}:\n"
                for subject, teacher, room in data:
                    display += f"\tSubject: {subject}, Teacher: {teacher}, Room: {room}\n"
        return display
    
    def display(self) -> None:
        print(self)
    
    def clone(self) -> 'State':
        return State(self.size, copy(self.orar), self.nconflicts)
