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
    
    def change_mode(self, mode):
        mode_letter = 'mu'
        if mode == 'local_angle':
            mode_letter = 'ma'
        if mode == 'local':
            mode_letter = 'mp'
        self.serial.write(mode_letter)
        self.mode = mode

    def update(self):
#        while True:
#            if self.mode != 'user':
#                self.serial.write(b'r')
#                line = self.serial.readline()
#                steering = float(line[:5])
#                throttle = float(line[5:10]) - 0.5
#                remote = float(line[10:15])
                #self.set_mode(remote)
#            time.sleep(0.5)
                
        return True

    def run_threaded(self, p_angle, p_throttle, p_mode):
        steering = p_angle
        throttle = p_throttle
        if p_mode != self.mode:
            self.change_mode(p_mode)
        if throttle > 0.2:
            throttle = 0.2
        if p_mode == 'user':
            self.serial.write(b'r')
            line = self.serial.readline()
            steering = float(line[:5]) * 2 - 1
            throttle = float(line[5:10]) * 2 - 1
            #remote = float(line[10:15])
            #
            if throttle < 0.05 and throttle > -0.05: 
                throttle = 0
            #self.set_mode(remote)
            self.recording = throttle > 0 and self.mode == 'user'
        else:
            steering = (steering + 1)/2
            throttle = (throttle + 1)/2
            self.serial.write(b'w{:01.3f}{:01.3f}'.format(steering, throttle))
        
        return steering, throttle, self.mode, self.recording

    def run(self, angle, steering):
        return False

    def shutdown(self):
        self.running = False
