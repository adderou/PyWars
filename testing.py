#!/usr/bin/env python
# -*- coding: utf-8 -*-

import utils as utils
import main as main
import tools.agent as agent
import MySQLdb


if __name__ == "__main__":

    db = db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    cursor = db.cursor()
    cursor = db.cursor (MySQLdb.cursors.DictCursor)

    print "Generando gráficos de éxito de Red Neuronal vs. Agresivo Aleatorio"
    hidenUnitsList = [50,100,1000]
    trainingSamplesList = [500,5000,30000]
    whoStartList = [-1,0,1]
    whoStartType = {-1:"Aleatorio",0:"Parte Red Neuronal",1:"Parte Agresivo Aleatorio"}
    iteraciones = 10
    valuesArray = []
    blueAgent = agent.agresiveAgent()
    for whoStart in whoStartList:
        print "Probando con configuración"
        valuesArray.append([])
        for hidenUnits in hidenUnitsList:
            print "Usando hidenUnits =",hidenUnits
            valuesArray[len(valuesArray)-1].append([])
            for trainingSamples in trainingSamplesList:
                print "Usando trainingSamples =",trainingSamples
                redAgent = main.createTrainedNeuralAgent(hidenUnits,trainingSamples)
                values = utils.testAgentRed(cursor,redAgent,blueAgent,iteraciones)
                valuesArray[len(valuesArray)-1][len(valuesArray[0])].append(values)
    print valuesArray