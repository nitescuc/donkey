import serial
import time

class NucleoController(object):

    def __init__(self,
                 serial_device=None,
                 serial_baud=115200,
                 model_path=None,
                 verbose = False
                 ):
        self.model_path = model_path
        self.serial_device = serial_device
        self.serial_baud = serial_baud

        self.mode = 'user'
        
        self.init()

    def init(self):
        self.serial = serial.Serial(self.serial_device, self.serial_baud)
        return True
    
    def update(self):
        return True

    def run_threaded(self):
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
