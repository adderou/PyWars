#!/usr/bin/env python
# -*- coding: utf-8 -*-

#Por hacer
#Mostrar acciones y su valor

#analisis de porcentaje victorias contra randon, agresivo,
#quizas es necesario cambiar la generacion de tropas a algo justo


#Visualizacion de acciones
#Mostrar lista ordenada de acciones por valor, pero parsear para mejor visibilidad (estilo rocket 2,3 to artillery 4,5)



import datetime
import pickle
import time
import random

import MySQLdb
import numpy as np
from tools.database import getNStates
from tools.model import doTransition, calcReward, getTurnFromState
import units2

class abstractAgent():
    def __init__(self):
        self.randomProb = 0
        self.isHuman = False
    # Allows to preselect one move to use it in humanAgent.
    def selectMove(self, troops, actionList, player):
        pass
    def evalAction(self, state, action, turn):
        raise NotImplemented
    #The default case is not used. This is used to train one step at the time
    def observeTransition(self,jsonState):
        pass
    def saveModel(self):
        pass
    #Load should make the calling instance a exact copy of the saved model not return the saved model
    def loadModel(self,filename):
        pass
    # Log action in human-readable text
    def actionToString(self,action,player):
        if action == None:
            print "Jugador",player,"termina su turno."
            return
        print "Jugador", player, "Mueve tropa en (",action["Xi"],",",action["Yi"],\
            ") a la posición (",action["Xf"],",",action["Yf"],")",
        #If attack
        if (action["action_type"] == 1):
            print "y ataca a la posición (",action["Xa"],",",action["Ya"],")."
        else :
            print "y no ataca."

class humanAgent(abstractAgent):
    def __init__(self):
        abstractAgent.__init__(self)
        self.randomProb = 0
        self.isHuman = True


    def getTroopFromCoords(self,troops,player,xCoord,yCoord,position):
        for troop in troops[player]:
            if (troop["x"],troop["y"]) == (xCoord,yCoord):
                return {"x":troop["x"],"y":troop["y"],"name":units2.troopClassTypeDict[troop["Troop"]].type, "pos":position,"HP":troop["HP"]}

    def getTroopList(self,troops,player,actionList):
        troopList = []
        lastCoordVisited = (-1,-1)
        i = -1
        for action in actionList:
            i = i+1
            actualCoords = (action["Xi"],action["Yi"]);
            if  actualCoords != lastCoordVisited:
                troopList.append(self.getTroopFromCoords(troops,player,action["Xi"], action["Yi"],i))
                lastCoordVisited = actualCoords
            else:
                continue
        return troopList

    def getMovesList(self,actionList,x,y):
        movesList = []
        for i in range(0,len(actionList)):
            action = actionList[i]
            if (action["Xi"],action["Yi"]) == (x,y) and action["action_type"] == 0:
                movesList.append({"x":action["Xf"],"y":action["Yf"],"pos":i})
        return movesList

    def getAttacksList(self,actionList,xi,yi,xf,yf):
        attacksList = []
        for i in range(0,len(actionList)):
            action = actionList[i]
            if (action["Xi"], action["Yi"]) == (xi, yi) and (action["Xf"], action["Yf"]) == (xf, yf):
                if action["action_type"] == 1:
                    attacksList.append({"attack": 1, "x": action["Xa"], "y": action["Ya"], "pos": i})
                else:
                    attacksList.append({"attack":0,"pos":i})
        return attacksList

    #Selects a move
    def selectMove(self,troops,actionList,player):
        selected = -1
        troopList = self.getTroopList(troops,player,actionList)
        # Select Troop
        while (selected < 1 or selected > len(troopList)):
            # Pass
            if selected == 0:
                return None
            print "Jugador",player,": Selecciona una tropa para mover, o ingresa 0 si quieres pasar:"
            i = 1
            for troop in troopList:
                print "------",i, ")",troop["name"]," ( HP = ",troop["HP"],") ubicada en (",troop["x"],",",troop["y"],")"
                i = i + 1
            selected = input()
            if selected < 0 or selected > len(actionList):
                print "Error: Ingresa un número entre 1 y",len(actionList),"."

        selectedTroop = troopList[selected-1]
        actionStartIndex = selectedTroop["pos"]
        xi = selectedTroop["x"]
        yi = selectedTroop["y"]
        movesList = self.getMovesList(actionList,xi,yi)
        selected = -1
        while (selected < 1 or selected > len(movesList)):
            if selected == 0:
                #Start again
                return self.selectMove(troops,actionList,player)
            print "Selecciona un movimiento para esa tropa, o ingresa 0 si quieres escoger otra:"
            i = 1
            for move in movesList:
                print "------", i, ")", "Moverse a la posición (",move["x"],",",move["y"],")"
                i = i + 1
            selected = input()
            if selected < 0 or selected > len(movesList):
                print "Error: Ingresa un número entre 1 y", len(movesList), "."

        selectedMove = movesList[selected-1]
        moveStartIndex = selectedMove["pos"]
        xf = selectedMove["x"]
        yf = selectedMove["y"]
        attacksList = self.getAttacksList(actionList,xi,yi,xf,yf)
        if len(attacksList) == 1:
            print "No es posible atacar desde acá, así que se moverá a esta posición."
            return actionList[attacksList[0]["pos"]]
        else:
            selected = -1
            while (selected < 1 or selected > len(attacksList)):
                if selected == 0:
                    #Start again
                    return self.selectMove(troops,actionList,player)
                print "Selecciona si la tropa atacará, o ingresa 0 si quieres escoger otra tropa:"
                i = 1
                for attack in attacksList:
                    print "------", i, ")",
                    if attack["attack"] == 1:
                        attackedTroop = self.getTroopFromCoords(troops, 1 - player, attack["x"], attack["y"], -1)
                        print "Atacar al",attackedTroop["name"],"( HP = ",attackedTroop["HP"],") enemigo en la posición (",attack["x"],",",attack["y"],")"
                    else:
                        print "No atacar."
                    i = i + 1
                selected = input()
                if selected < 0 or selected > len(attacksList):
                    print "Error: Ingresa un número entre 1 y", len(attacksList), "."
            selectedAttack = attacksList[selected-1]
            return actionList[selectedAttack["pos"]]


class randomAgent(abstractAgent):
    def __init__(self):
        abstractAgent.__init__(self)
        self.randomProb = 1.0

# Send agresive evaluation. Always try to attack
# If action type == 1 is an attack then eval to 1 else eval to 0
class agresiveAgent(abstractAgent):
    def __init__(self):
        abstractAgent.__init__(self)
        self.randomProb = 0
        pass
    def evalAction(self, state, action,turn):
        coef = -1 if action['action_type'] == 1 else 1
        return  coef * random.randint(1,10)

class neuralTD1Agent(abstractAgent):
    def __init__(self,inputLength,hidenUnits):
        abstractAgent.__init__(self)
        self.randomProb = 0

        #input lenghth
        self.inputLength = inputLength
        #hidden units
        self.hiddenUnits = hidenUnits

        #Learning rate (like in gradient descent )
        self.alpha = 0.4

        self.discountFactor = 1

        #lambda for update elegibility traces
        self.parlambda = 0.9

        #Weights of NN
        self.weight_InHide = np.random.rand(self.hiddenUnits,self.inputLength+1)/10
        self.weight_HideOut = np.random.rand(1,self.hiddenUnits+1)/10

        # elegibility traces (used for training )
        self.e_InHide = np.zeros((self.hiddenUnits,self.inputLength+1))
        self.e_HideOut = np.zeros((1,self.hiddenUnits+1))

        #N of trained json states used
        self.timesTrained = 0



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

    def observeTransition(self,jsonState):
        self.trainOneStep(jsonState)
        self.timesTrained += 1

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
            realOutput = reward + self.discountFactor*self.eval(nextStateArray)

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

    """
    This jsonState must have an asocieated action otherwise it will make an error
    """
    def trainOneStep(self,jsonState):
        usedAction = jsonState['Action']
        jsonNext = doTransition(jsonState, usedAction)
        turn = getTurnFromState(jsonState)
        reward = calcReward(jsonState, usedAction, jsonNext, turn)

        arrayCurrent = self.toInput(jsonState)
        arrayNext = self.toInput(jsonNext)
        # See if states is almost endGame
        if jsonState['next_terminal'] != 0:
            self.backpropagate(arrayCurrent, arrayNext, reward, True)
        else:
            self.backpropagate(arrayCurrent, arrayNext, reward, False)


    def trainBatchN(self,cursor,numberOfStatesToTrain,justTerminal=False):

        #get N states as Json
        start = time.clock()
        print "Getting training samples "

        # Special query to get only terminal states
        if justTerminal:
            query = "SELECT `current_state_id` from `state` WHERE `current_state_id` = 1 ORDER BY RAND() LIMIT %s ;"
            listaJsonStates = getNStates(numberOfStatesToTrain,cursor,query = query,nthreads=10)
        else:
            listaJsonStates = getNStates(numberOfStatesToTrain, cursor, nthreads=10)

        print "Training samples ready it took ",time.clock()-start


        start = time.clock()
        print "Training started "
        for jsonState in listaJsonStates:
            self.trainOneStep(jsonState)

        end = time.clock()
        print "Model trained in ", end - start, " trained with ", numberOfStatesToTrain
        print "Average time by train sample ", (end - start) * 1.0 / numberOfStatesToTrain
    def saveModel(self):
        #Here should be somekind of parse of the parameters to make name = str(parameter) + str(date)
        name = "Td1 NoReward JUSTTERMINAL LR 04 hd" + str(self.hiddenUnits) + " trainedStates " + str(
            self.timesTrained) + " date " + datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y").replace(".",
                                                                                                           " ").replace(
            ":", " ")
        output = open(name + '.pkl', 'wb')
        pickle.dump(self, output, -1)

#Do something more adaptable
def loadModel(filepath):
    output = open(filepath, 'rb')
    model = pickle.load(output)
    if isinstance(model,neuralTD1Agent):
        try:
            model.isHuman = False
            model.timesTrained = model.timesTrained + 0
        except:
            model.timesTrained = 0
    output.close()
    return model

if __name__ == "__main__":
    #Start database conection
    db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    cursor = db.cursor (MySQLdb.cursors.DictCursor)


    #Set up game inputs and hiden layers
    hidenUnits = 1000
    trainingSamples = 30000
    nnAgent = neuralTD1Agent(3042, hidenUnits)


    #Train with N states
    nnAgent.trainBatchN(cursor, trainingSamples,justTerminal=True)

    # Save Model
    nnAgent.saveModel()

    cursor.close()
    db.commit()
    db.close()
    pass






