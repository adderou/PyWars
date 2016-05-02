#
# X hacia abajo Y hacia la derecha centrado en la esquina sup izq
from copy import copy

import MySQLdb


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

    query = "SELECT * FROM `state`, `cell_states`   WHERE `state_id` = %s and `current_state_id` = %s" \
            "ORDER  BY `order_in_game` "

    cursor.execute(query,(str(idGame),str(idGame)))
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
    # team_id	hp	visibility	is_solid	state_id




    dictCell = jointCellTypes(transition)

    #Add to string (va1,val2 ... valX), (val1,val2,....), (val1,val2...valX)
    paramsString = ""
    for listCell in dictCell.values():
        listCell.append(idState)
        paramsString += (str(tuple(listCell))+' , ')
    paramsString = paramsString[:-2]
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
    # cursor = db.cursor()
    cursor = db.cursor (MySQLdb.cursors.DictCursor)
    # saveGameToDb(cursor,testGame,'Este es el primer desde code')
    getGamefromDb(16,cursor)

    cursor.close()
    db.commit()
    db.close()