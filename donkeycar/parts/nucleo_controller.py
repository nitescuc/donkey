import serial
import time
from collections import deque

class NucleoController(object):

    def __init__(self,
                 serial_device=None,
                 serial_baud=115200,
                 verbose = False,
                 limit = 64,
                 slow_throttle = 10,
                 medium_throttle = 12,
                 fast_throttle = 14
                 ):
        self.serial_device = serial_device
        self.serial_baud = serial_baud
        self.recording = False
        self.limit = limit
        self.slow_throttle = slow_throttle
        self.medium_throttle = medium_throttle
        self.fast_throttle = fast_throttle
        self.echo = False
        self.serialInitialized = False
        
        self.speed = 0
        self.breakSeq = deque([])
        self.throttleMap = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, self.slow_throttle, 11, self.medium_throttle, 13, self.fast_throttle]

        self.mode = None

        self.serial_init()
    

    def apply_config(self, config):
        if 'limit' in config and config['limit']:
            self.limit = int(config['limit'])
            self.serial.write(b'L')
            packet = bytearray()
            packet.append(self.limit)
            self.serial.write(packet)


    def serial_init(self):
        self.serial = serial.Serial(self.serial_device, self.serial_baud, timeout=5)
        self.serial.reset_input_buffer()
        # set limit
        self.serial.write(b'L')
        packet = bytearray()
        packet.append(self.limit)
        self.serial.write(packet)
        #
        print('Serial initialized')
        self.serialInitialized = True
    

    def change_mode(self, mode):
        mode_letter = 'u'
        if mode == 'local_angle':
            mode_letter = 'a'
        if mode == 'local':
            mode_letter = 'p'
        self.serial.write(b'm')
        self.serial.write(mode_letter.encode())
        self.mode = mode


    def update(self):
        return True


    def run_threaded(self, p_angle, p_throttle, p_mode):
        return True


    def run(self, p_angle, p_throttle, p_mode, p_recording):
        if not self.serialInitialized:
            return 7, 7, 'user', False
        if p_mode != self.mode:
            self.change_mode(p_mode)
        if self.mode != 'user':
            steering = p_angle
            throttle = p_throttle
        if self.mode == 'user':
            self.serial.write(b'r')
            temp = self.serial.read(1)
            if len(temp):
                steering = temp[0] >> 4
                throttle = temp[0] & 0x0F
            else:
               steering = 7
               throttle = 7
        else:
            if throttle != None and steering != None:
                # break management
                if throttle >= 12:
                    self.speed = self.speed + 1
                elif throttle < 12:
                    print('Speed: ' + str(self.speed))
                    if self.speed > 10:
                        self.breakSeq.extend([0,0])
                    self.speed = 0
                if len(self.breakSeq):
                    throttle = self.breakSeq.popleft()
                # send throttle
                package = bytearray()
                package.append(steering * 16 + self.throttleMap[throttle])
                self.serial.write(b'w')
                self.serial.write(package)
            steering = 7
            throttle = 7

        self.recording = p_recording or (throttle > 7 and self.mode == 'user')
        
        return steering, throttle, self.mode, self.recording


    def shutdown(self):
        self.change_mode('user')
        self.running = False
