import serial
import time

class NucleoController(object):

    def __init__(self,
                 serial_device=None,
                 model_path=None,
                 tub_writer=None,
                 verbose = False
                 ):
        self.model_path = model_path
        self.tub_writer = tub_writer
        self.serial_device = serial_device

        self.mode = 'user'
        
        self.init()

    def init(self):
        self.serial = serial.Serial(self.serial_device, 230400)
        return True
    
    def update(self):
        return True

    def run_threaded(self, img_arr):
        self.serial.write(b'r')
        line = self.serial.readline()
        steering = float(line[:5])
        throttle = float(line[5:10])
        remote = float(line[10:15])
        return steering, throttle, self.mode

    def run(self, *args):
        return False

    def shutdown(self):
        self.running = False
