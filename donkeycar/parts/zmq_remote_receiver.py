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
        self.mode = 'user'
        self.recording = False 

        self.on = True

        self.speed = 0

    def run(self):
        [address, angle, throttle] = self.subscriber.recv_multipart()
        self.angle = angle
        self.throttle = throttle
        self.recording = (throttle > 2) 
        return self.angle, self.throttle, self.recording

    def run_threaded(self):
        return self.angle, self.throttle, self.mode, self.recording

    def update(self):
        while self.on:
            [address, angle, throttle, mode] = self.subscriber.recv_multipart()
            self.angle = angle
            self.throttle = throttle
            self.mode = mode
            self.recording = self.recording or (throttle > 8) 

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqRemoteReceiver')
        self.subscriber.close()
        self.context.term()
