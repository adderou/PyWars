import multiprocessing

import numpy as np
import pylab as plt
import skimage
from skimage import io
from skimage.color import rgb2hsv, hsv2rgb
from skimage.transform import resize

from batleStub import virtualBattle
from tools.database import jointCellTypes

#Convencciones EL TROOPS[0] ES RED Y EL TROOPS[1] ES BLUE
from tools.model import getAllPosibleActions
from matplotlib.pyplot import plot, draw, show
import time


class gameSlider(object):
    def __init__(self, ax, imageList):
        self.ax = ax
        # ax.set_title('use scroll wheel to navigate images')

        self.data = imageList
        self.ind = 0
        self.maxImg = len(imageList)
        self.im = ax.imshow(showTransition(self.data[self.ind],True)[0])
        self.update()

    def onscroll(self, event):
        if event.button == 'up':
            self.ind = (self.ind - 1) % (self.maxImg)
        else:
            self.ind = (self.ind + 1) % (self.maxImg)

        self.update()

    def update(self):
        out = showTransition(self.data[self.ind],True)
        self.im.set_data(out[0])
        self.ax.set_title(out[1]+'slice %s' % self.ind)
        self.im.axes.figure.canvas.draw()


def showTransition(transition,dontShow=False,actionN=None):
    rutaTiles = "tiles/"
    rutaTroops="units/"
    dictMap = {0:'WaterOpen.png',
               1: 'Grass.png', 2: 'RoadInter.png',
               3: 'Forest.png', 4: "simpleMountain.png", 5: 'simpleRiver.png',
               6: 'BridgeHoriz.png'}
    dictTroop = {1:'Infantry.png',2:'RocketInf.png',
                 3:'SmTank.png',4:"LgTank.png",5:'Artillery.png',
                 6:'APC.png'}

    dictCell = jointCellTypes(transition)

    #Create empty image 10 * 16

    base = io.imread("tiles/"+dictMap[0])
    wImg = skimage.img_as_float(io.imread(rutaTroops + "wait.png"))
    maxRows = 10
    maxCols = 16
    tileDim = 64

    base = resize(base, (tileDim * maxRows, tileDim * maxCols))

    for cell in transition["Terrain"]:
        type = cell["Terrain_type"]
        x = cell["y"]*tileDim
        y = cell["x"]*tileDim
        img = io.imread(rutaTiles+dictMap[type])
        img = skimage.img_as_float(img)
        base[y:y + img.shape[0],x:x + img.shape[1]] = img


    #place troops
    for index,side in enumerate(["Red","Blue"]):
        for troop in transition["Troops"][index]:
            canMove = troop["Can_move"]
            hp = troop["HP"]
            type = troop["Troop"]
            img = skimage.img_as_float(io.imread(rutaTroops+side+dictTroop[type]))
            hpImg = skimage.img_as_float(io.imread(rutaTroops+str(hp/10)+".png"))

            x = troop["y"] * tileDim
            y = troop["x"] * tileDim

            mask = np.zeros(base.shape)
            mask[y:y + tileDim, x:x + tileDim] = img
            ms = np.bool_(mask[:, :, 3])
            base[ms] = mask[ms]

            mask = np.zeros(base.shape)
            mask[y:y + tileDim, x:x + tileDim] = hpImg
            ms = np.bool_(mask[:,:,3])
            base[ms] = mask[ms]

            if not canMove:
                mask = np.zeros(base.shape)
                mask[y:y + tileDim, x:x + tileDim] = wImg
                ms = np.bool_(mask[:, :, 3])
                base[ms] = mask[ms]
    stringOut = 'No action'
    if (transition.has_key('Action')):
        actionMask = np.zeros((base.shape[0],base.shape[1],3))

        if (transition['Action']['action_type']):
            x = transition['Action']["Ya"] * tileDim
            y = transition['Action']["Xa"] * tileDim
            actionMask[y:y + tileDim, x:x + tileDim] = [1,0,0]
        x = transition['Action']["Yf"] * tileDim
        y = transition['Action']["Xf"] * tileDim
        actionMask[y:y + tileDim, x:x + tileDim] = [0,0,1]
        x = transition['Action']["Yi"] * tileDim
        y = transition['Action']["Xi"] * tileDim
        actionMask[y:y + tileDim, x:x + tileDim] = [0,1,0]
        alpha = 0.6

        temp = rgb2hsv(base[:,:,:3])
        color_mask_hsv = rgb2hsv(actionMask)
        temp[..., 0] = color_mask_hsv[..., 0]
        temp[..., 1] = color_mask_hsv[..., 1] * alpha

        temp = hsv2rgb(temp)


        if (transition['Action']['action_type']):
            x = transition['Action']["Ya"] * tileDim
            y = transition['Action']["Xa"] * tileDim
            base[y:y + tileDim, x:x + tileDim,:3] = temp[y:y + tileDim, x:x + tileDim]

        x = transition['Action']["Yf"] * tileDim
        y = transition['Action']["Xf"] * tileDim
        base[y:y + tileDim, x:x + tileDim,:3] = temp[y:y + tileDim, x:x + tileDim]

        x = transition['Action']["Yi"] * tileDim
        y = transition['Action']["Xi"] * tileDim
        base[y:y + tileDim, x:x + tileDim,:3] = temp[y:y + tileDim, x:x + tileDim]

        stringOut = "Xi, Yi : " + str((transition['Action']["Xi"],
                                       transition['Action']["Yi"])) + " " +"Xf, Yf : " + \
                    str((transition['Action']["Xf"], transition['Action']["Yf"])) + " " +"Type : " +\
                    str(transition['Action']["action_type"]) + " ""Xa, Ya : " + str((transition['Action']["Xa"],
                                                                                     transition['Action']["Ya"])) + " "

    if dontShow:
        return (base,stringOut)

    job_for_another_core = multiprocessing.Process(target=plotInAnotherProcess, args=(stringOut,base,actionN))
    job_for_another_core.start()


def plotInAnotherProcess(string,image,actionN=None):
    if actionN:
        plt.suptitle("Action "+str(actionN)+" "+string)
    else:
        plt.suptitle(string)
    plt.imshow(image)
    plt.show()


def showGameScroll(gameList):


    imageList = [state for state in gameList]

    fig = plt.figure()
    ax = fig.add_subplot(111)

    tracker = gameSlider(ax, imageList)

    fig.canvas.mpl_connect('scroll_event', tracker.onscroll)
    plt.show()

def showActionsAgent(state,agent,turn):
    teamActing = 'Red' if turn == 0 else 'Blue'
    elseTeam = 'Red' if (1-turn) == 0 else 'Blue'

    baseBattle = virtualBattle.generateFromJson(state)
    baseBattle.initGame()
    accionesValidas = getAllPosibleActions(baseBattle, state, turn)

    #get all actions and value given agente
    actionsValue = []  # The python heap keep TUPLES (value,action) sorted by value like a heap

    for action in accionesValidas:
        value = agent.evalAction(state, action, turn)
        if type(value) == np.ndarray:
            value = value[0][0]
        cordsA = (action['Xi'], action['Yi'])
        cordsB = (action['Xf'], action['Yf'])
        cordsAttack = (action['Xa'], action['Ya'])

        troopActing = baseBattle.getTroopString(cordsA)

        rest = ""
        if action['action_type'] == 1:
            troopAttacked = baseBattle.getTroopString(cordsAttack)
            rest = 'and Attack '+elseTeam+" "+troopAttacked+str(cordsAttack)
        stringRep = teamActing+" "+troopActing+str(cordsA)+" moving to "+str(cordsB)+" "+rest
        actionsValue.append((value,stringRep,str(action)))
    actionsValue.sort()

    for elem in actionsValue:
        print "Value ",elem[0]," ",elem[1]

    showTransition(state)
    print "Test"

