from collections import deque

class SpeedController(object):

    def __init__(self,
                 slow_throttle = 10,
                 medium_throttle = 12,
                 fast_throttle = 14,
                 break_sequence = [0,0,0,0,0],
                 distance_break_limit = 60
                ):
        
        self.slow_throttle = slow_throttle
        self.medium_throttle = medium_throttle
        self.fast_throttle = fast_throttle
        self.break_sequence = break_sequence
        self.distance_break_limit = distance_break_limit
        
        self.speed = 0
        self.breakSeq = deque([])
        self.throttleMap = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, self.slow_throttle, 11, self.medium_throttle, 13, self.fast_throttle]


    def run(self, p_throttle, p_mode, p_speed = None, p_distance = None):
        if p_distance != None and p_distance < self.distance_break_limit:
            pass
#            print('Distance break')
#            return 0
        if p_mode == 'user':
            return p_throttle
        else:
            # break management
            if p_throttle >= 12:
                self.speed = self.speed + 1
                self.breakSeq.clear()
            elif p_throttle < 12:
                if self.speed > 10:
                    self.breakSeq.extend(self.break_sequence)
                self.speed = 0
            if len(self.breakSeq):
#                print('break')
#                print("Speed " + str(p_speed))
                p_throttle = self.breakSeq.popleft()
            return self.throttleMap[p_throttle]

    def shutdown(self):
        pass        