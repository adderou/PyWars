


def toInput(jsonState):
    return None

def getTrainingSet(bsim,evalFun):
    listaXtarget = []

    #get N states as Json
    listaJsonStates = []



    for jsonState in listaJsonStates:
        jsonNext = None

        reward = 0.2

        #See if states is almost endGame
        if jsonState['next_terminal'] != 0:
            #Reward WIn or Lose
            reward = 1 if jsonState['next_terminal'] == -1 else 0
            arrayRep = toInput(jsonState)

            listaXtarget.append((arrayRep,reward))

        else:
            #GEt next state
            jsonNext = 1
            turn = jsonState.turn
            bsim.set(jsonNext)
            bsim.setTurn(turn)

            arrayNext = toInput(jsonNext)

            tuplasValAction = []
            for action in bsim.getAllposibles():
                tuplasValAction.append(evalFun(arrayNext,action))
            bestTuple = max(tuplasValAction)

            target = reward + bestTuple[0]

            arrayRep = toInput(jsonState)
            listaXtarget.append((arrayRep,target))


    return listaXtarget



