#
# X hacia abajo Y hacia la derecha centrado en la esquina sup izq
import heapq
import random

import MySQLdb
import numpy as np
import pylab as plt
import skimage
from skimage import io
from skimage.color import rgb2hsv,hsv2rgb
from skimage.transform import resize

from batleStub import virtualBattle
from tools.agent import agresiveAgent
from tools.database import getRandomGamesDb, saveGameToDb, jointCellTypes
from tools.model import doTransition, calcReward, checkTerminal

#Convencciones EL TROOPS[0] ES RED Y EL TROOPS[1] ES BLUE

class gameSlider(object):
    def __init__(self, ax, imageList):
        self.ax = ax
        # ax.set_title('use scroll wheel to navigate images')

        self.data = imageList
        self.ind = 0
        self.maxImg = len(imageList)
        self.im = ax.imshow(self.data[self.ind][0])
        self.update()

    def onscroll(self, event):
        if event.button == 'up':
            self.ind = (self.ind - 1) % (self.maxImg)
        else:
            self.ind = (self.ind + 1) % (self.maxImg)

        self.update()

    def update(self):
        self.im.set_data(self.data[self.ind][0])
        self.ax.set_title(self.data[self.ind][1]+'slice %s' % self.ind)
        self.im.axes.figure.canvas.draw()


testGame = [
                {
                    'Terrain':[
                    {'x':1,
                    'y':2,
                    'Terrain_type':0
                     }
                    ],
                    'Troops':[
                            [{'x':1,
                             'y':2,
                             'Can_move':0,
                             'Troop':1,
                             'Team':0,
                             'HP':100
                            }],
                            []
                            ],

                    'Action':{
                        'Xi':1,
                        'Yi':2,
                        'Xf':3,
                        'Yf':4,
                        'Xa':5,
                        'Ya':6,
                        'action_type':0 # Attacking if value is 1.
                    },
                    'next_terminal':-1 #If -1 Lost game in next_state 0 non terminal +1 won in next_state
                    }

            ]

"""
A query to the db returns a list of cells that form a states
All this columns make a cell
current_state_id
game_id	xi
yi
xf
yf
action
next_state
id
can_move
x
y
terrain_type_id
troop_id
team_id	hp
visibility
is_solid
state_id
"""

#NOW RANDOM PROB IS inside agent behavior DEFAULT IS 0
def gameLoop(baseBattle, initialState, agentRed,agentBlue, store=True,cursor=None):

    #just to avoid infinite loops
    maxIter = 100
    # print "bla"
    #get initial game state
    game = []
    state = initialState
    baseBattle.setGameState(state)
    #ASEGURATE QUE EL EQUIPO INICIAL SEA RED
    baseBattle.activePlayer = baseBattle.teams[0]
    nextState = None

    #Is red or blue turn?
    activeTeam = 0

    while checkTerminal(state, activeTeam) == 0:
        agent = agentRed if activeTeam == 0 else agentBlue
        for troop in state['Troops'][activeTeam]:
            heapAction = [] #The python heap keep TUPLES (value,action) sorted by value like a heap
            accionesValidas = baseBattle.getPossibleMoves((troop['x'], troop['y']))

            #Random action or evaluation ?
            randomNumber = random.random()
            if randomNumber < agent.randomProb:
                for action in accionesValidas:
                    value = agent.evalAction(state, action,activeTeam)
                    heapq.heappush(heapAction,(value,action))
                bestValue, bestAction = heapq.heappop(heapAction)
                # print "Best action to choose ",bestAction
            else:
                bestAction = random.choice(accionesValidas)
                bestValue = -1

            nextState = doTransition(state, bestAction)
            reward = calcReward(state, bestAction, nextState, activeTeam)

            #place if next state is win,lose or non terminal
            state['next_terminal'] = checkTerminal(nextState, activeTeam)
            #set Action to state
            state['Action'] = bestAction

            # showTransition(state)

            #append transition to game
            game.append(state)
            state = nextState
            baseBattle.setGameState(state)


            # maybe we win but we havent move all
            if checkTerminal(state, activeTeam) != 0:
                break

        #after all troops moved refresh troop_wait and give turn to opponent
        for troop in state['Troops'][activeTeam]:
            troop['Can_move'] = 1
        activeTeam = 1-activeTeam
        baseBattle.activePlayer = baseBattle.teams[activeTeam]


        maxIter -= 1
        if maxIter == 0:
            print "Maxima iteracion alcanzada saliendo"
            break

    #place terminal in last transition
    if store:
        #open db and store game
        saveGameToDb(cursor, game, 'GameComment')

    return game



def generateGame(cursor, store=True):

    #TODO create map independent from battle. A lot of innecesary stuff there and pygame is heavy

    #Generate map
    batalla = virtualBattle.randomMap()
    batalla.initGame()

    initialState = batalla.getGameState()

    #Send agresive evaluation. Always try to attack
    #If action type == 1 is an attack then eval to 1 else eval to 0
    agresiveRed = agresiveAgent()
    agresiveBlue = agresiveAgent()

    game = gameLoop(batalla,initialState,agresiveRed,agresiveBlue,store=store,cursor=cursor)

    print "Game generation ended ",len(game)," transitions"
    return game


def showTransition(transition,dontShow=False):
    rutaTiles = "tiles/"
    rutaTroops="units/"
    dictMap = {0:'WaterOpen.png',
               1: 'Grass.png', 2: 'RoadInter.png',
               3: 'Forest.png', 4: "simpleMountain.png", 5: 'simpleRiver.png',
               6: 'BridgeHoriz.png'}
    dictTroop = {1:'Infantry.png',2:'RocketInf.png',
                 3:'SmTank.png',4:"LgTank.png",5:'Artillery.png',
                 6:'APC.png'}

    dictCell = jointCellTypes(transition)

    #Create empty image 10 * 16

    base = io.imread("tiles/"+dictMap[0])
    wImg = skimage.img_as_float(io.imread(rutaTroops + "wait.png"))
    maxRows = 10
    maxCols = 16
    tileDim = 64

    base = resize(base, (tileDim * maxRows, tileDim * maxCols))

    for cell in transition["Terrain"]:
        type = cell["Terrain_type"]
        x = cell["y"]*tileDim
        y = cell["x"]*tileDim
        img = io.imread(rutaTiles+dictMap[type])
        img = skimage.img_as_float(img)
        base[y:y + img.shape[0],x:x + img.shape[1]] = img


    #place troops
    for index,side in enumerate(["Red","Blue"]):
        for troop in transition["Troops"][index]:
            canMove = troop["Can_move"]
            hp = troop["HP"]
            type = troop["Troop"]
            img = skimage.img_as_float(io.imread(rutaTroops+side+dictTroop[type]))
            hpImg = skimage.img_as_float(io.imread(rutaTroops+str(hp/10)+".png"))

            x = troop["y"] * tileDim
            y = troop["x"] * tileDim

            mask = np.zeros(base.shape)
            mask[y:y + tileDim, x:x + tileDim] = img
            ms = np.bool_(mask[:, :, 3])
            base[ms] = mask[ms]

            mask = np.zeros(base.shape)
            mask[y:y + tileDim, x:x + tileDim] = hpImg
            ms = np.bool_(mask[:,:,3])
            base[ms] = mask[ms]

            if not canMove:
                mask = np.zeros(base.shape)
                mask[y:y + tileDim, x:x + tileDim] = wImg
                ms = np.bool_(mask[:, :, 3])
                base[ms] = mask[ms]

    if (transition.has_key('Action')):
        actionMask = np.zeros((base.shape[0],base.shape[1],3))

        if (transition['Action']['action_type']):
            x = transition['Action']["Ya"] * tileDim
            y = transition['Action']["Xa"] * tileDim
            actionMask[y:y + tileDim, x:x + tileDim] = [1,0,0]
        x = transition['Action']["Yf"] * tileDim
        y = transition['Action']["Xf"] * tileDim
        actionMask[y:y + tileDim, x:x + tileDim] = [0,0,1]
        x = transition['Action']["Yi"] * tileDim
        y = transition['Action']["Xi"] * tileDim
        actionMask[y:y + tileDim, x:x + tileDim] = [0,1,0]
        alpha = 0.6

        temp = rgb2hsv(base[:,:,:3])
        color_mask_hsv = rgb2hsv(actionMask)
        temp[..., 0] = color_mask_hsv[..., 0]
        temp[..., 1] = color_mask_hsv[..., 1] * alpha

        temp = hsv2rgb(temp)


        if (transition['Action']['action_type']):
            x = transition['Action']["Ya"] * tileDim
            y = transition['Action']["Xa"] * tileDim
            base[y:y + tileDim, x:x + tileDim,:3] = temp[y:y + tileDim, x:x + tileDim]

        x = transition['Action']["Yf"] * tileDim
        y = transition['Action']["Xf"] * tileDim
        base[y:y + tileDim, x:x + tileDim,:3] = temp[y:y + tileDim, x:x + tileDim]

        x = transition['Action']["Yi"] * tileDim
        y = transition['Action']["Xi"] * tileDim
        base[y:y + tileDim, x:x + tileDim,:3] = temp[y:y + tileDim, x:x + tileDim]

        stringOut = "Xi, Yi : " + str((transition['Action']["Xi"],
                                       transition['Action']["Yi"])) + " " +"Xf, Yf : " + \
                    str((transition['Action']["Xf"], transition['Action']["Yf"])) + " " +"Type : " +\
                    str(transition['Action']["action_type"]) + " ""Xa, Ya : " + str((transition['Action']["Xa"],
                                                                                     transition['Action']["Ya"])) + " "

    if dontShow:
        return (base,stringOut)
    plt.suptitle(stringOut)
    plt.imshow(base)
    plt.show()

def showGameScroll(gameList):


    imageList = [showTransition(state, True) for state in gameList]

    fig = plt.figure()
    ax = fig.add_subplot(111)

    tracker = gameSlider(ax, imageList)

    fig.canvas.mpl_connect('scroll_event', tracker.onscroll)
    plt.show()


if __name__ == '__main__':


    db = db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    cursor = db.cursor()
    cursor = db.cursor (MySQLdb.cursors.DictCursor)


    # mode = "showRandomGames"
    mode = "generateRandomGames"

    if mode == "generateRandomGames":
        for i in range(2):
            game = generateGame(cursor, False)

    if mode == "showRandomGames":
        gameList = getRandomGamesDb(2, cursor)
        #If goes too slow use for state in game : showTransition(state) JUST FOR BETTER VISUALIZATION
        for game in gameList:
            showGameScroll(game)

    cursor.close()
    db.commit()
    db.close()