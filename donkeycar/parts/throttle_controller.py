from collections import deque

class ThrottleController(object):

    def __init__(self,
                 slow_throttle = 10,
                 medium_throttle = 12,
                 fast_throttle = 14,
                 slow_rpm = 4000,
                 medium_rpm = 3000,
                 break_intensity = 200
                ):
        
        self.slow_throttle = slow_throttle
        self.medium_throttle = medium_throttle
        self.fast_throttle = fast_throttle

        self.slow_rpm = slow_rpm
        self.medium_rpm = medium_rpm
        self.break_intensity = break_intensity
        self.invert = True
        self.break_speed = 0

        self.last_throttle = None
        self.target_rpm = None
        
        self.throttleMap = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, self.slow_throttle, 11, self.medium_throttle, 13, self.fast_throttle]

    
    def is_rpm_superior(self, p_speed, p_target):
        if p_target == None or p_speed == 0:
            return False
        if self.invert:
            return p_speed < p_target
        else:
            return p_speed > p_target


    def throttle_has_changed(self, p_throttle):
        return self.last_throttle == None or p_throttle != self.last_throttle

    def run(self, p_throttle, p_mode, p_rpm = None, p_distance = None):
        if p_mode == 'user' or p_rpm == None:
            return p_throttle
        else:
            if self.throttle_has_changed(p_throttle):
                self.last_throttle = p_throttle
                if p_throttle <= self.slow_throttle:
                    self.target_rpm = self.slow_rpm
                elif p_throttle <= self.medium_throttle:
                    self.target_rpm = self.medium_rpm
                else:
                    self.target_rpm = None
                
            if self.is_rpm_superior(p_rpm, self.target_rpm):
                diff = (self.target_rpm - p_rpm)//self.break_intensity
                if diff > p_throttle:
                    diff = p_throttle
#                print(str(p_throttle)+' '+str(diff))
                p_throttle = p_throttle - diff
            return self.throttleMap[p_throttle]


    def shutdown(self):
        pass        