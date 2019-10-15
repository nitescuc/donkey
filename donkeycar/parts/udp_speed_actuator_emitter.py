import sys
import time
import socket

class UdpSpeedActuatorEmitter():
    def __init__(self, 
        remote_addr, 
        remote_port, 
        slow_throttle = 4000,
        medium_throttle = 3000,
        fast_throttle = 2000
        ):

        #  Socket to talk to server
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.remote_addr = remote_addr
        self.remote_port = remote_port

        self.slow_throttle = slow_throttle
        self.medium_throttle = medium_throttle
        self.fast_throttle = fast_throttle

        self.throttleMap = [10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 10000, 
            self.slow_throttle, 10000, self.medium_throttle, 10000, self.fast_throttle]

        self.on = True

    def run(self, angle, throttle, mode):
        if angle == None:
            angle = 7
        if throttle == None:
            throttle = 7
        if mode == None:
            mode = 'user'
        remap_angle = angle * (2/14) - 1
        remap_throttle = self.throttleMap[throttle]
        bytesToSend = ("{:01.4f};{:d};{}".format(remap_angle, remap_throttle, mode)).encode()
        self.socket.sendto(bytesToSend, (self.remote_addr, self.remote_port))

    def run_threaded(self, angle, throttle, mode):
        pass

    def update(self):
        pass

    def shutdown(self):
        bytesToSend = ("{:01.4f};{:d};{}".format(0, 10000, 'user')).encode()
        self.socket.sendto(bytesToSend, (self.remote_addr, self.remote_port))
        # indicate that the thread should be stopped
        self.on = False
        print('stoping UdpActuatorEmitter')
