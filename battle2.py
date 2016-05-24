# battle.py
# by David Simon (dasimon@andrew.cmu.edu)
# Dec 2014

# Based on Advance Wars (Intelligent Systems, Nintendo)

import copy
from map2 import *
from units2 import *


class Team():
    colors = ["Red", "Blue", "Green", "Yellow"]
    def __init__(self, teamNumber, funds, cursorCoords, camRect):
        self.teamNumber = teamNumber
        self.funds = funds
        self.color = Team.colors[teamNumber]
        self.heldObjectives = []
        self.units = set()
        self.cursorCoords = cursorCoords
        self.camLeft = camRect[0]
        self.camTop = camRect[1]
        self.camRight = camRect[2]
        self.camBottom = camRect[3]


class Battle():
    """Main gametype"""

    shopTypes = {
        1: Infantry,
        2: RocketInf,
        3: APC,
        4: SmTank,
        5: LgTank,
        6: Artillery
    }


    shopCosts = {
        1: 1000,
        2: 3000,
        3: 4000,
        4: 7000,
        5: 16000,
        6: 6000
    }

    @staticmethod
    def loadUnits(unitString):
        if len(unitString) == 0: return []
        units = []
        unitIdentifiers = unitString.splitlines()
        for i in xrange(len(unitIdentifiers)):
            thisUnitStr = unitIdentifiers[i]
            thisUnitList = thisUnitStr.split()
            team = int(thisUnitList[0])
            type = int(thisUnitList[1])
            rowAndCol = thisUnitList[2].split(',')
            coords = (int(rowAndCol[0]), int(rowAndCol[1]))
            units.append((team, type, coords))
        return units

    @staticmethod
    def fromFile(path):
        with open(path, "rt") as input:
            save = input.read()
        saveContents = save.split('\n*\n')
        mapString = saveContents[0]
        numPlayers = int(saveContents[1])
        initialFunds = int(saveContents[2])
        unitString = saveContents[3]
        map = mapString
        units = Battle.loadUnits(unitString)
        return Battle(map, numPlayers, initialFunds, units)


    @staticmethod
    def randomMap():
        baseMap = Battle.generateRandomBaseMap()
        numPlayers = 2
        initialFunds = 0
        unitString, used = Battle.generateUnits(baseMap)
        finalMap = Battle.populateMap(baseMap,used)
        map = Battle.generateMapString(finalMap)
        units = Battle.loadUnits(unitString)
        return Battle(map, numPlayers, initialFunds, units)

    @staticmethod
    def generateRandomBaseMap():
        map = []
        for i in range(10):
            mapLine = []
            for j in range(16):
                mapLine.append("1")
            map.append(mapLine)
        # Map Headquarters
        map[2][2] = "00"
        map[7][13] = "10"
        return map

    @staticmethod
    def generateMapString(map):
        mapString = ""
        for i in range(10):
            for j in range(16):
                mapString += str(map[i][j])+(3-len(map[i][j]))*" "
            mapString+="\n"
        return mapString

    @staticmethod
    def populateMap(map,used):
        #Rivers
        x = random.randint(0, 9)
        y = random.randint(0, 15)
        d = 1
        while x not in [0,9] and y not in [0,15]:
            possible = [(max(0,x-d),y),(min(9,x+d),y),(x,max(0,y-d)),(x,min(15,y+d))]
            x,y = possible[random.randint(0,3)]
            counter = 0
            while ((x,y) not in used) and (x,y) in [(2,2), (7,13)] and counter<5:
                x, y = possible[random.randint(0, 3)]
                counter +=1
            map[x][y] = "5"
            used.append((x,y))

        #mountains
        x = random.randint(0, 9)
        y = random.randint(0, 15)
        d = 1
        while x not in [0,9] and y not in [0,15]:
            possible = [(max(0,x-d),y),(min(9,x+d),y),(x,max(0,y-d)),(x,min(15,y+d))]
            x,y = possible[random.randint(0,3)]
            counter = 0
            while ((x,y) not in used) and (x,y) in [(2,2), (7,13)] and counter<5:
                x, y = possible[random.randint(0, 3)]
                counter +=1
            map[x][y] = "4"
            used.append((x,y))

        #Forests

        x = random.randint(0, 9)
        y = random.randint(0, 15)
        d = 1
        while x not in [0, 9] and y not in [0, 15]:
            possible = [(max(0, x - d), y), (min(9, x + d), y), (x, max(0, y - d)), (x, min(15, y + d))]
            x, y = possible[random.randint(0, 3)]
            counter = 0
            while ((x, y) not in used) and (x, y) in [(2, 2), (7, 13)] and counter < 5:
                x, y = possible[random.randint(0, 3)]
                counter += 1
            map[x][y] = "3"
            used.append((x, y))

        #roads
        x = random.randint(0, 9)
        y = random.randint(0, 15)
        d = 1
        while x not in [0, 9] and y not in [0, 15]:
            possible = [(max(0, x - d), y), (min(9, x + d), y), (x, max(0, y - d)), (x, min(15, y + d))]
            x, y = possible[random.randint(0, 3)]
            counter = 0
            while ((x, y) not in used) and (x, y) in [(2, 2), (7, 13)] and counter < 5:
                x, y = possible[random.randint(0, 3)]
                counter += 1
            map[x][y] = "2"
            used.append((x, y))

        return map
    @staticmethod
    def generateUnits(map):
        unitString = ""
        team1Size = random.randint(1,3)
        team2Size = random.randint(1,3)
        used = []
        x = random.randint(0, 9)
        y = random.randint(0, 15)
        d = 2
        while team1Size>0:
            unitType = random.randint(1,6)
            x = random.randint(max(0, x - d), min(9, x + d))
            y = random.randint(max(0, y - d), min(15, y + d))
            while ((x,y) in used):
                x = random.randint(max(0,x-d),min(9,x+d))
                y = random.randint(max(0,y-d), min(15,y+d))
            used.append((x,y))
            unitString += str(0)+" "+str(unitType)+" "+str(x)+","+str(y)+"\n"
            team1Size-=1
        while team2Size > 0:
            unitType = random.randint(1, 6)
            x = random.randint(max(0, x - d), min(9, x + d))
            y = random.randint(max(0, y - d), min(15, y + d))
            while ((x,y) in used):
                x = random.randint(max(0, x - d), min(9, x + d))
                y = random.randint(max(0, y - d), min(15, y + d))
            used.append((x,y))
            unitString += str(1) + " " + str(unitType) + " " + str(x) + "," + str(y) + "\n"
            team2Size -= 1
        return unitString, used

    ##################################################################
    # Game setup
    ##################################################################

    def __init__(self, map, numPlayers, initialFunds=5000, initialUnits=[]):
        # super(Battle, self).__init__('Battle')
        self.map = Map(map)
        self.rows, self.cols = self.map.rows, self.map.cols
        self.unitSpace = self.getUnitSpace()
        self.numPlayers = numPlayers
        self.initialFunds = initialFunds
        self.teams = self.createTeams()
        self.placeInitialUnits(initialUnits)
        # print self.getGameState()

    def initGraphics(self):
        self.camWidth = 16
        self.camHeight = 10
        self.camLeft, self.camTop = (0, 0)
        self.screenTopLeft = (0, 128)
        self.screenDisplaySize = (1024, 640)
        self.screenSize = (self.map.cols*Tile.size, self.map.rows*Tile.size)
        self.camTop = 0
        self.camLeft = 0
        self.camBottom = 10
        self.camRight = 16

    def getUnitSpace(self):
        """Create an empty 2D list the size of the map"""
        contents = []
        for row in xrange(self.rows):
            contents += [[None] * self.cols]
        return contents

    def getHQCoords(self, teamNum):
        map = self.map.map
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                tile = map[row][col]
                if (isinstance(tile, Objective) and
                    tile.typeNum == 0 and
                    tile.teamNum == teamNum):
                    return (row, col)

    def getCamRect(self, hqCoords):
        row, col = hqCoords
        camWidth = 16
        camHeight = 10
        camRight = col + camWidth/2
        camLeft = camRight - camWidth
        camBottom = row + camHeight/2
        camTop = camBottom - camHeight
        while camLeft < 0:
            camLeft += 1
            camRight += 1
        while camRight > self.cols:
            camLeft -= 1
            camRight -= 1
        while camTop < 0:
            camTop += 1
            camBottom += 1
        while camBottom > self.rows:
            camTop -= 1
            camBottom -= 1
        camRect = [camLeft, camTop, camRight, camBottom]
        return camRect

    def createTeams(self):
        """Create the appropriate number of teams, each with the initial
        amount of funds"""
        teams = []
        for teamNumber in xrange(self.numPlayers):
            hqCoords = self.getHQCoords(teamNumber)
            camRect = self.getCamRect(hqCoords)
            teams.append(Team(teamNumber, self.initialFunds, hqCoords, camRect))
        return teams

    def placeInitialUnits(self, initialUnits):
        """Add the initial units to the unit space"""
        for item in initialUnits:
            teamNum, typeNum, coords = item
            type = Battle.shopTypes[typeNum]
            team = self.teams[teamNum]
            row, col = coords
            unit = type(teamNum)
            self.unitSpace[row][col] = unit
            team.units.add(unit)


    def initGame(self):
        """Set up initial game conditions"""
        self.gameIsOver = False
        self.eliminatedPlayers = set()
        self.contextMenuIsOpen = False
        self.contextMenuOptions = [False, False]
        self.inAttackMode = False
        self.shopIsOpen = False
        self.shopCoords = None
        self.attackerCoords = None
        self.attackKey = '2'
        self.unitIsSelected = False
        self.captureKey = '3'
        self.getHeldObjectives()
        firstPlayer = random.randrange(self.numPlayers)
        self.playerIndex = firstPlayer
        self.activePlayer = self.teams[self.playerIndex]
        self.activeUnits = copy.copy(self.activePlayer.units)
        self.movementRange = set()
        self.cursorCoords = (0, 0)
        self.targetCoords = None
        self.targets = []
        self.targetIndex = 0
        self.beginTurn()

    def getHeldObjectives(self):
        """Add each objective to the heldObjectives list of the team that
        holds it"""
        map = self.map
        for row in xrange(map.rows):
            for col in xrange(map.cols):
                tile = self.map.map[row][col]
                if isinstance(tile, Objective) and tile.teamNum != 4:
                    holdingTeam = self.teams[tile.teamNum]
                    holdingTeam.heldObjectives.append(tile)

    ##################################################################
    # Gameplay methods
    ##################################################################

    def beginTurn(self):
        """Start the turn of the active player"""
        self.activePlayer = self.teams[self.playerIndex]
        additionalFundsPerBuilding = 1000
        newFunds = (additionalFundsPerBuilding *
                     len(self.activePlayer.heldObjectives))
        self.activePlayer.funds += newFunds
        self.activeUnits = copy.copy(self.activePlayer.units)
        self.placeCursor(self.activePlayer.cursorCoords)
        self.camLeft = self.activePlayer.camLeft
        self.camRight = self.activePlayer.camRight
        self.camTop = self.activePlayer.camTop
        self.camBottom = self.activePlayer.camBottom
        self.selection = None
        self.clearMovementRange()
        self.restoreUnitHealth()

    def placeCursor(self, coords):
        """Move the cursor to a new location, redrawing the old and new
        locations"""
        oldRow, oldCol = self.cursorCoords
        self.cursorCoords = coords

    def placeUnit(self, team, type, coords):
        """Place and draw the given unit in the given tile"""
        row, col = coords
        teamColor = self.teams[team].color
        self.unitSpace[row][col] = type(team)

    def adjustCam(self):
        row, col = self.cursorCoords
        if col < self.camLeft:
            self.camLeft -= 1
            self.camRight -= 1
        elif col >= self.camRight:
            self.camLeft += 1
            self.camRight += 1
        if row < self.camTop:
            self.camTop -= 1
            self.camBottom -= 1
        elif row >= self.camBottom:
            self.camTop += 1
            self.camBottom += 1

    def moveCursor(self, dir):
        """Handle motion of the cursor by the arrow keys"""
        oldRow, oldCol = self.cursorCoords
        newRow, newCol = None, None
        # get new Coords
        if dir == 'left':
            newRow, newCol = oldRow, oldCol - 1
        elif dir == 'right':
            newRow, newCol = oldRow, oldCol + 1
        elif dir == 'up':
            newRow, newCol = oldRow - 1, oldCol
        elif dir == 'down':
            newRow, newCol = oldRow + 1, oldCol
        # if new coords are legal, change cursorCoords
        if 0 <= newRow < self.rows and 0 <= newCol < self.cols:
            coords = (newRow, newCol)
            self.placeCursor(coords)
            self.adjustCam()

    def getNextTiles(self, map, unit, coords):
        """Return a list of the tiles adjacent to (row, col), sorted by
        movement cost for the given unit"""
        row, col = coords
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        nextTiles = []
        for (dRow, dCol) in directions:
            nextRow = row + dRow
            nextCol = col + dCol
            nextTiles.append((nextRow, nextCol))
        return nextTiles

    def isBlocked(self, coords):
        """Return true if (row, col) is occupied by an enemy team"""
        row, col = coords
        unit = self.unitSpace[row][col]

        activeTeam = self.activePlayer.color
        return (unit != None) and (unit.team != activeTeam)

    def movementRangeHelperFunction(self, map, unit, coords, movementPoints):
        """Do a weighted floodfill method to populate the movement range"""
        row, col = coords
        if not (0 <= row < self.rows and 0 <= col < self.cols): return
        terrainType = map[row][col].terrainType
        movementCost = unit.movementCost[terrainType]
        pointsAfterMove = movementPoints - movementCost
        if (pointsAfterMove > 0 and movementCost != -1 and
            not self.isBlocked(coords)):
            self.movementRange.add(coords)
            for newCoords in self.getNextTiles(map, unit, coords):
                self.movementRangeHelperFunction(map, unit,
                                                 newCoords, pointsAfterMove)

    def getMovementRangeOf(self, coords):
        """Calculate movement range from the current selection"""
        map = self.map.map
        row, col = coords
        unit = self.unitSpace[row][col]
        movementPoints = unit.movementPoints
        self.movementRange.add(coords)
        for newCoords in self.getNextTiles(map, unit, coords):
                    self.movementRangeHelperFunction(map, unit,
                                                     newCoords,
                                                     movementPoints)

    def getMovementRange(self):
        self.getMovementRangeOf(self.selection)

    def clearMovementRange(self):
        """Clear the movement range and redrawing all of the tiles"""
        oldMovementRange = self.movementRange
        self.movementRange = set()


    def checkArtilleryRange(self, unit, coords):
        maxDistance = unit.artilleryMaxRange
        minDistance = unit.artilleryMinRange
        cRow, cCol = coords
        for row in xrange(cRow - maxDistance, cRow + maxDistance + 1):
            for col in xrange(cCol - maxDistance, cCol + maxDistance + 1):
                taxicabDistance = abs(row - cRow) + abs(col - cCol)
                if ((0 <= row < self.rows) and (0 <= col < self.cols) and
                    self.isBlocked((row, col)) and
                    (minDistance <= taxicabDistance <= maxDistance)):
                    return True
        return False

    def checkAdjacent(self, coords):
        cRow, cCol = coords
        adjacentDir = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for (dRow, dCol) in adjacentDir:
            newRow, newCol = cRow + dRow, cCol + dCol
            if ((0 <= newRow < self.rows and 0 <= newCol < self.cols) and
                self.isBlocked((newRow, newCol))):
                return True
        return False

    def canAttack(self, unit, coords, distanceMoved):
        if unit.isArtilleryUnit and distanceMoved == 0:
            return self.checkArtilleryRange(unit, coords)
        elif not unit.isArtilleryUnit:
            return self.checkAdjacent(coords)
        else:
            return False

    def canCapture(self, unit, coords):
        row, col = coords
        tile = self.map.map[row][col]
        return (unit.canCapture and isinstance(tile, Objective) and
                (unit.team != tile.team))

    def openContextMenu(self, unit, coords, distanceMoved):
        self.contextMenuIsOpen = True
        self.contextMenuOptions = [False, False]
        self.attackKey = None
        self.captureKey = None
        key = 1
        if self.canAttack(unit, coords, distanceMoved):
            key += 1
            self.attackKey = str(key)
            self.contextMenuOptions[0] = True
        if self.canCapture(unit, coords):
            key += 1
            self.captureKey = str(key)
            self.contextMenuOptions[1] = True

    def moveUnit(self, old, new):
        """Move the unit from one tile to another"""
        oldRow, oldCol = old
        newRow, newCol = new
        if self.unitSpace[newRow][newCol] == None:
            unit = self.unitSpace[oldRow][oldCol]
            self.unitSpace[newRow][newCol] = unit
            self.unitSpace[oldRow][oldCol] = None
        self.selection = None
        self.clearMovementRange()

    def updateSelection(self):
        """Handle the changing selection"""
        row, col = self.cursorCoords
        if self.selection == None:
            # get the selection and movement range
            row, col = self.cursorCoords
            unit = self.unitSpace[row][col]
            tile = self.map.map[row][col]
            if ((unit != None) and
                (unit.team == self.activePlayer.color) and
                (unit in self.activeUnits)):
                self.unitIsSelected = True
                self.selection = self.cursorCoords
                self.getMovementRange()
            elif ((unit == None) and isinstance(tile, Objective) and
                  (tile.team == self.activePlayer.color) and
                  (tile.type == 'Factory')):
                self.shopIsOpen = True
                self.shopCoords = self.cursorCoords
        elif (self.cursorCoords in self.movementRange and
              (self.unitSpace[row][col] == None or
               self.selection == self.cursorCoords)):
            self.oldCoords = oldRow, oldCol = self.selection
            self.newCoords = newRow, newCol = self.cursorCoords
            self.moveUnit(self.selection, self.cursorCoords)
            taxicabDistance = abs(newRow - oldRow) + abs(newCol - oldCol)
            unit = self.unitSpace[newRow][newCol]
            self.openContextMenu(unit, self.newCoords, taxicabDistance)

    def clearSelection(self):
        """Clear the selection and the movement range"""
        self.unitIsSelected = False
        self.selection = None
        self.clearMovementRange()

    def restoreObjectives(self):
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                unit = self.unitSpace[row][col]
                objective = self.map.map[row][col]
                if (isinstance(objective, Objective) and
                    (unit == None or unit.team == objective.team)):
                    objective.health = Objective.baseHealth

    def restoreUnitHealth(self):
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                unit = self.unitSpace[row][col]
                objective = self.map.map[row][col]
                if ((unit != None) and isinstance(objective, Objective) and
                    (unit.team == objective.team) and
                    (unit.team == self.activePlayer.color)):
                    unit.health += 50
                    if unit.health > 100:
                        unit.health = 100

    def endTurn(self):
        """Store the current player's cursor position and begin the next
        player's turn"""
        self.restoreObjectives()
        for unit in self.activePlayer.units:
            unit.hasMoved = False
        self.activePlayer.cursorCoords = self.cursorCoords
        self.activePlayer.camLeft = self.camLeft
        self.activePlayer.camRight = self.camRight
        self.activePlayer.camTop = self.camTop
        self.activePlayer.camBottom = self.camBottom
        self.playerIndex += 1
        while self.playerIndex in self.eliminatedPlayers:
            self.playerIndex += 1
        self.playerIndex %= self.numPlayers
        self.beginTurn()

    def wait(self):
        row, col = self.newCoords
        unit = self.unitSpace[row][col]
        unit.hasMoved = True
        self.unitIsSelected = False
        self.activeUnits.remove(unit)
        self.contextMenuIsOpen = False

    def revertMove(self):
        self.moveUnit(self.newCoords, self.oldCoords)
        self.contextMenuIsOpen = False
        self.unitIsSelected = False

    def endGame(self):
        self.gameIsOver = True
        self.winner = None
        for team in self.teams:
            if team.teamNumber not in self.eliminatedPlayers:
                self.winner = team

    def removeTeam(self, teamNum):
        self.eliminatedPlayers.add(teamNum)
        for row in xrange(self.rows):
            for col in xrange(self.cols):
                unit = self.unitSpace[row][col]
                tile = self.map.map[row][col]
                if unit != None and unit.teamNum == teamNum:
                    self.unitSpace[row][col] = None
                if isinstance(tile, Objective) and tile.teamNum == teamNum:
                    typeNum = tile.typeNum
                    if typeNum == 0: typeNum = 1 # replace HQ with a city
                    self.map.map[row][col] = Objective((4, typeNum))
        if self.numPlayers - len(self.eliminatedPlayers) == 1:
            self.endGame()

    def capture(self):
        row, col = self.newCoords
        objective = self.map.map[row][col]
        unit = self.unitSpace[row][col]
        objective.health -= (unit.health / 10)
        if objective.health <= 0:
            oldTeam = objective.teamNum
            if oldTeam != 4:
                self.teams[oldTeam].heldObjectives.remove(objective)
            team = unit.teamNum
            type = objective.typeNum
            if type == 0:
                self.removeTeam(oldTeam)
                type = 1 # don't allow a team to gain more than one HQ
            newObjective = Objective((team, type))
            self.map.map[row][col] = newObjective
            self.activePlayer.heldObjectives.append(newObjective)
        self.wait()

    def moveTarget(self):
        newCoords = self.targets[self.targetIndex]
        self.targetCoords = newCoords


    def getArtilleryInPlace(self,unit,cords):
        cRow, cCol = cords
        maxDistance = unit.artilleryMaxRange
        minDistance = unit.artilleryMinRange
        for row in xrange(cRow - maxDistance, cRow + maxDistance + 1):
            for col in xrange(cCol - maxDistance, cCol + maxDistance + 1):
                taxicabDistance = abs(row - cRow) + abs(col - cCol)
                if ((0 <= row < self.rows) and (0 <= col < self.cols) and
                    self.isBlocked((row, col)) and
                    (minDistance <= taxicabDistance <= maxDistance)):
                    self.targets.append((row, col))
    def getArtilleryTargetsIn(self,coords):
        cRow, cCol = coords
        unit = self.unitSpace[cRow][cCol]
        return self.getArtilleryInPlace(unit,coords)

    def getArtilleryTargets(self):
        self.getArtilleryTargetsIn(self.attackerCoords)

    def getTargetsIn(self,coords):
        cRow, cCol = coords
        directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
        for (dRow, dCol) in directions:
            row = cRow + dRow
            col = cCol + dCol
            if ((0 <= row < self.rows) and (0 <= col < self.cols) and
                self.isBlocked((row, col))):
                self.targets.append((row, col))

    def getTargets(self):
        self.getTargetsIn(self.attackerCoords)

    def removeUnit(self, coords):
        row, col = coords
        unit = self.unitSpace[row][col]
        team = self.teams[unit.teamNum]
        team.units.remove(unit)
        self.unitSpace[row][col] = None
        if len(team.units) == 0:
            self.removeTeam(unit.teamNum)

    def attack(self):
        atkRow, atkCol = self.attackerCoords
        defRow, defCol = self.targets[self.targetIndex]
        attacker = self.unitSpace[atkRow][atkCol]
        defender = self.unitSpace[defRow][defCol]
        atkEnv = self.map.defense[atkRow][atkCol]
        defEnv = self.map.defense[defRow][defCol]
        defender.health -= attacker.getAttackDamage(defender, defEnv)
        if defender.health <= 0:
            self.removeUnit((defRow, defCol))
        elif not attacker.isArtilleryUnit and not defender.isArtilleryUnit:
            attacker.health -= defender.getRetaliatoryDamage(attacker, atkEnv)
            if attacker.health <= 0:
                self.removeUnit((atkRow, atkCol))
        self.unitIsSelected = False
        self.contextMenuIsOpen = False
        if self.unitSpace[atkRow][atkCol] != None:
            self.wait()

    def contextMenu(self, keyName):
        if keyName == '1':
            self.wait()
        elif keyName == self.attackKey:
            self.enterAttackMode()
        elif keyName == self.captureKey:
            self.capture()
        elif keyName == 'x':
            self.revertMove()

    def enterAttackMode(self):
        self.inAttackMode = True
        row, col = self.attackerCoords = self.cursorCoords
        self.targets = []
        self.targetIndex = 0
        unit = self.unitSpace[row][col]
        if unit.isArtilleryUnit:
            self.getArtilleryTargets()
        else:
            self.getTargets()
        self.moveTarget()

    def attackMode(self, keyName):
        if keyName == 'right':
            self.targetIndex += 1
            self.targetIndex %= len(self.targets)
            self.moveTarget()
        elif keyName == 'left':
            self.targetIndex -= 1
            self.targetIndex %= len(self.targets)
            self.moveTarget()
        elif keyName == 'z':
            self.inAttackMode = False
            self.attack()

        elif keyName == 'x':
            self.inAttackMode = False


    def shop(self, keyName):
        if keyName == 'x':
            self.shopIsOpen = False
        elif keyName in '123456':
            num = int(keyName)
            cost = Battle.shopCosts[num]
            if cost <= self.activePlayer.funds:
                self.activePlayer.funds -= cost
                type = Battle.shopTypes[num]
                team = self.activePlayer.teamNumber
                self.placeUnit(team, type, self.shopCoords)
                row, col = self.shopCoords
                unit = self.unitSpace[row][col]
                self.activePlayer.units.add(unit)
                unit.hasMoved = True
                self.shopIsOpen = False



    ##################################################################
    # Drawing to "screen" surface
    ##################################################################



    ##################################################################
    # Drawing to the screen
    ##################################################################



    def getGameState(self):
        invShopTypes = {
            'Infantry': 1,
            'RocketInf': 2,
            'APC': 3,
            'SmTank': 4,
            'LgTank': 5,
            'Artillery': 6
        }
        GameState = {}
        GameState['Terrain'] = []
        map = self.map.contents
        print map
        units = self.unitSpace
        # Terrain
        for i in range(len(map)):
            for j in range(len(map[i])):
                print map[i]
                terrainType = map[i][j] if (int == type(map[i][j])) else  map[i][j][1]
                GameState['Terrain'].append({'x': i, 'y': j, 'Terrain_type': terrainType})
        # Troops
        GameState['Troops'] = [[],[]]
        for i in range(len(units)):
            for j in range(len(units[i])):
                if units[i][j] is not None:
                    num = 0 if (units[i][j].team == 'Blue') else 1
                    GameState['Troops'][num].append(
                        {'x': i,
                         'y': j,
                         'Team': num,
                         'Troop': invShopTypes[units[i][j].type],
                         'Can_move': (1-int(units[i][j].hasMoved)),
                         'HP': units[i][j].health
                         })
        return GameState

    def getPossibleMoves(self, position):
        # print position
        xi,yi = position
        unit = self.unitSpace[xi][yi]
        moves = []
        # Conseguir todas las posibles posiciones
        self.getMovementRangeOf((xi,yi))
        movRange = self.movementRange
        # Para cada posible posicion
        for mov in movRange:
            entry = {}
            xf,yf = mov
            entry['Xi'] = xi
            entry['Yi'] = yi
            entry['Xf'] = xf
            entry['Yf'] = yf
            entry['Xa'] = 0
            entry['Ya'] = 0
            entry['action_type'] = 0
            # Agregarla a la lista como movimiento
            # Para cada posicion del mapa
            moves.append(entry)
            if unit.isArtilleryUnit:
                self.getArtilleryInPlace(unit,mov)
            else:
                self.getTargetsIn(mov)
            for coords in self.targets:
                xa,ya = coords
                taxicabDistance = abs(yi - ya) + abs(xi - xa)
                # Si hay algun enemigo en ella, agregar a la lista como movimiento
                if self.canAttack(unit,coords,taxicabDistance):
                    entry = {}
                    entry['Xi'] = xi
                    entry['Yi'] = yi
                    entry['Xf'] = xf
                    entry['Yf'] = yf
                    entry['Xa'] = xa
                    entry['Ya'] = ya
                    entry['action_type'] = 1
                    moves.append(entry)
        # Devolver lista de movimientos posibles
        return moves

    #Seteamos ahora las tropas del json en el modelo
    def setGameState(self,gameState):
        #Delete Unitspace
        self.unitSpace = self.getUnitSpace()
        initialUnits = []
        #Para cada equipo
        for i in range(len(gameState['Troops'])):
            for j in range(len(gameState['Troops'][i])):
                currentTroop = gameState['Troops'][i][j]
                item = (i, currentTroop['Troop'], (currentTroop['y'],currentTroop['x']))
                initialUnits.append(item)
        self.placeInitialUnits(initialUnits)

# testMapPath = os.path.join('maps', 'gauntlet.tpm')
# a = Battle.fromFile(testMapPath)
# a.run()
