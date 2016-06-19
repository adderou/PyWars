from copy import copy

import time
from pandas import json
from threading import Thread

import MySQLdb

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
def getRandomGamesDb(number,cursor):
    gameList = []
    query = "SELECT `id` from `game` ORDER BY RAND() LIMIT %s ;"
    cursor.execute(query,(number,))
    result = cursor.fetchall()
    print result
    for row in result:
        ident = int(row['id'])
        print ident
        gameList.append(getGamefromDb(ident,cursor))
    return gameList


def getStateFromId(idState,cursor):
    ident = idState

    query = "SELECT `json` FROM `state`  WHERE `current_state_id` = %s ;"
    cursor.execute(query, (ident,))
    cellsState = cursor.fetchall()

    assert(len(cellsState) == 1)

    return parseState(cellsState[0])


def createThread(db,cursor,lista,inicio,salto):
    result = []
    thread = Thread(target=threadList, args=(db,cursor,lista,inicio,salto,result))
    return (thread, result)

def threadList(db,cursor,lista,inicio,salto,salida):
    indice = inicio
    while indice < len(lista):
        idState = int(lista[indice]['current_state_id'])
        salida.append(getStateFromId(idState, cursor))
        indice += salto
    cursor.close()
    db.close()
    return

#Without threads this takes 17.84 s for 10 samples
def getNStates(number,cursor,nthreads=1):
    states = []

    if number < nthreads:
        nthreads = number

    query = "SELECT `current_state_id` from `state` ORDER BY RAND() LIMIT %s ;"
    start = time.clock()
    cursor.execute(query,(number,))
    result = cursor.fetchall()
    end = time.clock()
    print "The query took ",end-start

    #start N conection as N threads

    stateList = []
    threads = []
    for idTh in range(nthreads):
        db = db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
        cursor = db.cursor()
        cursor = db.cursor(MySQLdb.cursors.DictCursor)
        threads.append(createThread(db,cursor, result, idTh, nthreads))

    for t in threads:
        t[0].start()
    for t in threads:
        t[0].join()
        stateList += t[1]

    return stateList


def getGamefromDb(idGame,cursor):

    query = "SELECT * FROM `state`  WHERE `game_id` = %s ORDER  BY `order_in_game` "
    print 'Getting ',idGame
    cursor.execute(query,(str(idGame),))
    result = cursor.fetchall()

    return [parseState(state) for state in result]

"""
Given a list of cells process all the states (must follow game_order) return gameList.
Game list is a list of states.
"""


def parseState(result):
    #load all
    return json.loads(result['json'])


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
    query = "INSERT INTO `state` (`json`, `game_id`,`order_in_game`) VALUES (%s, %s,%s ) ; "


    cursor.execute(query,(json.dumps(transition),str(gameId),str(orderInGame)))
    idState = int(cursor.lastrowid)
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


#FUNCITONS OF JSON RETRIVAL



#una funcion que gardar stateJson en database   getStateFromId, getGamefromDb, saveGameToDb

#una funcion que carge el json text de un texto