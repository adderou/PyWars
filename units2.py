# units.py
# by David Simon (dasimon@andrew.cmu.edu)
# Dec 2014

# Sprites from Advance Wars (Intelligent Systems, Nintendo)

import random
import os


def troopFromJson(jsonTroop):
    type = jsonTroop['Troop']
    hp = jsonTroop['HP']
    team = jsonTroop['Team']

    newTroop = troopClassTypeDict[type](team)
    newTroop.health = hp
    return newTroop
    pass

"""
It cant get x,y, Can_move of troop !!!!
"""
def troppToJson(troop):

    newTroop ={'x':None,
               'y':None,
               'Can_move':None,
               'Troop':troop.unitCode,
               'Team':troop.team,
               'HP':troop.health
                            }
    return newTroop

class Unit():
    """
    Represent a game unit.
    """
    type = 'Unit'
    unitCode = None
    # define unit movement points and movement cost for each terrain type
    movementPoints = 5
    movementCost = dict()
    # define base attack and defense for combat
    attack = 500
    defense = 50
    # define minimum and maximum taxicab distance for artillery
    isArtilleryUnit = False
    artilleryMinRange = 0
    artilleryMaxRange = 0
    # define strengths and weaknesses against other types
    attackModifiers = dict()
    # fields for game methods to use
    hasMoved = False
    canCapture = False
    colors = ["Red", "Blue", "Green", "Yellow"]

    def __init__(self, teamNum):
        """Create a unit for the given team at full health"""
        self.teamNum = teamNum
        self.team = Unit.colors[teamNum]
        self.health = 100


    def getAttackModifier(self, other):
        """Get the attack modifier for the given units"""
        if other.type in self.attackModifiers:
            return self.attackModifiers[other.type]
        else:
            # if there is no attack modifier for these types
            return 0

    def damageCalc(self, other, envFactor, attack):
        """Determine the damage based on the attack strength and health
         of this unit, the defense value of the enemy unit, the environmental
         defense factor of the defender, with some randomness factor"""
        # Determine base damage accounting for the health of the unit, with a
        # minimum of half of the base attack
        baseAttackDamage = attack + self.getAttackModifier(other)
        minimumDamageFactor = 0.5
        minimumBaseDamage = baseAttackDamage * minimumDamageFactor
        maxHealth = 100.0
        healthPercentage = self.health / maxHealth
        baseDamage = minimumBaseDamage + minimumBaseDamage * healthPercentage
        # account for defense
        defenseFactor = 0.1 * other.defense
        baseDefense = defenseFactor * envFactor
        baseDamage = int(baseDamage - baseDefense)
        # modify this by some random factor
        randomnessFactor = 0.2
        randomAllowance = int(round(randomnessFactor * baseDamage))
        damage = random.randint(baseDamage - randomAllowance,
                                      baseDamage + randomAllowance)
        return max(0, damage) # if the damage is less than 0, do no damage

    def getAttackDamage(self, other, defenderEnvFactor=0):
        """Get the damage dealt to a unit by an attacking unit"""
        return self.damageCalc(other, defenderEnvFactor, self.attack)

    def getRetaliatoryDamage(self, other, attackerEnvFactor=0):
        """Get the damage dealt to an attacking unit by a defending unit"""
        retaliationDamageFactor = 0.75
        # retaliation attacks should not do full damage
        retaliationAttack = int(round(retaliationDamageFactor * self.attack))
        return self.damageCalc(other, attackerEnvFactor, retaliationAttack)

    def __repr__(self):
        return self.type + '(%r)' % self.team

class Infantry(Unit):
    """
    Base unit. Has no attack modifiers
    """
    type = 'Infantry'
    movementPoints = 4
    unitCode = 1
    movementCost = {
        0: -1,
        1: 1,
        2: 0.8,
        3: 1.5,
        4: 2,
        5: 1.5,
        6: 0.8,
        7: 1.5
    }
    attack = 50
    defense = 10
    canCapture = True

class RocketInf(Unit):
    """
    Strong against Vehicles. Weak against Infantry.
    """
    type = 'RocketInf'
    unitCode = 2
    movementPoints = 5
    movementCost = {
        0: -1,
        1: 1,
        2: 0.8,
        3: 1.5,
        4: 2,
        5: 1.5,
        6: 0.8,
        7: 1.5
    }
    attack = 50
    defense = 5
    canCapture = True
    attackModifiers = {
        'Infantry': -5,
        'APC': 330,
        'SmTank': 30,
        'LgTank': 30,
        'Artillery': 30
    }

class APC(Unit):
    """
    Wheeled unit. Particularly effective against infantry.
    """
    type = 'APC'
    unitCode = 6
    movementPoints = 9
    movementCost = {
        0: -1,
        1: 1,
        2: 0.8,
        3: 2,
        4: 5,
        5: -1,
        6: 0.8,
        7: 3
    }
    attack = 60
    defense = 20
    attackModifiers = {
        'Infantry': 10,
        'RocketInf': 10
    }

class SmTank(Unit):
    type = 'SmTank'
    unitCode = 3
    movementPoints = 5
    movementCost = {
        0: -1,
        1: 1,
        2: 0.8,
        3: 2,
        4: 5,
        5: -1,
        6: 0.8,
        7: 3
    }
    attack = 80
    defense = 25

class LgTank(Unit):
    type = 'LgTank'
    unitCode = 4
    movementPoints = 4
    movementCost = {
        0: -1,
        1: 1,
        2: 0.8,
        3: 2,
        4: 5,
        5: -1,
        6: 0.8,
        7: 3
    }
    attack = 95
    defense = 50

class Artillery(Unit):
    type = 'Artillery'
    unitCode = 5
    movementPoints = 4
    movementCost = {
        0: -1,
        1: 1,
        2: 0.8,
        3: 2,
        4: 5,
        5: -1,
        6: 0.8,
        7: 3
    }
    isArtilleryUnit = True
    artilleryMinRange = 2
    artilleryMaxRange = 3
    attack = 85
    defense = 20


troopClassTypeDict = {1: Infantry,
                 2: RocketInf,
                 3: SmTank,
                 4: LgTank,
                 5: Artillery,
                 6:APC}
# 1	infantry
# 2	rocketinf
# 3	smtank
# 4	lgtank
# 5	artillery
# 6	apc