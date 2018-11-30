import serial
import time

class NucleoController(object):

    def __init__(self,
                 serial_device=None,
                 serial_baud=115200,
                 model_path=None,
                 verbose = False,
                 limit = 0x04
                 ):
        self.model_path = model_path
        self.serial_device = serial_device
        self.serial_baud = serial_baud
        self.recording = False
        self.limit = limit
        self.echo = False
        self.serialInitialized = False

        self.mode = None

        self.serial_init()

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

    def run(self, p_angle, p_throttle, p_mode):
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
            self.recording = throttle > 7 and self.mode == 'user'
        else:
            if throttle != None and steering != None:
                package = bytearray()
                package.append(steering * 16 + throttle)
                self.serial.write(b'w')
                self.serial.write(package)
        
        return steering, throttle, self.mode, self.recording

    def shutdown(self):
        self.change_mode('user')
        self.running = False
