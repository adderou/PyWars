# X hacia abajo Y hacia la derecha centrado en la esquina sup izq
import heapq
import random
import MySQLdb
from batleStub import virtualBattle
from tools.agent import agresiveAgent, randomAgent, loadModel, neuralTD1Agent
from tools.database import getRandomGamesDb, saveGameToDb, getNStates, getStateFromId
from tools.model import doTransition, calcReward, checkTerminal, getTurnFromState, getAllPosibleActions
from tools.visualization import showGameScroll, showTransition, showActionsAgent

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



#NOW RANDOM PROB IS inside agent behavior DEFAULT IS 0
def gameLoop(baseBattle, initialState, agentRed,agentBlue,whoStart, store=True,cursor=None):

    #just to avoid infinite loops
    maxIter = 100
    #get initial game state
    game = []
    state = initialState
    baseBattle.setGameState(state)
    #ASEGURATE QUE EL EQUIPO INICIAL SEA RED
    baseBattle.activePlayer = baseBattle.teams[whoStart]
    nextState = None

    #Is red or blue turn?
    activeTeam = whoStart

    while checkTerminal(state, activeTeam) == 0:
        agent = agentRed if activeTeam == 0 else agentBlue
        accionesValidas = getAllPosibleActions(baseBattle,state, activeTeam)
        while len(accionesValidas) != 0:
            heapAction = [] #The python heap keep TUPLES (value,action) sorted by value like a heap

            #Random action or evaluation ?
            randomNumber = random.random()
            if randomNumber > agent.randomProb:
                for action in accionesValidas:

                    value = agent.evalAction(state, action,activeTeam)
                    # print value
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

            #Use this transition to update agent
            agent.observeTransition(state)

            state = nextState
            baseBattle.setGameState(state)

            #Calculate new state actions
            accionesValidas = getAllPosibleActions(baseBattle, state, activeTeam)


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



def generateGame(cursor,agentRed,agentBlue, store=True,fair=False):

    #Generate map
    batalla = virtualBattle.randomMap(fair)
    batalla.initGame()

    initialState = batalla.getGameState()

    whoStart = random.randint(0,1)
    game = gameLoop(batalla,initialState,agentRed,agentBlue,whoStart,store=store,cursor=cursor)

    # print "Game generation ended ",len(game)," transitions"
    return game


def testAgentRed(agentRed,agentBlue,nGames=40):
    won = 0
    lost = 0
    notEnded = 0
    for i in range(nGames):
        game = generateGame(cursor, agentRed, agentBlue, False,fair=True)
        endState = game[len(game) - 1]
        endGameResult = endState['next_terminal']
        endTurn = getTurnFromState(endState)

        if endGameResult == 0:
            notEnded += 1
        elif endGameResult == -1:
            if endTurn == 0:
                lost += 1
            else:
                won +=1
        elif endGameResult == 1:
            if endTurn == 0:
                won += 1
            else:
                lost += 1
    print ""
    print 'Results for RED ',str(agentRed)," vs ",str(agentBlue)," in ",str(nGames),' games'
    print ""
    print "%Won ",won*1.0/nGames
    print "%Lost ",lost*1.0/nGames
    print "Draws ",notEnded
    print ""

def analisisRedAgent(agentToTest,cursor,battleTest=True):
    if battleTest:
        #test agent vs agresive blue
        agresiveBlue = agresiveAgent()
        testAgentRed(agentToTest, agresiveBlue,40)

        # test agent vs random blue
        blue = randomAgent()
        testAgentRed(agentToTest, blue)

    #Test with a series of know cases
    testCases = [161304,263315]

    for idState in testCases:
        testState1 = getStateFromId(idState,cursor)
        showActionsAgent(testState1, agentToTest, 0)

if __name__ == '__main__':
    db = db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    cursor = db.cursor()
    cursor = db.cursor (MySQLdb.cursors.DictCursor)

    #Variables
    #Mode of this program
    # mode = "showRandomGames"
    # mode = "showBattle"
    mode='testAgent'
    # mode = 'IncrementalTraining'
    # mode = "generateRandomGames"

    #Agent settings

    agentRed = agresiveAgent()
    agentRed = loadModel("v2 11155.pkl")

    agentBlue = agresiveAgent()
    # agresiveBlue = loadNNTD1("tools/modelo TD1 500 iteraciones.pkl")

    #Do that thing

    if mode == "generateRandomGames":
        for i in range(10000):
            game = generateGame(cursor, agentRed, agentBlue, True)
            print "Game generation ended ",len(game)," transitions"

    elif mode == "showRandomGames":
        gameList = getRandomGamesDb(10, cursor)
        #If goes too slow use for state in game : showTransition(state) JUST FOR BETTER VISUALIZATION
        for game in gameList:
            showGameScroll(game)
    elif mode == 'IncrementalTraining':
        trainingGames = 100
        saveRedAgent = True
        agentRed.setLearning(True)
        #Here it uses only agent Red to maximize learning.
        for i in range(trainingGames):
            game = generateGame(cursor, agentRed, agentRed, store=False)
            print "Game generation ended ",len(game)," transitions"
        print "Incremental training seasion ended after "+str(trainingGames)+" now saving results"
        agentRed.setLearning(False)
        # Saving Red Model
        if saveRedAgent:
            agentRed.saveModel()
    elif mode == "showBattle":
        game = generateGame(cursor, agentRed, agentBlue, False,fair=True)
        showGameScroll(game)
    elif mode == 'testAgent':
        print "Testing agent Red "
        analisisRedAgent(agentRed,cursor,battleTest=True)





    #Close connection
    cursor.close()
    db.commit()
    db.close()