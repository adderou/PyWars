#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils as utils
import main as main
import tools.agent as agent
import MySQLdb
import matplotlib.pyplot as plt
import numpy as np


if __name__ == "__main__":

    db = db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    cursor = db.cursor()
    cursor = db.cursor (MySQLdb.cursors.DictCursor)

    print "Generando gráficos de éxito de Red Neuronal vs. Agresivo Aleatorio"
    hidenUnitsList = [5,10,20,50,100,500]
    fixedUnit = 100
    trainingSamplesList = [10,50,100,500,5000,30000]
    fixedSample = 30000
    whoStartList = [-1,0,1]
    whoStartType = {-1:"Aleatorio",0:"Parte Red Neuronal",1:"Parte Agresivo Aleatorio"}
    iteraciones = 20
    blueAgent = agent.agresiveAgent()
    for whoStart in whoStartList:
        valuesArray = []
        for hidenUnits in hidenUnitsList:
            print "Probando con configuración: ", whoStartType[whoStart],"HidenUnits:",hidenUnits,"trainingSamples",fixedSample
            redAgent = main.createTrainedNeuralAgent(hidenUnits, fixedSample)
            values = utils.testAgentRed(cursor, redAgent, blueAgent, iteraciones)
            valuesArray.append(values["won"])
        plt.plot(hidenUnitsList,valuesArray)
        plt.title("Victorias Red Neuronal "+whoStartType[whoStart]+" y trainingSamples = "+fixedSample)
        plt.ylabel('% Ganado')
        plt.xlabel('Valor hiddenUnits')
        plt.show()
        for trainingSamples in trainingSamplesList:
            print "Probando con configuración: ", whoStartType[whoStart],"HidenUnits:",hidenUnits,"trainingSamples",fixedSample
            redAgent = main.createTrainedNeuralAgent(fixedUnit, trainingSamples)
            values = utils.testAgentRed(cursor, redAgent, blueAgent, iteraciones)
            valuesArray.append(values["won"])
        plt.plot(trainingSamplesList,valuesArray)
        plt.title("Victorias Red Neuronal "+whoStartType[whoStart]+" y hiddenUnits = "+fixedUnit)
        plt.ylabel('% Ganado')
        plt.xlabel('Valor hiddenUnits')
        plt.show()