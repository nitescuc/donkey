import sys
import time
import socket

class UdpActuatorEmitter():
    def __init__(self, remote_addr, remote_port):
        #  Socket to talk to server
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.remote_addr = remote_addr
        self.remote_port = remote_port

        self.on = True

    def run(self, angle, throttle, mode):
        if angle == None:
            angle = 7
        if throttle == None:
            throttle = 7
        if mode == None:
            mode = 'user'
        remap_angle = angle * (2/14) - 1
        remap_throttle = throttle * (2/14) - 1
        bytesToSend = ("{:01.4f};{:01.4f};{}".format(remap_angle, remap_throttle, mode)).encode()
        self.socket.sendto(bytesToSend, (self.remote_addr, self.remote_port))

    def run_threaded(self, angle, throttle, mode):
        pass

    def update(self):
        pass

    def shutdown(self):
        bytesToSend = ("{:01.4f};{:01.4f};{}".format(0, 0, 'user')).encode()
        self.socket.sendto(bytesToSend, (self.remote_addr, self.remote_port))
        # indicate that the thread should be stopped
        self.on = False
        print('stoping UdpActuatorEmitter')
