import argparse
from copy import deepcopy
from enum import Enum, auto
import random
import sys
import time
from binascii import crc32

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

# EntityA methods
class EntityA:
    # Este método se llama una vez antes de que se llamen otros métodos EntityA.
    # Se utiliza para la inicialización.
    # seqnumLimit es el número máx de valores de secuencia distintos que puede utilizar el protocolo.
    def __init__(self, seqnumLimit):
        # Inicialización de variables de estado (constantes)
        self.output = 0
        self.input = 1
        self.timerInterrupt = 2
        self.waitTime = 10.0
        
        # Inicialización de variables de estado (específicas del protocolo)
        self.layer5Msgs = []
        self.bit = 0
        self.sentPkt = None
        self.handleEvent = self.handleEventWaitForCall 

    # Este método se llama desde layer5 cuando hay datos para enviar.
    # Agrega el msg a la cola y llama al método handleEvent con el evento "output".
    def output(self, msg):
        self.layer5Msgs.append(msg)
        self.handleEvent(self.output)

    # Este método se llama desde layer3 cuando llega un paquete a layer4 en EntityA.
    # Llama al método handleEvent con el evento "input" y pasa el paquete como argumento.
    def input(self, packet):
        self.handleEvent(self.input, packet)

    # Este método se llama cuando el temporizador A expira.
    # Llama al método handleEvent con el evento "timerInterrupt".
    def timerInterrupt(self):
        self.handleEvent(self.timerInterrupt)
        pass
    
    # Este método maneja eventos cuando EntityA está esperando una llamada.
    # Los eventos pueden ser "output", "input" o "timerInterrupt". 
    # Dependiendo del evento, realiza acciones específicas.
    def handleEventWaitForCall(self, e, arg=None):
        if e == self.output:
            # Verifica si hay mensajes para enviar
            if not self.layer5Msgs:
                return
            
            # Toma el 1er msg de la lista.
            m = self.layer5Msgs.pop(0)
            
            # Crea un paquete con información específica y el contenido del msg
            p = Pkt(self.bit, 0, 0, m.data)
            
            #Inserta un checksum al paquete
            pktInsertChecksum(p)
            
            # Envía el paquete a layer3
            toLayer3(self, p)
            
            # Guarda el paquete enviado
            self.sentPkt = p
            
            # Inicia un temporizador con un tiempo de espera definido
            startTimer(self, self.waitTime)
            
            # Establece el próximo estado del manejador de eventos
            self.handleEvent = self.handleEventWaitForAck
            
        elif e == self.input:
            # No realiza ninguna acción específica en este caso
            pass
        
        elif e == self.timerInterrupt:
            # Ignora el evento de temporizador y emite un msg si TRACE es mayor que 0
            if TRACE > 0:
                print("EntityA: ignoring unexpected timeout")
                
        else:
            # Para otros eventos llama a la función para manejar eventos desconocidos
            self.unknownEvent(e)

# Este método maneja eventos cuando la EntityA está esperando un acknowledgment (ack)
# Los eventos pueden ser "output", "input" o "timerInterrupt".
# Dependiendo del evento realiza acciones específicas.
def handleEventWaitForAck(self, e, arg=None):
    if e == self.output:
        # No realiza ninguna acción específica en este caso.
        pass
    
    elif e == self.input:
        # Obtiene el paquete recibido como argumento.
        p = arg
        
        # Verifica si el paquete está corrupto o el acknum no coincide con el bit esperado
        if pktIsCorrupt(p) or p.acknum != self.bit:
            # Ignora el paquete en caso de corrupción o acknum incorrecto-
            return
        
        # Detiene el temporizador.
        stopTimer(self)
        
        # Cambia el bit esperado (alternado entre 0 y 1)
        self.bit = 1 - self.bit
        
        # Establece el próximo estado del manejador de eventos
        self.handleEvent = self.handleEventWaitForCall
        
        # Llama al manejador de eventos para el evento de salida
        self.handleEvent(self.output)
        
    elif e == self.timerInterrupt:
        # Reenvía el pkt previamente enviado a layer3
        toLayer3(self, self.sentPkt)
        
        # Inicia un temporizador con un tiempo de espera definido
        startTimer(self, self.waitTime)
        
    else:
        # Para otros eventos llama a la función para manejar eventos desconocidos.
        self.unknownEvent(e)
        
# Este método imprime un msg indicando que se recibió un evento desconocido.
def unknownEvent(self, e):
    print(f'EntityA: ignoring unknown event {e}')


# EntityB methods.
class EntityB:
    # Este método inicializa la entidad B. 
    # La entidad B tiene una variable expectingBit que indica el próximo bit esperado.
    def __init__(self, seqnum_limit):
        self.expectingBit = 0
        pass

    # Este método se llama desde layer3 cuando llega un paquete a layer4 en EntityB.
    # Verifica si el paquete es válido, y si no lo es, envía un ack negativo. Si es válido,
    # entrega el mensaje a layer5 y envía un ack positivo.
    def input(self, packet):
        # print(f'B received: {packet}')
        if (packet.seqnum != self.expectingBit
                or pktIsCorrupt(packet)):
            p = Pkt(0, 1 - self.expectingBit, 0, packet.payload)
            pktInsertChecksum(p)
            toLayer3(self, p)
        else:
            toLayer5(self, Msg(packet.payload))
            # Ack.
            p = Pkt(0, self.expectingBit, 0, packet.payload)
            pktInsertChecksum(p)
            toLayer3(self, p)
            #
            self.expectingBit = 1 - self.expectingBit

    # Este método se llama cuando el temporizador de B expira. En este caso, no realiza ninguna acción.
    def timerInterrupt(self):
        pass


# Estas funciones se encargan de calcular el checksum de un paquete, insertar el
# checksum en el paquete y verificar si un paquete está corrupto.
# Estos métodos y funciones se utilizan para implementar la lógica del protocolo de bits alternados,
# donde A espera un ack antes de enviar el siguiente paquete y B envía un ack por cada paquete recibido correctamente.

def pktComputeChecksum(packet):
    crc = 0
    crc = crc32(packet.seqnum.to_bytes(4, byteorder='big'), crc)
    crc = crc32(packet.acknum.to_bytes(4, byteorder='big'), crc)
    crc = crc32(packet.payload, crc)
    return crc


def pktInsertChecksum(packet):
    packet.checksum = pktComputeChecksum(packet)


def pktIsCorrupt(packet):
    return pktComputeChecksum(packet) != packet.checksum

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