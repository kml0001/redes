import argparse
from copy import deepcopy
from enum import Enum, auto
import random
import sys
import time

# Data structures:
# From Layer5 to Layer4
class Msg:
    msgSize = 20

    def __init__(self, data):
        self.data = data               

    def __str__(self):
        return 'Msg(data=%s)' % (self.data)

# From Layer4 to Layer3
class Pkt:
    def __init__(self, seqnum, acknum, checksum, payload):
        self.seqnum = seqnum            
        self.acknum = acknum            
        self.checksum = checksum        
        self.payload = payload          

    def __str__(self):
        return ('Pkt(seqnum=%s, acknum=%s, checksum=%s, payload=%s)'
                % (self.seqnum, self.acknum, self.checksum, self.payload))

# Entity A methods
class EntityA:
    def __init__(self, seqnumLimit):
        pass

    def output(self, msg):
        pass

    def input(self, packet):
        pass

    def timerInterrupt(self):
        pass

# Entity B methods
class EntityB:
    def __init__(self, seqnumLimit):
        pass

    def input(self, packet):
        pass

    def timerInterrupt(self):
        pass

# Callable functions:
def startTimer(callingEntity, increment):
    sim.startTimer(callingEntity, increment)

def stopTimer(callingEntity):
    sim.stopTimer(callingEntity)

def toLayer3(callingEntity, packet):
    sim.toLayer3(callingEntity, packet)

def toLayer5(callingEntity, message):
    sim.toLayer5(callingEntity, message)

def getTime(callingEntity):
    return sim.getTime(callingEntity)

# Network simulation:
class EventType(Enum):
    timerInterrupt = auto()
    fromLayer5 = auto()
    fromLayer3 = auto()

class Event:
    def __init__(self, eventTime, eventType, eventEntity, packet=None):
        self.eventTime = eventTime      
        self.eventType = eventType      
        self.eventEntity = eventEntity  
        self.packet = packet       

class Simulator:
    def __init__(self, options, cbA=None, cbB=None):
        self.nSim = 0
        self.nSimMax = options.num_msgs
        self.time = 0.000
        self.interarrivalTime = options.interarrivalTime
        self.lossProb = options.lossProb
        self.corruptProb = options.corruptProb
        self.seqnumLimit = options.seqnumLimit
        self.nToLayer3A = 0
        self.nToLayer3B = 0
        self.nLost = 0
        self.nCorrupt = 0
        self.nToLayer5A = 0
        self.nToLayer5B = 0

        if options.randomSeed is None:
            self.randomSeed = time.time_ns
        else:
            self.randomSeed = options.randomSeed
        random.seed(self.randomSeed)

        if self.seqnumLimit < 2:
            self.seqnumLimitNBits = 0
        else:
            self.seqnumLimitNBits = (self.seqnumLimit-1).bitLength()

        self.trace = options.trace
        self.toLayer5CallbackA = cbA
        self.toLayer5CallbackB = cbB

        self.entityA = EntityA(self.seqnumLimit)
        self.entityB = EntityB(self.seqnumLimit)
        self.events = []
        
    def main(options, cbA=None, cbB=None):
        global TRACE
        TRACE = options.trace

        global sim
        sim = Simulator(options, cbA, cbB)
        sim.run()