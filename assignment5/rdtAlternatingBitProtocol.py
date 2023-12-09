# Esta es la version del laboratorio Alternating-Bit-Protocol.

# El emisor divide los datos en tramas, cada una marcada con un bit de control.
# Después de enviar una trama, espera la confirmación (ACK) del receptor antes de enviar la siguiente,
# alternando el bit de control. El receptor verifica la integridad de cada trama y envía un ACK.
# Si se detectan errores, se envía un NAK (Negative Acknowledgment) y se reenvía la trama.

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
    MSG_SIZE = 20

    def __init__(self, data):
        self.data = data  # type: bytes[MSG_SIZE]

    def __str__(self):
        return 'Msg(data=%s)' % (self.data)


# From Layer4 to Layer3
class Pkt:
    def __init__(self, seqnum, acknum, checksum, payload):
        self.seqnum = seqnum  # type: integer
        self.acknum = acknum  # type: integer
        self.checksum = checksum  # type: integer
        self.payload = payload  # type: bytes[Msg.MSG_SIZE]

    def __str__(self):
        return ('Pkt(seqnum=%s, acknum=%s, checksum=%s, payload=%s)'
                % (self.seqnum, self.acknum, self.checksum, self.payload))


# Entity A methods
class EntityA:
    #  Este método se llama una vez antes de que se llamen otros métodos de EntityA.
    #  Se utiliza para la inicialización.
    #  seqnum_limit es el número máximo de valores de secuencia distintos que puede utilizar el protocolo.
    def __init__(self, seqnum_limit):
        # Inicialización de variables de estado (constantes)
        self.OUTPUT = 0
        self.INPUT = 1
        self.TIMER = 2
        self.WAIT_TIME = 10.0  # How long to wait for ack?

        # Inicialización de variables de estado (específicas del protocolo)
        self.layer5_msgs = []
        self.bit = 0
        self.sent_pkt = None
        self.handle_event = self.handle_event_wait_for_call

    #  Este método se llama desde la capa 5 cuando hay datos para enviar.
    #  Agrega el mensaje a la cola y llama al método handle_event con el evento OUTPUT
    def output(self, message):
        self.layer5_msgs.append(message)
        self.handle_event(self.OUTPUT)

    # Este método se llama desde la capa 3 cuando llega un paquete a la capa 4 en EntityA.
    # Llama al método handle_event con el evento INPUT y pasa el paquete como argumento.
    def input(self, packet):
        self.handle_event(self.INPUT, packet)

    #  Este método se llama cuando el temporizador de A expira.
    #  Llama al método handle_event con el evento TIMER.
    def timer_interrupt(self):
        self.handle_event(self.TIMER)
        pass

    # Este método maneja eventos cuando la entidad A está esperando una llamada (waiting for a call).
    # Los eventos pueden ser OUTPUT (datos listos para enviar), INPUT (llegada de un paquete), o TIMER
    # (expiración del temporizador). Dependiendo del evento, realiza acciones específicas.
    def handle_event_wait_for_call(self, e, arg=None):
        if e == self.OUTPUT:
            # Verifica si hay mensajes para enviar
            if not self.layer5_msgs:
                return

            # Toma el primer mensaje de la lista
            m = self.layer5_msgs.pop(0)

            # Crea un paquete con información específica y el contenido del mensaje
            p = Pkt(self.bit, 0, 0, m.data)

            # Inserta un checksum al paquete
            pkt_insert_checksum(p)

            # Envía el paquete a la capa 3
            to_layer3(self, p)

            # Guarda el paquete enviado
            self.sent_pkt = p

            # Inicia un temporizador con un tiempo de espera definido
            start_timer(self, self.WAIT_TIME)

            # Establece el próximo estado del manejador de eventos
            self.handle_event = self.handle_event_wait_for_ack

        elif e == self.INPUT:
            # No realiza ninguna acción específica en este caso
            pass

        elif e == self.TIMER:
            # Ignora el evento de temporizador y emite un mensaje si TRACE es mayor que cero
            if TRACE > 0:
                print('EntityA: ignoring unexpected timeout.')


        else:
            # Para otros eventos llama a la función para manejar eventos desconocidos
            self.unknown_event(e)

    # Este método maneja eventos cuando la entidad A está esperando un ack (acknowledgment).
    # Los eventos pueden ser OUTPUT (datos listos para enviar), INPUT (llegada de un paquete),
    # o TIMER (expiración del temporizador). Dependiendo del evento, realiza acciones específicas.
    def handle_event_wait_for_ack(self, e, arg=None):
        if e == self.OUTPUT:
            # No realiza ninguna acción específica en este caso
            pass

        elif e == self.INPUT:
            # Obtiene el paquete recibido como argumento
            p = arg

            # Verifica si el paquete está corrupto o el acknum no coincide con el bit esperado
            if pkt_is_corrupt(p) or p.acknum != self.bit:
                # Ignora el paquete en caso de corrupción o acknum incorrecto
                return

            # Detiene el temporizador
            stop_timer(self)

            # Cambia el bit esperado (alterna entre 0 y 1)
            self.bit = 1 - self.bit

            # Establece el próximo estado del manejador de eventos
            self.handle_event = self.handle_event_wait_for_call

            # Llama al manejador de eventos para el evento de salida
            self.handle_event(self.OUTPUT)

        elif e == self.TIMER:
            # Reenvía el paquete previamente enviado a la capa 3
            to_layer3(self, self.sent_pkt)

            # Inicia un temporizador con un tiempo de espera definido
            start_timer(self, self.WAIT_TIME)


        else:
            # Para otros eventos llama a la función para manejar eventos desconocidos
            self.unknown_event(e)

    # Este método imprime un mensaje indicando que se recibió un evento desconocido.
    def self_unknown_event(self, e):
        print(f'EntityA: ignoring unknown event {e}.')


# Entity B methods
class EntityB:
    # Este método inicializa la entidad B. La entidad B tiene una variable expecting_bit
    # que indica el próximo bit esperado.
    def __init__(self, seqnum_limit):
        self.expecting_bit = 0
        pass

    # Este método se llama desde la capa 3 cuando llega un paquete a la capa 4 en EntityB.
    # Verifica si el paquete es válido, y si no lo es, envía un ack negativo. Si es válido,
    # entrega el mensaje a la capa 5 y envía un ack positivo.
    def input(self, packet):
        # print(f'B received: {packet}')
        if (packet.seqnum != self.expecting_bit
                or pkt_is_corrupt(packet)):
            p = Pkt(0, 1 - self.expecting_bit, 0, packet.payload)
            pkt_insert_checksum(p)
            to_layer3(self, p)
        else:
            to_layer5(self, Msg(packet.payload))
            # Ack.
            p = Pkt(0, self.expecting_bit, 0, packet.payload)
            pkt_insert_checksum(p)
            to_layer3(self, p)
            #
            self.expecting_bit = 1 - self.expecting_bit

    # Este método se llama cuando el temporizador de B expira. En este caso, no realiza ninguna acción.
    def timer_interrupt(self):
        pass


# Estas funciones se encargan de calcular el checksum de un paquete, insertar el
# checksum en el paquete y verificar si un paquete está corrupto.
# Estos métodos y funciones se utilizan para implementar la lógica del protocolo de bits alternados,
# donde A espera un ack antes de enviar el siguiente paquete y B envía un ack por cada paquete recibido correctamente.

def pkt_compute_checksum(packet):
    crc = 0
    crc = crc32(packet.seqnum.to_bytes(4, byteorder='big'), crc)
    crc = crc32(packet.acknum.to_bytes(4, byteorder='big'), crc)
    crc = crc32(packet.payload, crc)
    return crc


def pkt_insert_checksum(packet):
    packet.checksum = pkt_compute_checksum(packet)


def pkt_is_corrupt(packet):
    return pkt_compute_checksum(packet) != packet.checksum


# Callable functions:
# Función para iniciar el temporizador.
def start_timer(calling_entity, increment):
    the_sim.start_timer(calling_entity, increment)

# Función para detener el temporizador.
def stop_timer(calling_entity):
    the_sim.stop_timer(calling_entity)

# Función para enviar un paquete a la capa 3.
def to_layer3(calling_entity, packet):
    the_sim.to_layer3(calling_entity, packet)

# Función para enviar un mensaje a la capa 5.
def to_layer5(calling_entity, message):
    the_sim.to_layer5(calling_entity, message)

# Función para obtener el tiempo actual.
def get_time(calling_entity):
    return the_sim.get_time(calling_entity)


# Network simulation:
class EventType(Enum):
    TIMER_INTERRUPT = auto()
    FROM_LAYER5 = auto()
    FROM_LAYER3 = auto()


class Event:
    def __init__(self, ev_time, ev_type, ev_entity, packet=None):
        self.ev_time = ev_time  # float
        self.ev_type = ev_type  # EventType
        self.ev_entity = ev_entity  # EntityA or EntityB
        self.packet = packet  # Pkt or None


class Simulator:
    def __init__(self, options, cbA=None, cbB=None):
        self.n_sim = 0
        self.n_sim_max = options.num_msgs
        self.time = 0.000
        self.interarrival_time = options.interarrival_time
        self.loss_prob = options.loss_prob
        self.corrupt_prob = options.corrupt_prob
        self.seqnum_limit = options.seqnum_limit
        self.n_to_layer3_A = 0
        self.n_to_layer3_B = 0
        self.n_lost = 0
        self.n_corrupt = 0
        self.n_to_layer5_A = 0
        self.n_to_layer5_B = 0

        if options.random_seed is None:
            self.random_seed = time.time_ns()
        else:
            self.random_seed = options.random_seed
        random.seed(self.random_seed)

        if self.seqnum_limit < 2:
            self.seqnum_limit_n_bits = 0
        else:
            # How many bits to represent integers in [0, seqnum_limit-1]?
            self.seqnum_limit_n_bits = (self.seqnum_limit - 1).bit_length()

        self.trace = options.trace
        self.to_layer5_callback_A = cbA
        self.to_layer5_callback_B = cbB

        self.entity_A = EntityA(self.seqnum_limit)
        self.entity_B = EntityB(self.seqnum_limit)
        self.event_list = []

    def get_stats(self):
        stats = {'n_sim': self.n_sim,
                 'n_sim_max': self.n_sim_max,
                 'time': self.time,
                 'interarrival_time': self.interarrival_time,
                 'loss_prob': self.loss_prob,
                 'corrupt_prob': self.corrupt_prob,
                 'seqnum_limit': self.seqnum_limit,
                 'random_seed': self.random_seed,
                 'n_to_layer3_A': self.n_to_layer3_A,
                 'n_to_layer3_B': self.n_to_layer3_B,
                 'n_lost': self.n_lost,
                 'n_corrupt': self.n_corrupt,
                 'n_to_layer5_A': self.n_to_layer5_A,
                 'n_to_layer5_B': self.n_to_layer5_B
                 }
        return stats

    def run(self):
        if self.trace > 0:
            print('\n===== SIMULATION BEGINS')

        self._generate_next_arrival()

        while (self.event_list
               and self.n_sim < self.n_sim_max):
            ev = self.event_list.pop(0)
            if self.trace > 2:
                print(f'\nEVENT time: {ev.ev_time}, ', end='')
                if ev.ev_type == EventType.TIMER_INTERRUPT:
                    print(f'timer_interrupt, ', end='')
                elif ev.ev_type == EventType.FROM_LAYER5:
                    print(f'from_layer5, ', end='')
                elif ev.ev_type == EventType.FROM_LAYER3:
                    print(f'from_layer3, ', end='')
                else:
                    print(f'unknown_type, ', end='')
                print(f'entity: {ev.ev_entity}')

            self.time = ev.ev_time

            if ev.ev_type == EventType.FROM_LAYER5:
                self._generate_next_arrival()
                j = self.n_sim % 26
                m = bytes([97 + j for i in range(Msg.MSG_SIZE)])
                if self.trace > 2:
                    print(f'          MAINLOOP: data given to student: {m}')
                self.n_sim += 1
                ev.ev_entity.output(Msg(m))

            elif ev.ev_type == EventType.FROM_LAYER3:
                ev.ev_entity.input(deepcopy(ev.packet))

            elif ev.ev_type == EventType.TIMER_INTERRUPT:
                ev.ev_entity.timer_interrupt()

            else:
                print('INTERNAL ERROR: unknown event type; event ignored.')

        if self.trace > 0:
            print('===== SIMULATION ENDS')

    def _insert_event(self, event):
        if self.trace > 2:
            print(f'            INSERTEVENT: time is {self.time}')
            print(f'            INSERTEVENT: future time will be {event.ev_time}')
        # Python 3.10+: use the bisect module:
        # insort(self.event_list, event, key=lambda e: e.ev_time)
        i = 0
        while (i < len(self.event_list)
               and self.event_list[i].ev_time < event.ev_time):
            i += 1
        self.event_list.insert(i, event)

    def _generate_next_arrival(self):
        if self.trace > 2:
            print('          GENERATE NEXT ARRIVAL: creating new arrival')

        x = self.interarrival_time * 2.0 * random.random()
        ev = Event(self.time + x, EventType.FROM_LAYER5, self.entity_A)
        self._insert_event(ev)

    #####

    def _valid_entity(self, e, method_name):
        if (e is self.entity_A
                or e is self.entity_B):
            return True
        print(f'''WARNING: entity in call to `{method_name}` is invalid!
  Invalid entity: {e}
  Call ignored.''')
        return False

    def _valid_increment(self, i, method_name):
        if ((type(i) is int or type(i) is float)
                and i >= 0.0):
            return True
        print(f'''WARNING: increment in call to `{method_name}` is invalid!
  Invalid increment: {i}
  Call ignored.''')
        return False

    def _valid_message(self, m, method_name):
        if (type(m) is Msg
                and type(m.data) is bytes
                and len(m.data) == Msg.MSG_SIZE):
            return True
        print(f'''WARNING: message in call to `{method_name}` is invalid!
  Invalid message: {m}
  Call ignored.''')
        return False

    def _valid_packet(self, p, method_name):
        if (type(p) is Pkt
                and type(p.seqnum) is int
                and 0 <= p.seqnum < self.seqnum_limit
                and type(p.acknum) is int
                and 0 <= p.acknum < self.seqnum_limit
                and type(p.checksum) is int
                and type(p.payload) is bytes
                and len(p.payload) == Msg.MSG_SIZE):
            return True
        # Issue special warnings for invalid seqnums and acknums.
        if (type(p.seqnum) is int
                and not (0 <= p.seqnum < self.seqnum_limit)):
            print(f'''WARNING: seqnum in call to `{method_name}` is invalid!
  Invalid packet: {p}
  Call ignored.''')
        elif (type(p.acknum) is int
              and not (0 <= p.acknum < self.seqnum_limit)):
            print(f'''WARNING: acknum in call to `{method_name}` is invalid!
  Invalid packet: {p}
  Call ignored.''')
        else:
            print(f'''WARNING: packet in call to `{method_name}` is invalid!
  Invalid packet: {p}
  Call ignored.''')
        return False

    #####

    def start_timer(self, entity, increment):
        if not self._valid_entity(entity, 'start_timer'):
            return
        if not self._valid_increment(increment, 'start_timer'):
            return

        if self.trace > 2:
            print(f'          START TIMER: starting timer at {self.time}')

        for e in self.event_list:
            if (e.ev_type == EventType.TIMER_INTERRUPT
                    and e.ev_entity is entity):
                print('WARNING: attempt to start a timer that is already started!')
                return

        ev = Event(self.time + increment, EventType.TIMER_INTERRUPT, entity)
        self._insert_event(ev)

    def stop_timer(self, entity):
        if not self._valid_entity(entity, 'stop_timer'):
            return

        if self.trace > 2:
            print(f'          STOP TIMER: stopping timer at {self.time}')

        i = 0
        while i < len(self.event_list):
            if (self.event_list[i].ev_type == EventType.TIMER_INTERRUPT
                    and self.event_list[i].ev_entity is entity):
                break
            i += 1
        if i < len(self.event_list):
            self.event_list.pop(i)
        else:
            print('WARNING: unable to stop timer; it was not running.')

    def to_layer3(self, entity, packet):
        if not self._valid_entity(entity, 'to_layer3'):
            return
        if not self._valid_packet(packet, 'to_layer3'):
            return

        if entity is self.entity_A:
            receiver = self.entity_B
            self.n_to_layer3_A += 1
        else:
            receiver = self.entity_A
            self.n_to_layer3_B += 1

        # Simulate losses.
        if random.random() < self.loss_prob:
            self.n_lost += 1
            if self.trace > 0:
                print('          TO_LAYER3: packet being lost')
            return

        seqnum = packet.seqnum
        acknum = packet.acknum
        checksum = packet.checksum
        payload = packet.payload

        # Simulate corruption.
        if random.random() < self.corrupt_prob:
            self.n_corrupt += 1
            x = random.random()
            if (x < 0.75
                    or self.seqnum_limit_n_bits == 0):
                payload = b'Z' + payload[1:]
            elif x < 0.875:
                # Flip a random bit in the seqnum.
                # The result might be greater than seqnum_limit if seqnum_limit
                # is not a power of two.  This is OK.
                # Recall that randrange(x) returns an int in [0, x).
                seqnum ^= 2 ** random.randrange(self.seqnum_limit_n_bits)
                # Kurose's simulator simply did:
                # seqnum = 999999
            else:
                # Flip a random bit in the acknum.
                acknum ^= 2 ** random.randrange(self.seqnum_limit_n_bits)
                # Kurose's simulator simply did:
                # acknum = 999999
            if self.trace > 0:
                print('          TO_LAYER3: packet being corrupted')

        # Compute the arrival time of packet at the other end.
        # Medium cannot reorder, so make sure packet arrives between 1 and 9
        # time units after the latest arrival time of packets
        # currently in the medium on their way to the destination.
        last_time = self.time
        for e in self.event_list:
            if (e.ev_type == EventType.FROM_LAYER3
                    and e.ev_entity is receiver):
                last_time = e.ev_time
        arrival_time = last_time + 1.0 + 8.0 * random.random()

        p = Pkt(seqnum, acknum, checksum, payload)
        ev = Event(arrival_time, EventType.FROM_LAYER3, receiver, p)
        if self.trace > 2:
            print('          TO_LAYER3: scheduling arrival on other side')
        self._insert_event(ev)

    def to_layer5(self, entity, message):
        if not self._valid_entity(entity, 'to_layer5'):
            return
        if not self._valid_message(message, 'to_layer5'):
            return

        if entity is self.entity_A:
            self.n_to_layer5_A += 1
            callback = self.to_layer5_callback_A
        else:
            self.n_to_layer5_B += 1
            callback = self.to_layer5_callback_B

        if self.trace > 2:
            print(f'          TO_LAYER5: data received: {message.data}')
        if callback:
            callback(message.data)

    def get_time(self, entity):
        if not self._valid_entity(entity, 'get_time'):
            return
        return self.time


###############################################################################

TRACE = 0

the_sim = None


def report_config():
    stats = the_sim.get_stats()
    print(f'''SIMULATION CONFIGURATION
--------------------------------------
(-n) # layer5 msgs to be provided:      {stats['n_sim_max']}
(-d) avg layer5 msg interarrival time:  {stats['interarrival_time']}
(-z) transport protocol seqnum limit:   {stats['seqnum_limit']}
(-l) layer3 packet loss prob:           {stats['loss_prob']}
(-c) layer3 packet corruption prob:     {stats['corrupt_prob']}
(-s) simulation random seed:            {stats['random_seed']}
--------------------------------------''')


def report_results():
    stats = the_sim.get_stats()
    time = stats['time']
    if time > 0.0:
        tput = stats['n_to_layer5_B'] / time
    else:
        tput = 0.0
    print(f'''\nSIMULATION SUMMARY
--------------------------------
# layer5 msgs provided to A:      {stats['n_sim']}
# elapsed time units:             {stats['time']}

# layer3 packets sent by A:       {stats['n_to_layer3_A']}
# layer3 packets sent by B:       {stats['n_to_layer3_B']}
# layer3 packets lost:            {stats['n_lost']}
# layer3 packets corrupted:       {stats['n_corrupt']}
# layer5 msgs delivered by A:     {stats['n_to_layer5_A']}
# layer5 msgs delivered by B:     {stats['n_to_layer5_B']}
# layer5 msgs by B/elapsed time:  {tput}
--------------------------------''')


def main(options, cb_A=None, cb_B=None):
    global TRACE
    TRACE = options.trace

    global the_sim
    the_sim = Simulator(options, cb_A, cb_B)
    report_config()
    the_sim.run()


#####

if __name__ == '__main__':
    desc = 'Run a simulation of a reliable data transport protocol.'
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument('-n', type=int, default=10,
                        dest='num_msgs',
                        help=('number of messages to simulate'
                              ' [int, default: %(default)s]'))
    parser.add_argument('-d', type=float, default=100.0,
                        dest='interarrival_time',
                        help=('average time between messages'
                              ' [float, default: %(default)s]'))
    parser.add_argument('-z', type=int, default=16,
                        dest='seqnum_limit',
                        help=('seqnum limit for data transport protocol; '
                              'all packet seqnums must be >=0 and <limit'
                              ' [int, default: %(default)s]'))
    parser.add_argument('-l', type=float, default=0.0,
                        dest='loss_prob',
                        help=('packet loss probability'
                              ' [float, default: %(default)s]'))
    parser.add_argument('-c', type=float, default=0.0,
                        dest='corrupt_prob',
                        help=('packet corruption probability'
                              ' [float, default: %(default)s]'))
    parser.add_argument('-s', type=int,
                        dest='random_seed',
                        help=('seed for random number generator'
                              ' [int, default: %(default)s]'))
    parser.add_argument('-v', type=int, default=0,
                        dest='trace',
                        help=('level of event tracing'
                              ' [int, default: %(default)s]'))
    options = parser.parse_args()

    main(options)
    report_results()
    sys.exit(0)

###############################################################################

## End of program.
