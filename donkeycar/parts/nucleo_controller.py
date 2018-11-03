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
        self.recording = False

        self.mode = 'user'
        
        self.init()

    def init(self):
        self.serial = serial.Serial(self.serial_device, self.serial_baud)
        # limit
        self.serial.write(b'L0.600')
        return True
    
    def set_mode(self, level):
        if self.model_path is not None:
            if level > 0.500:
                self.mode = 'local'
            else:
                self.mode = 'local_angle'
            self.recording = False

    def update(self):
        while True:
            if self.mode != 'user':
                self.serial.write(b'r')
                line = self.serial.readline()
                steering = float(line[:5])
                throttle = float(line[5:10]) - 0.5
                remote = float(line[10:15])
                #self.set_mode(remote)
            time.sleep(0.5)
                
        return True

    def run_threaded(self, p_angle, p_throttle):
        steering = p_angle
        throttle = p_throttle
        if throttle > 0.2:
            throttle = 0.2
        if self.mode == 'user':
            self.serial.write(b'r')
            line = self.serial.readline()
            steering = float(line[:5]) * 2 - 1
            throttle = float(line[5:10]) * 2 - 1
            remote = float(line[10:15])
            #
            if throttle < 0.05 and throttle > -0.05: 
                throttle = 0
            self.set_mode(remote)
            self.recording = throttle > 0 and self.mode == 'user'
        else:
            self.serial.write(b'w{:01.3f}{:01.3f}'.format((steering + 1) / 2, (throttle + 1) / 2)

        
        return steering, throttle, self.mode, self.recording

    def run(self, angle, steering):
        return False

    def shutdown(self):
        self.running = False
