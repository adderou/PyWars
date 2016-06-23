#Por hacer
#Mostrar acciones y su valor

#analisis de porcentaje victorias contra randon, agresivo,
#quizas es necesario cambiar la generacion de tropas a algo justo


#Visualizacion de acciones
#Mostrar lista ordenada de acciones por valor, pero parsear para mejor visibilidad (estilo rocket 2,3 to artillery 4,5)



import datetime
import pickle
import time

import MySQLdb
import numpy as np

from tools.database import getNStates
from tools.model import doTransition, calcReward, getTurnFromState


class randomAgent():
    def __init__(self):
        self.randomProb = 1.0
    def evalAction(self,state,action,turn):
        return 0

# Send agresive evaluation. Always try to attack
# If action type == 1 is an attack then eval to 1 else eval to 0
class agresiveAgent():
    def __init__(self):
        self.randomProb = 0
        pass
    def evalAction(self, state, action,turn):
        return -1 * (action['action_type'])

class neuralTD1Agent():
    def __init__(self,inputLength,hidenUnits):

        self.randomProb = 0

        #input lenghth
        self.inputLength = inputLength
        #hidden units
        self.hiddenUnits = hidenUnits

        #Learning rate (like in gradient descent )
        self.alpha = 0.2

        #Discount factor of the model = 1 so its not explicitly included in the ecuations

        #lambda for update elegibility traces
        self.parlambda = 0.9

        #Weights of NN
        self.weight_InHide = np.random.rand(self.hiddenUnits,self.inputLength+1)/10
        self.weight_HideOut = np.random.rand(1,self.hiddenUnits+1)/10

        # elegibility traces (used for training )
        self.e_InHide = np.zeros((self.hiddenUnits,self.inputLength+1))
        self.e_HideOut = np.zeros((1,self.hiddenUnits+1))



    """
    There are 16 * 10 cells
    each cell has binary arrays with values (1 present - 0 absent)
    The binary array contains
    7 vars for troop type [noTroop,Infantry,mech,SmallTank,LgTank,artillery,APC]
    1 var float 0-1 for hp (hp*1.0/100)
    2 vars for team [RedTroop,BlueTroop]
    2 vars for waiting [canMove,Waiting]
    7 vars terrain [Sea,Plain,Road,Forest,Mountain,River,Bridge]

    And in the end append [remainingRed,remainingBlue]
    16*10* ( 19 ) + 2 = 3042
    X*Y* ( arrayPos )
    [noTroop,Infantry,mech,SmallTank,LgTank,artillery,APC,HP,RedTroop,BlueTroop,Waiting,canMove,Sea,Plain,Road,Forest,Mountain,River,Bridge] * 16 * 10
    +
    [remainingRed,remainingBlue]
    """
    def toInput(self,jsonState):
        arrayRep = np.zeros((self.inputLength,1))
        for troop in (jsonState['Troops'][0] + jsonState['Troops'][1]) :
            cordinate = 19*troop['y']+troop['x']*16*19
            arrayRep[cordinate+troop['Troop']] = 1
            arrayRep[cordinate + 7] = troop['HP']*1.0/100
            #Team 0 Red team 1 Blue
            arrayRep[cordinate + 8 + troop['Troop']] = 1
            #Can_move 0 is Waiting 1 can move
            arrayRep[cordinate + 10 + troop['Can_move']] = 1

        for terrain in jsonState['Terrain']:
            cordinate = 19 * terrain['y'] + terrain['x'] * 16 * 19
            arrayRep[cordinate + 12 + terrain['Terrain_type']] = 1
            pass
        #Remember to append reamingn troops red,blue
        arrayRep[10*16*19 ] = len(jsonState['Troops'][0])
        arrayRep[10*16*19 + 1] = len(jsonState['Troops'][1])
        return arrayRep

    #Return cost given state,action,turn 1 worst cost (lose), 0 best cost (win)
    def evalAction(self,state,action,turn):
        nextState = doTransition(state,action)

        costForRed = self.eval(self.toInput(nextState))
        #If red try to minimize expected cost
        if turn == 0:
            return costForRed
        #if blue maximize expected cost of red
        else:
            return -1.0 * costForRed

    def eval(self,stateArray):

        inputWithBias = np.append(stateArray,1).reshape(self.inputLength+1,1)

        hideSum = np.dot(self.weight_InHide, inputWithBias)
        hide = 1.0 / (1 + np.exp(-hideSum))

        hidenOutWithBias = np.append(hide,1).reshape(self.hiddenUnits+1,1)
        outputSum = np.dot(self.weight_HideOut, hidenOutWithBias)
        output = 1.0 / (1 + np.exp(-outputSum))
        return output

    # ejemplo https://github.com/harpribot/TD-Gammon/blob/master/BackPropogation.m
    def backpropagate(self,stateArray,nextStateArray,reward,endNext):
        #use target = rewardEndGame
        if endNext:
            realOutput = reward
        #use target = reward + Val(nextState)
        else:
            realOutput = reward + self.eval(nextStateArray)

        expectedOut = self.eval(stateArray)

        #update weights of nn
        self.weight_InHide = self.weight_InHide + self.alpha * (realOutput - expectedOut) * self.e_InHide
        self.weight_HideOut = self.weight_HideOut + self.alpha * (realOutput - expectedOut) * self.e_HideOut

        #get out from hiden layer to calcculate eligibility
        inputWithBias = np.append(nextStateArray, 1).reshape(self.inputLength+1, 1)
        hideSum = np.dot(self.weight_InHide, inputWithBias)
        hide = 1.0 / (1 + np.exp(-hideSum))
        hidenOutWithBias = np.append(hide, 1).reshape(self.hiddenUnits+1, 1)

        nextOutputAfterChange = self.eval(nextStateArray)

        # update elegibility traces
        # newEligibility = lambda * old + grad(Value) respect to corresponding weight
        self.e_HideOut = self.parlambda * self.e_HideOut + (1 - nextOutputAfterChange) * nextOutputAfterChange * np.transpose(hidenOutWithBias)
        self.e_InHide = self.parlambda * self.e_InHide + ((1 - nextOutputAfterChange)* nextOutputAfterChange) * np.dot(((1 - hide)* hide)* self.weight_HideOut[0,:-1].reshape((self.hiddenUnits,1)), np.transpose(inputWithBias))

        pass

    def trainBatchN(self,cursor,numberOfStatesToTrain):

        #get N states as Json
        start = time.clock()
        print "Getting training samples "
        listaJsonStates = getNStates(numberOfStatesToTrain, cursor,nthreads=10)
        print "Training samples ready it took ",time.clock()-start


        start = time.clock()
        print "Training started "
        for jsonState in listaJsonStates:
            usedAction = jsonState['Action']
            jsonNext = doTransition(jsonState, usedAction)
            turn = getTurnFromState(jsonState)
            reward = calcReward(jsonState, usedAction, jsonNext, turn)

            arrayCurrent = self.toInput(jsonState)
            arrayNext = self.toInput(jsonNext)
            #See if states is almost endGame
            if jsonState['next_terminal'] != 0:
                self.backpropagate(arrayCurrent,arrayNext,reward,True)
            else:
                self.backpropagate(arrayCurrent, arrayNext, reward, False)
        end = time.clock()
        print "Model trained in ", end - start, " trained with ", trainingSamples
        print "Average time by train sample ", (end - start) * 1.0 / trainingSamples

    def train1Step(self,currentState,reward,nextState,terminal):
        arrayCurrent = self.toInput(currentState)
        arrayNext = self.toInput(nextState)

        self.backpropagate(arrayCurrent, arrayNext, reward, terminal)


def loadNNTD1(filepath):
    output = open(filepath, 'rb')
    objecttNN = pickle.load(output)
    output.close()
    return objecttNN

if __name__ == "__main__":
    #Start database conection
    db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    cursor = db.cursor (MySQLdb.cursors.DictCursor)

    hidenUnits = 50
    #Set up game inputs and hiden layers
    nnAgent = neuralTD1Agent(3042, hidenUnits)

    trainingSamples = 1000


    #Train with N states
    nnAgent.trainBatchN(cursor, trainingSamples)

    #Test in 10 games again random heuristic



    # Save Model
    name = "ModeloTD1 hd"+str(hidenUnits)+" samples "+str(trainingSamples)+" date "+datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y").replace(".", " ").replace(":", " ")
    output = open(name + '.pkl', 'wb')
    pickle.dump(nnAgent, output, -1)

    cursor.close()
    db.commit()
    db.close()
    pass






