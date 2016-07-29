#!/usr/bin/env python
# -*- coding: utf-8 -*-

import agent
import utils
def set_player(number):
    p = -1
    while (p not in [1, 2, 3]):
        print "Selecciona el tipo de jugador 1:"
        print "1) Humano"
        print "2) Computador - Juego Aleatorio"
        print "3) Computador - Juego Ofensivo Aleatorio"
        print "Pronto ) Computador - Juego Red Neuronal"
        p = input()
        if (p not in [1,2,3]):
            print "Error, ingresa un número del 1 al 3"
        print ""
        print ""
    return p

agents = [agent.humanAgent(),agent.randomAgent(),agent.agresiveAgent()]

if __name__ == "__main__":
    print "Bienvenido a PyWars"
    print "---------------------"
    p1 = set_player(1) - 1
    p2 = set_player(2) - 1
    agent1 = agents[p1]
    agent2 = agents[p2]
    utils.generateGame(None,agent1,agent2,fair=True,store=False,consoleMode=True)



