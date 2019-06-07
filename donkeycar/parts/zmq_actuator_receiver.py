import sys
import zmq

class ZmqActuatorReceiver():
    def __init__(self, remote):
        #  Socket to talk to server
        self.context = zmq.Context()

        self.subscriber = self.context.socket(zmq.SUB)
        self.subscriber.connect(remote)
        self.subscriber.setsockopt(zmq.SUBSCRIBE, b"actuator")

        self.angle = None
        self.throttle = None
        self.mode = None

        self.on = True

        self.speed = 0

    def run(self):
        pass

    def run_threaded(self):
        return self.angle, self.throttle, self.mode

    def update(self):
        while self.on:
            [address, angle, throttle, mode] = self.subscriber.recv_multipart()
            self.angle = float(angle)
            self.throttle = float(throttle)
            self.mode = mode.decode()

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping ZmqActuatorReceiver')
        self.subscriber.close()
        self.context.term()
