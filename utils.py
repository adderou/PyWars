#
# X hacia abajo Y hacia la derecha centrado en la esquina sup izq
from copy import copy
from copy import deepcopy
from skimage import data, color, io, img_as_float
from skimage.color import rgb2hsv,hsv2rgb
import units
from map import Tile
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
from battle2 import Battle

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
# def getActionTroop(state, troop):
#     if troop['Can_move']:
#         return [{
#             'Xi': troop['x'],
#             'Yi': troop['y'],
#             'Xf': troop['x']+1,
#             'Yf': troop['y'],
#             'Xa': 0,
#             'Ya': 0,
#             'action_type': 0  # MoveAttack if value is 1, 0 just move.
#         }
#         ]
#     return []



#TODO get next state from currentState, action
"""
This function calculate next_state given current_state, action
THIS FUNCTION CAN MAKE ILEGAL ACTIONS must call a getlegal_actions() to be safe

ACTION_TYPE = 0 Just Move
ACTION_TYPE = 1 Move and Attack

"""
def doTransition(state,action):

    #after the action go to wait (troop["Can_move"] = 0)
    #if you just wait move from Xi to Xf = Xi
    state = deepcopy(state)


    currentTroop = None
    #get troop in cords
    for troop in (state["Troops"][0] +state["Troops"][1]) :
        if troop["x"] == action['Xi'] and troop["y"] == action['Yi']:
            currentTroop = troop

    current_team = currentTroop["Team"]

    #Could it move?
    try:
        assert(currentTroop["Can_move"])
    except Exception,e:
        print str(e)
    #move to Xf,Yf
    currentTroop['x'] = action['Xf']
    currentTroop['y'] = action['Yf']

    #Action_type = 0 just move so we end TROOP_TURN
    if action["action_type"] == 0:
        currentTroop["Can_move"] = 0


    #Action_type = 1 Attack_Move. Troop A in (Xi,Yi) attacks Troop B in (Xa,Ya)
    if action["action_type"] == 1:

        #get troop A
        troopA = currentTroop
        #getTroopB
        troopB = None


        try:
            troopB = [troop for troop in state["Troops"][1-current_team] if ((troop["x"] == action['Xa']) and (troop["y"] == action['Ya']))][0]
        except Exception,e:
            print (e)

        if troopA['x'] == troopB['x'] and troopA['y'] == troopB['y']:
            print "error"

        #get env

        terrAly = [terrain for terrain in state["Terrain"] if ((terrain["x"] == action['Xi']) and (terrain["y"] == action['Yi']))][0]
        terrEnemy = [terrain for terrain in state["Terrain"] if ((terrain["x"] == action['Xa']) and (terrain["y"] == action['Ya']))][0]

        atkEnv = Tile.defenseValues[terrAly['Terrain_type']]
        defEnv = Tile.defenseValues[terrEnemy['Terrain_type']]

        #Crear tropa simulada desde tropa jason
        attacker =  units.troopFromJson(troopA)
        defender = units.troopFromJson(troopB)

        #realiza calculo de ataque


        #End troop TURN so we wait (just the attacker wait)
        troopA["Can_move"] = 0

        #calculo damage defender
        defender.health -= attacker.getAttackDamage(defender, defEnv)
        #Si hp defensor es 0 eliminar de tropas
        if defender.health <= 0:
            state["Troops"][1-current_team].remove(troopB)
        else:
            troopB["HP"] = defender.health
            if not attacker.isArtilleryUnit and not defender.isArtilleryUnit:
                attacker.health -= defender.getRetaliatoryDamage(attacker, atkEnv)
                #si hp de atacante es cero eliminar de troops
                if attacker.health <= 0:
                    state["Troops"][current_team].remove(troopA)
                else:
                    troopA["HP"] = attacker.health

        #Hp actualizado




    return state

"""
WE CALCULATE FOR RED PLAYER state["Troops"][0] = Red
Reward for state,action,nextState
For the first try the Network will estimate Q(s,a) as the EXPECTED COST from S taking action A.
The agent try to take the minium cost path (path to goal WIN STATE).

No enemys left = 0 (No cost Best case scenario)
No troops left = 1 (Maxium cost Worst case)
Else living penalty = 0.2 as an example (this make the agent end as quicly as posible)
"""
def calcReward(state,action,nextState,currentTurn):

    #teams are 0 or 1
    aly = currentTurn
    enemy = 1-aly

    lostGame = 1
    win = 0
    livingPenalty = 0.2

    if len(nextState["Troops"][aly]) == 0:
        return lostGame
    if len(nextState["Troops"][enemy]) == 0:
        return win
    else:
        return livingPenalty

def checkTerminal(state,currentTurn):
    if len(state["Troops"][1-currentTurn]) == 0:
        return 1
    if len(state["Troops"][currentTurn]) == 0:
        return -1
    else:
        return 0

#TODO encodeAction to Json
def encodeActionJson():
    pass

def gameLoop(baseBattle,initialState,funStateAction,store=True,randomProb=0.5):

    #just to avoid infinite loops
    maxIter = 100

    #get initial game state
    game = []
    state = initialState
    baseBattle.setGameState(state)
    #ASEGURATE QUE EL EQUIPO INICIAL SEA RED
    baseBattle.activePlayer = baseBattle.teams[0]
    nextState = None

    #Is red or blue turn?
    activeTeam = 0

    while checkTerminal(state,activeTeam) == 0:

        for troop in state['Troops'][activeTeam]:
            heapAction = [] #The python heap keep TUPLES (value,action) sorted by value like a heap
            accionesValidas = baseBattle.getPossibleMoves((troop['x'], troop['y']))


            #Random action or evaluation ?
            randomNumber = random.random()
            if randomNumber < randomProb:
                for action in accionesValidas:
                    value = funStateAction(state,action)
                    heapq.heappush(heapAction,(value,action))
                bestValue, bestAction = heapq.heappop(heapAction)
            else:
                bestAction = random.choice(accionesValidas)
                bestValue = -1

            nextState = doTransition(state,bestAction)
            reward = calcReward(state, bestAction, nextState,activeTeam)

            #place if next state is win,lose or non terminal
            state['next_terminal'] = checkTerminal(nextState,activeTeam)
            #set Action to state
            state['Action'] = bestAction

            showTransition(state)

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
        saveGameToDb(None,game,'GameComment')

    return game



def generateTestCase(store=True):

    #TODO create map independent from battle. A lot of innecesary stuff there and pygame is heavy

    #Generate map
    batalla = Battle.randomMap()
    batalla.initGame()

    initialState = batalla.getGameState()

    #Send agresive evaluation. Always try to attack
    #If action type == 1 is an attack then eval to 1 else eval to 0
    evalfun = lambda state,action : 1*(action['action_type'])

    game = gameLoop(batalla,initialState,evalfun)

    print "Game generation ended ",len(game)," transitions"


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

        plt.suptitle(
            "Xi, Yi : " + str((transition['Action']["Xi"], transition['Action']["Yi"])) + " " +
            "Xf, Yf : " + str((transition['Action']["Xf"], transition['Action']["Yf"])) + " " +
            "Type : " + str(transition['Action']["action_type"]) + " "
            "Xa, Ya : " + str((transition['Action']["Xa"], transition['Action']["Ya"])) + " ")
    plt.imshow(base)
    plt.show()



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
    game = generateTestCase(False)

    for transition in game:
        showTransition(transition)
