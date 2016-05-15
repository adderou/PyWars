#
# X hacia abajo Y hacia la derecha centrado en la esquina sup izq
from copy import copy

import MySQLdb
import heapq
import pygame
from pygame.locals import *
import numpy as np
from skimage import io
from skimage.transform import resize
import skimage
import pylab as plt
import random

#Convencciones EL TROOPS[0] ES BLUE Y EL TROOPS[1] ES RED
from battle import Battle

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

def gameToInputNN():
    pass



#nota 1 ya no es necesario first game id
def getGamefromDb(idGame,cursor):


    query = "SELECT * FROM `state`, `cell_states`   WHERE `game_id` = %s and `state_id` = `current_state_id` " \
            "ORDER  BY `order_in_game` "
    print 'Getting ',idGame
    cursor.execute(query,(str(idGame),))
    result = cursor.fetchall()

    listGame = []
    currentId = -1
    currentRow = None



    #get all rows in state,cell with game id
    for row in result:

        rowId = int(row['state_id'])

        if rowId != currentId:
            #change currentRow
            currentRow = {}
            currentId = rowId
            #format action
            currentRow['Action'] = {}
            currentRow['Action']['Xi'] = int(row['xi'])
            currentRow['Action']['Yi'] = int(row['yi'])
            currentRow['Action']['Xf'] = int(row['xf'])
            currentRow['Action']['Yf'] = int(row['yf'])
            currentRow['Action']['Xa'] = int(row['xa'])
            currentRow['Action']['Ya'] = int(row['ya'])
            currentRow['Action']['action_type'] = int(row['action'])

            #format next_terminal
            currentRow['next_terminal'] = int(row['next_terminal'])

            #initialize terrain, troops as empty lists
            currentRow['Terrain'] = []
            #Troops contains two list BlueTroops = list[0], RedTroops=list[1]
            currentRow['Troops'] = [[],[]]
            #append to gameList
            listGame.append(currentRow)

        #format cell things in currentRow object
        newCellTerrain = {'x':int(row['x']),'y':int(row['y']),'Terrain_type':int(row['terrain_type_id'])}

        currentRow['Terrain'].append(newCellTerrain)

        #Only add troop if troop_type != 0
        troop_type = int(row['troop_id'])
        if troop_type != 0:
            newCellTroop = {'x':int(row['x']),'y':int(row['y'])
                ,'Can_move':int(row['can_move']),'Troop':int(row['troop_id']),
                            'Team':int(row['team_id']),'HP':int(row['hp'])
                            }
            currentTeam = int(row['team_id'])
            currentRow['Troops'][currentTeam].append(newCellTroop)

    return listGame

"""
Take the entire game (list of transitions from start to end ) and save it in the DB
Game = [ (transition0) , (transition1) ..... ]
"""


def saveGameToDb(cursor, listaTrans, comment):


    #insert the first transition returning the transition id
    firstTrans = listaTrans[0]
    firstStateId = saveTransitionToDb(cursor,firstTrans,0,0) #Just put any gameId for the moment

    #insert new Game row (first_state, comment)

    insertQuery = "INSERT INTO `game`( `first_state`, `comment`)" \
                  " VALUES ( %s,%s); "

    cursor.execute(insertQuery,(str(firstStateId),comment))
    gameId = int(cursor.lastrowid)
    print 'La game id es ',gameId
    #edit first transition gameId
    cursor.execute("UPDATE `state` SET `game_id`= %s"
                   "  WHERE  `current_state_id`= %s ",(str(gameId),str(firstStateId)))

    #insert all the states
    for i in range(1,len(listaTrans)):
        saveTransitionToDb(cursor,listaTrans[i],gameId,i)

    return gameId

"""
Insert transition into DB and return the STATE_ID given for this transition
Transition consist of Terrain, Troops and action
"""
def saveTransitionToDb(cursor,transition,gameId,orderInGame):
    query = "INSERT INTO `state`" \
            "( `game_id`, `xi`, `yi`, `xf`, `yf`, `action`, `order_in_game`," \
            " `next_terminal`, `xa`, `ya`)" \
            " VALUES %s ; " \
            " "

    params = ([gameId,
              transition['Action']['Xi'],
              transition['Action']['Yi'],
              transition['Action']['Xf'],
              transition['Action']['Yf'],
              transition['Action']['action_type'],
              orderInGame,
              transition['next_terminal'],
              transition['Action']['Xa'],
              transition['Action']['Ya']],
              )
    print params
    #current_state_id	game_id	xi	yi	xf	yf	action	order_in_game	next_terminal

    #insert new state id with action and order return this state_id
    cursor.execute(query,params)
    idState = int(cursor.lastrowid)
    print 'Id del state ',idState

    #create all the cell given the state_id
    #id	can_move	x	y	terrain_type_id	troop_id
    # team_id	hp	state_id




    dictCell = jointCellTypes(transition)

    #Add to string (va1,val2 ... valX), (val1,val2,....), (val1,val2...valX)
    paramsString = ""
    for listCell in dictCell.values():
        listCell.append(idState)
        paramsString += (str(tuple(listCell))+' , ')
    paramsString = paramsString[:-2]
    print {'Can_move': 0, 'x': 1, 'y': 2, 'Terrain_type': 3, 'Troop': 4, 'Team': 5,
             'HP': 6}
    print 'Params to add ',paramsString


    #Add all cells to DB
    query = "INSERT INTO `cell_states` " \
            "(`can_move`, `x`, `y`, `terrain_type_id`, " \
            " `troop_id`, `team_id`, `hp`, `state_id`) VALUES %s ; "

    cursor.execute(query % paramsString)

    return idState

def jointCellTypes(transition):
    dictCell = {}
    order = {'Can_move': 0, 'x': 1, 'y': 2, 'Terrain_type': 3, 'Troop': 4, 'Team': 5,
             'HP': 6}

    defaultlist = [0 for i in range(7)]

    # join all cell types
    for cell in (transition['Troops'][0] + transition['Troops'][1] + transition['Terrain']):
        if not (dictCell.has_key((cell['x'], cell['y']))):
            dictCell[(cell['x'], cell['y'])] = copy(defaultlist)
        for key in cell:
            dictCell[(cell['x'], cell['y'])][order[key]] = cell[key]
    return dictCell

#TODO get all posible actions
def getLegalActions(state):
    pass

#TODO get next state from currentState, action
def doTransition(state,action):
    pass

"""
WE CALCULATE FOR RED PLAYER state["Troops"][0] = Red
Reward for state,action,nextState
For the first try the Network will estimate Q(s,a) as the EXPECTED COST from S taking action A.
The agent try to take the minium cost path (path to goal WIN STATE).

No enemys left = 0 (No cost Best case scenario)
No troops left = 1 (Maxium cost Worst case)
Else living penalty = 0.2 as an example (this make the agent end as quicly as posible)
"""
def calcReward(state,action,nextState):

    lostGame = 1
    win = 0
    livingPenalty = 0.2

    if len(nextState["Troops"][0]) == 0:
        return lostGame
    if len(nextState["Troops"][1]) == 0:
        return win
    else:
        return livingPenalty

def checkTerminal(state):
    if len(state["Troops"][0]) == 0:
        return True
    if len(state["Troops"][1]) == 0:
        return True
    else:
        return False

#TODO encodeAction to Json
def encodeActionJson():
    pass

def gameLoop(initialState,funStateAction,store=True,randomProb=0.5):
    #get initial game state
    game = []
    state = initialState

    nextState = None

    while not(checkTerminal(state)):

        #The python heap keep TUPLES (value,action) sorted by value like a heap
        heapAction = []
        accionesValidas = getLegalActions(state)

        #Random action or evaluation ?
        randomNumber = random.random()
        if random < randomProb:
            for action in accionesValidas:
                value = funStateAction(state,action)
                heapq.heappush(heapAction,(value,action))
            bestValue, bestAction = heapq.heappop(heapAction)
        else:
            bestAction = random.choice(accionesValidas)
            bestValue = -1

        nextState = doTransition(state,bestAction)
        reward = calcReward(state, bestAction, nextState)



        #append transition to game
        game.append(state)

    #place terminal in last transition

    if store:
        #open db and store game
        saveGameToDb(None,game,'GameComment')



def generateTestCase():

    #TODO create map independent from battle. A lot of innecesary stuff there and pygame is heavy

    #Generate map
    batalla = Battle.randomMap()

    initialState = batalla.getGameState()

    #Send agresive evaluation. Always try to attack
    #TODO add function
    evalfun = None

    gameLoop(initialState,evalfun)


def showTransition(transition):
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
        x = cell["x"]*tileDim
        y = cell["y"]*tileDim
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

            x = troop["x"] * tileDim
            y = troop["y"] * tileDim

            mask = np.zeros(base.shape)
            mask[y:y + img.shape[0], x:x + img.shape[1]] = img
            ms = np.bool_(mask[:, :, 3])
            base[ms] = mask[ms]

            mask = np.zeros(base.shape)
            mask[y:y + hpImg.shape[0], x:x + hpImg.shape[1]] = hpImg
            ms = np.bool_(mask[:,:,3])
            base[ms] = mask[ms]

            if not canMove:
                mask = np.zeros(base.shape)
                mask[y:y + wImg.shape[0], x:x + wImg.shape[1]] = wImg
                ms = np.bool_(mask[:, :, 3])
                base[ms] = mask[ms]

    #TODO add action representation

    plt.imshow(base)
    plt.show()



    pass


if __name__ == '__main__':
    # db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    # # cursor = db.cursor()
    # cursor = db.cursor (MySQLdb.cursors.DictCursor)
    # saveGameToDb(cursor,testGame,'Este es el primer das code')
    # # getGamefromDb(16,cursor)
    #
    # cursor.close()
    # db.commit()
    # db.close()
    generateTestCase()