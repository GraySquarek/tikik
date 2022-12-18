import os
import json
import random
import copy
import numpy as np
import matplotlib.pyplot as plt


class Game:

    def __init__(self, field=None):
        self.field = None

        if field:
            self.field = field
        else:
            self.start()

    def start(self):
        self.field = [' '] * 9

    def printField(self):
        row = ''
        for i in range(len(self.field)):
            cell = self.field[i]
            row += '['
            if cell != ' ':
                row += cell
            else:
                row += str(i + 1)
            row += ']'
            if (i % 3 == 2):
                print(row)
                row = ''

    def set(self, position, side):
        pos = int(position) - 1
        self.field[pos] = side

    def getFree(self):
        free = []
        for i in range(len(self.field)):
            cell = self.field[i]
            if (cell == ' '):
                free.append((i + 1))
        return free

    def isDraw(self):
        free = self.getFree();
        return len(free) == 0;

    def isWin(self, side):
        for i in range(3):
            isW = True
            for j in range(3):
                if self.field[i * 3 + j] != side:
                    isW = False
                    break
            if isW:
                return isW

        for i in range(3):
            isW = True
            for j in range(3):
                if self.field[j * 3 + i] != side:
                    isW = False
                    break
            if isW:
                return isW

        isW = True;
        for i in range(3):
            if self.field[i * 3 + i] != side:
                isW = False
                break
        if isW:
            return isW

        isWi = True;
        for i in range(3):
            if self.field[(i * 3 + 2 - i)] != side:
                isW = False
                break
        if isW:
            return isW

        return False

    def getState(self, side):
        if side == 'x':
            return self.field

        newField = ''
        for i in range(len(self.field)):
            if self.field[i] == 'x':
                newField += 'o'
            elif self.field[i] == 'o':
                newField += 'x'
            else:
                newField += self.field[i]

        return newField


class AIPlayer:
    def __init__(self, side, ai, isGreedy=True):
        self.side = side
        self.ai = ai
        self.oldState = None
        self.isGreedy = isGreedy

    def getSide(self):
        return self.side

    def makeStep(self, game):
        #получаем список доступных ходов
        free = game.getFree()

        #решаем, является ли текущий ход
        #зондирующим (случайным) или жадным (максимально выгодным)

        if not self.isGreedy:
            if ((random.randint(0,100)) < 30):
                #случайный ход
                step = random.choice(free)
                game.set(step, self.side)
                self.oldState = game.getState(self.side)
                return step

        #жадный ход
        rewards = {}
        for step in free:
            # для каждого доступного хода оцениваем состояние игры после него
            newGame = copy.deepcopy(game)
            newGame.set(step, self.side)
            rewards[step] = self.ai.getReward(newGame.getState(self.side))

        #выясняем, какое вознаграждение оказалось максимальным
        maxReward = 0
        for reward in rewards.values():
            if reward > maxReward:
                maxReward = reward

        #находим все шаги с максимальным вознаграждением
        steps = []

        for step in rewards:
            reward = rewards[step]
            if (maxReward > (reward - 0.01)) and (maxReward < (reward + 0.01)):
                steps.append(step)

        #корректируем оценку прошлого состояния
        #с учетом ценности нового состояния
        if (self.oldState):
            self.ai.correct(self.oldState, maxReward)

        #выбираем ход из ходов с максимальный вознаграждением
        step = random.choice(steps)
        game.set(step, self.side)

        #сохраняем текущее состояние для того,
        #чтобы откорректировать её ценность на следующем ходе
        self.oldState = game.getState(self.side)
        return step

    def loose(self):
        #корректируем ценность предыдущего состояния при проигрыше
        if self.oldState:
            self.ai.correct(self.oldState, 0)

    def win(self):
        #корректируем ценность предыдущего состояния при выигрыше
        if self.oldState:
            self.ai.correct(self.oldState, 1)

    def draw(self):
        #корректируем ценность предыдущего состояния при ничьей
        if self.oldState:
            self.ai.correct(self.oldState, 0.5)

def state_to_gmstate(state):
    """
    Переводим состояние игры из формата массива в формат строки,
    который используется игрой
    """
    gmstate = []
    for row in state:
        for ch in row:
            if ch == -1:
                gmstate.append(' ')
            elif ch == 1:
                gmstate.append('x')
            else:
                gmstate.append('o')
    return gmstate

def gmstep_to_step(step):
    """
    Переводим обозначение хода из принятого в игре
    в формат который ожидается на выходе агента
    """
    steps = {
        1:(1,1),
        2:(1,2),
        3:(1,3),
        4:(2,1),
        5:(2,2),
        6:(2,3),
        7:(3,1),
        8:(3,2),
        9:(3,3),
    }
    return (steps[step][0]-1,steps[step][1]-1)




class AI:

    def __init__(self):
        self.table = {}
        if os.path.isfile('./rewards.json'):
            with open('rewards.json', 'w') as json_file:
                self.table = json.load(json_file)
                print("loaded AI from rewards.json")

    def getReward(self, state):
        game = Game(state)

        # если победитель - мы, то оценка состояния игры "1"
        if game.isWin('x'):
            return 1

        # если победиль - соперник, то оценка состояния игры "0"
        if game.isWin('o'):
            return 0

        # смотрим ценность по таблице
        strstate = ''.join(state)
        if strstate in self.table.keys():
            return self.table[strstate]

        # если в таблице нет, то считаем начальной ценностью "0.5"
        return 0.5

    def correct(self, state, newReward):
        oldReward = self.getReward(state)
        strstate = ''.join(state)
        self.table[strstate] = oldReward + 0.1 * (newReward - oldReward)

    def save(self):
        with open('./rewards.json', 'w') as outfile:
            json.dump(self.table, outfile)

def get_AgentTicTacClass():
    class AgentTicTacGreedyClass:
        def __init__(self, is_zero):
            # is_zero == True если нолик
            self.player = None
            ai = AI()
            if is_zero:
                self.player = AIPlayer('o', ai, True)
            else:
                self.player = AIPlayer('x', ai, True)

        def get_action(self, state):
            # пример state = [[1,0,1],[0,1,0],[0,1,0]] 1 - это крестик, 0 - это нолик, -1 - пусто
            gmstate = state_to_gmstate(state)
            game = Game(field=gmstate)
            move = self.player.makeStep(game)
            return gmstep_to_step(move)  # возвращаем координаты хода

        def is_done(self, state, reward):
            # reward - вознаграждение 1 если выиграли , вызывается когда игра закончена
            gmstate = state_to_gmstate(state)
            game = Game(field=gmstate)
            return game.isWin(self.player.getSide())

    return AgentTicTacGreedyClass


AgentTicTacGreedy = get_AgentTicTacClass()


def initfun(par1, is_zero):
    # is_zero == True если нолик
    par1.player = None
    ai = AI()
    if is_zero:
        par1.player = AIPlayer('o', ai, False)
    else:
        par1.player = AIPlayer('x', ai, False)


# Агент где есть случайный выбор хода
AgentTicTacGreedyNew = get_AgentTicTacClass()
AgentTicTacGreedyNew.__init__ = initfun
#проверка победы
def check_win(state, label):
    for i in range(3):
        if np.all(state[i,:] == int(label)):
            return True
        elif np.all(state[:,i] == int(label)):
            return True
    if np.all(np.fliplr(state).diagonal() == int(label)):
        return True
    if np.all(state.diagonal() == int(label)):
        return True
    return False
#проведение 1 раунда
def two_came_in_one_came_out(agent_zeros, agent_ones, print_state = False):
    state = (np.zeros((3,3))-1).astype('int')
    while -1 in state:
        #ход креста
        state[agent_ones.get_action(state)] = 1
        if print_state:
            print(state)
            print()
        if check_win(state, 1):
            agent_ones.is_done(state, True)
            agent_zeros.is_done(state, False)
            return 1
        if not(-1 in state):
            break
        state[agent_zeros.get_action(state)] = 0
        if print_state:
            print(state)
            print()
        if check_win(state, 0):
            agent_ones.is_done(state, False)
            agent_zeros.is_done(state, True)
            return 0
    agent_ones.is_done(state, False)
    agent_zeros.is_done(state, False)
    return -1





def play(zeros_class, ones_class, rng=5, gmscnt=500):

    def graphic():
        plt.xlabel('Проведено игр')
        plt.ylabel('Победы')
        plt.title('График зависимости побед от общего кол-ва игр')
        plt.legend(['X', 'O', 'D'], loc=2)
        plt.grid(True)
        plt.show()

    a = [list]
    #countX = a[0]
    #countO = a[1]
    #countD = a[2]
    #1 - победа креста, 0 - победа нуля, -1 - ничья
    for _ in range(rng):
        a = [0, 0, 0]
        zeros = zeros_class(True)
        ones = ones_class(False)
        for i in range(gmscnt):
            a[two_came_in_one_came_out(zeros, ones, print_state = False)] += 1

        #plt.plot(i in range, a[0])
        print(a)


    #plt.plot(rng, countO, 'o-r', alpha=1, lw=2, color='g', mew=1, ms=1)
    #plt.plot(rng, countD, 'o-r', alpha=1, lw=2, color='b', mew=1, ms=1)
    graphic()


play(AgentTicTacGreedy, AgentTicTacGreedyNew)
