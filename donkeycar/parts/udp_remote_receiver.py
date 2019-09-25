import socket
import sys

class UdpRemoteReceiver():
    def __init__(self, port):
        #  Socket to talk to server
        self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.socket.bind(('', port))

        self.angle = None
        self.throttle = None
        self.recording = False 
        self.mode = 'local_angle'

        self.on = True

        self.speed = 0

    def run(self):
        pass

    def run_threaded(self):
        return self.angle, self.throttle, self.recording

    def update(self):
        while self.on:
            bytesAddressPair = self.socket.recvfrom(256)
            message = bytesAddressPair[0].decode().split(';')
            if message[0] == 'st':
                self.angle = float(message[1])
            if message[0] == 'th':
                self.throttle = float(message[1])
            #ignore mode for now
            self.recording = self.recording or (self.throttle > 0.2) 

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping UdpRemoteReceiver')
