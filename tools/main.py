#!/usr/bin/env python
# -*- coding: utf-8 -*-

import agent
import utils
import MySQLdb

def set_player(number):
    p = -1
    while (p not in [1, 2, 3, 4]):
        print "Selecciona el tipo de jugador 1:"
        print "1) Humano"
        print "2) Computador - Juego Aleatorio"
        print "3) Computador - Juego Ofensivo Aleatorio"
        print "4) Computador - Juego Red Neuronal"
        p = input()
        if (p not in [1 ,2 ,3 ,4]):
            print "Error, ingresa un número del 1 al 4"
        print ""
        print ""
    return p

def createTrainedNeuralAgent():
    print "Entrenando Agente"
    db = MySQLdb.connect("200.9.100.170", "bayes", "yesbayesyes", "bayes")
    cursor = db.cursor (MySQLdb.cursors.DictCursor)


    #Set up game inputs and hiden layers
    hidenUnits = 100
    trainingSamples = 30000
    nnAgent = agent.neuralTD1Agent(3042, hidenUnits)


    #Train with N states
    nnAgent.trainBatchN(cursor, trainingSamples,justTerminal=True)

    # Save Model
    nnAgent.saveModel()

    cursor.close()
    db.commit()
    db.close()
    return nnAgent

agents = [agent.humanAgent,agent.randomAgent,agent.agresiveAgent,createTrainedNeuralAgent] # Neural Network Missing

if __name__ == "__main__":
    print "Bienvenido a PyWars"
    print "---------------------"
    p1 = set_player(1) - 1
    p2 = set_player(2) - 1
    agent1 = agents[p1]()
    agent2 = agents[p2]()
    utils.generateGame(None,agent1,agent2,fair=True,store=False,consoleMode=True)



