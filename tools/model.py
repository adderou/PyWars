from copy import deepcopy

import units
from map import Tile

def getTurnFromState(jsonState):
    usedAction = jsonState['Action']
    return [troop for troop in (jsonState['Troops'][0] + jsonState['Troops'][1]) if troop['x'] == usedAction['Xi'] and troop['y'] == usedAction['Yi']][0]['Team']

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
    assert(currentTroop["Can_move"])
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


        troopB = [troop for troop in state["Troops"][1-current_team] if ((troop["x"] == action['Xa']) and (troop["y"] == action['Ya']))][0]



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
        # print "Game ended in WIN for ",currentTurn
        return 1
    if len(state["Troops"][currentTurn]) == 0:
        # print "Game ended in LOSE for ", currentTurn
        return -1
    else:
        return 0

def getAllPosibleActions(baseBattle,state,turn):
    allPosible = []
    for troop in state['Troops'][turn]:
        if troop['Can_move'] == 0:
            continue
        allPosible += baseBattle.getPossibleMoves((troop['x'], troop['y']),turn)
    return allPosible


