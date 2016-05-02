#
# X hacia abajo Y hacia la derecha centrado en la esquina sup izq
from copy import copy

import MySQLdb

#eliminar game

#Convencciones EL TROOPS[0] ES BLUE Y EL TROOPS[1] ES RED


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
                        'action_type':0
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


def tupleToGame():
    pass

#nota 1 ya no es necesario first game id
def getGamefromDb(idGame,cursor):

    query = "SELECT * FROM `state`, `cell_states`   WHERE `state_id` = %s and `current_state_id` = %s" % idGame

    cursor.execute(query)
    result = cursor.fetchall()

    listGame = []
    currentId = -1
    currentRow = 0

    # current_state_id
    # game_id
    # xi
    # yi
    # xf
    # yf
    # action
    # order_in_game
    # next_terminal
    # xa
    # ya
    # id
    # can_move
    # x
    # y
    # terrain_type_id
    # troop_id
    # team_id
    # hp
    # state_id

    #get all rows in state,cell with game id
    for row in result:

        rowId = 0

        if rowId != currentId:
            #format action,nextTerminal, append to gameList
            pass

        #format cell things in currentRow object

        pass

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
    for i in range(1,len(game)):
        saveTransitionToDb(cursor,listaTrans[i],gameId,i)

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

    params = ([str(gameId),
              str(transition['Action']['Xi']),
              str(transition['Action']['Yi']),
              str(transition['Action']['Xf']),
              str(transition['Action']['Yf']),
              str(transition['Action']['action_type']),
              str(orderInGame),
              str(transition['next_terminal']),
              str(transition['Action']['Xa']),
              str(transition['Action']['Ya'])],
              )
    print params
    #current_state_id	game_id	xi	yi	xf	yf	action	order_in_game	next_terminal

    #insert new state id with action and order return this state_id
    cursor.execute(query,params)
    idState = int(cursor.lastrowid)
    print 'Id del state ',idState

    #create all the cell given the state_id
    #id	can_move	x	y	terrain_type_id	troop_id
    # team_id	hp	visibility	is_solid	state_id




    dictCell = jointCellTypes(transition)

    #Add to string (va1,val2 ... valX), (val1,val2,....), (val1,val2...valX)
    paramsString = ""
    for listCell in dictCell.values():
        listCell.append(idState)
        paramsString += (str(tuple(listCell))+' , ')
    paramsString = paramsString[:-2]
    print paramsString


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
    for cell in (transition['Troops'][0] + transition['Troops'][0] + transition['Terrain']):
        if not (dictCell.has_key((cell['x'], cell['y']))):
            dictCell[(cell['x'], cell['y'])] = copy(defaultlist)
        for key in cell:
            dictCell[(cell['x'], cell['y'])][order[key]] = cell[key]
    return dictCell

def showMap(transition):
    dictMap = {0:'WaterOpen.png',
               1: 'Grass.png', 2: 'RoadInter.png',
               3: 'Forest.png', 4: "Mountain.png", 5: 'RiverInter.png',
               6: 'BridgeHoriz.png'}
    dictTroop = {1:'Infantry.png',2:'RocketInf.png',
                 3:'SmTank.png',4:"LgTank.png",5:'Artillery.png',
                 6:'APC.png'}

    dictCell = jointCellTypes(transition)

    #Create empty image 10 * 16

    #for

    pass


if __name__ == '__main__':
    db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    cursor = db.cursor()
    saveGameToDb(cursor,testGame,'Este es el primer desde code')

    cursor.close()
    db.commit()
    db.close()