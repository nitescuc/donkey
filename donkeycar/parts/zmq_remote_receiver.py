import sys
import zmq

class ZmqRemoteReceiver():
    def __init__(self, remote):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(remote)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"remote")

        self.angle = None
        self.throttle = None
        self.recording = False 
        self.mode = 'local_angle'

        self.on = True

        self.speed = 0

    def run(self):
        [address, value] = self.subscriber.recv_multipart()
        address = address.decode()
        if address == 'remote_steering':
            self.angle = float(value)
        if address == 'remote_throttle':
            self.throttle = float(value)
        #ignore mode for now
        self.recording = self.recording or (self.throttle > 0.2) 
        return self.angle, self.throttle, self.recording

    def run_threaded(self):
        return self.angle, self.throttle, self.recording

    def update(self):
        while self.on:
            [address, angle, throttle] = self.subscriber.recv_multipart()
            self.angle = float(angle)
            self.throttle = float(throttle)
            self.recording = self.recording or (throttle > 0.2) 

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqRemoteReceiver')
        self.subscriber.close()
        self.context.term()
