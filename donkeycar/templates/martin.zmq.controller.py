#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it. 

Usage:
    manage.py (drive)

Options:
    -h --help        Show this screen.
"""
import os
import logging
# set up logging to file - see previous section for more details
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s.%(msecs)03d %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='data/donkey.log',
                    filemode='w')
# define a Handler which writes INFO messages or higher to the sys.stderr
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
# set a format which is simpler for console use
formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
# add the handler to the root logger
logging.getLogger('').addHandler(console)

from docopt import docopt

import donkeycar as dk

# import parts
from donkeycar.parts.transform import Lambda
from donkeycar.parts.actuator import PCA9685, PWMSteering, PWMThrottle
from donkeycar.parts.control_api import APIController
from donkeycar.parts.web_fpv.web import FPVWebController
from donkeycar.parts.pirfcontroller import PiRfController
from donkeycar.parts.speed_controller import SpeedController
from donkeycar.parts.zmq_remote_emitter import ZmqRemoteEmitter
from donkeycar.parts.sonar import SonarController
from donkeycar.parts.led_display import LedDisplay

from sys import platform

def drive(cfg):
    '''
    Start the drive loop
    Each part runs as a job in the Vehicle loop, calling either
    it's run or run_threaded method depending on the constructor flag `threaded`.
    All parts are updated one after another at the framerate given in
    cfg.DRIVE_LOOP_HZ assuming each part finishes processing in a timely manner.
    Parts may have named outputs and inputs. The framework handles passing named outputs
    to parts requesting the same named input.
    '''

    # Initialize car
    V = dk.vehicle.Vehicle()

    steering_controller = PCA9685(cfg.STEERING_CHANNEL)
    steering = PWMSteering(controller=steering_controller,
                           left_pulse=cfg.STEERING_LEFT_PWM,
                           right_pulse=cfg.STEERING_RIGHT_PWM)

    throttle_controller = PCA9685(cfg.THROTTLE_CHANNEL)
    throttle = PWMThrottle(controller=throttle_controller,
                           max_pulse=cfg.THROTTLE_FORWARD_PWM,
                           zero_pulse=cfg.THROTTLE_STOPPED_PWM,
                           min_pulse=cfg.THROTTLE_REVERSE_PWM)

    #This web controller will create a web server that is capable
    #of managing steering, throttle, and modes, and more.
    ctr = APIController()
    V.add(ctr, outputs=['user/mode', 'recording', 'config'], threaded=True)

    def apply_config(config):
        if config != None:
            V.apply_config(config)
    apply_config_part = Lambda(apply_config)
    V.add(apply_config_part, inputs=['config'])

    ctr = PiRfController(throttle_tx_min = cfg.PI_RF_THROTTLE_MIN,
                        throttle_tx_max = cfg.PI_RF_THROTTLE_MAX,
                        steering_tx_min = cfg.PI_RF_STEERING_MIN,
                        steering_tx_max = cfg.PI_RF_STEERING_MAX,
                        throttle_tx_thresh = cfg.PI_RF_THROTTLE_TRESH,
                        steering_pin = cfg.PI_RF_STEERING_PIN,
                        throttle_pin = cfg.PI_RF_THROTTLE_PIN,
                        change_mode_pin = cfg.PI_RF_MODE_PIN,
                        steering_act = steering,
                        throttle_act = throttle,
                        model_path = None,
                        verbose = cfg.PI_RF_VERBOSE
                        )
    V.add(ctr,
        inputs=['user/mode', 'recording'],
        outputs=['user/angle', 'user/throttle', 'user/mode', 'recording'],
        threaded=True, can_apply_config=True)

    # See if we should even run the pilot module.
    # This is only needed because the part run_condition only accepts boolean
    def pilot_condition(mode):
        if mode == 'user':
            return False
        else:
            return True

    pilot_condition_part = Lambda(pilot_condition)
    V.add(pilot_condition_part, inputs=['user/mode'], outputs=['run_pilot'])
    
    ctr = ZmqRemoteEmitter(binding=cfg.ZMQ_REMOTE_EMITTER)
    V.add(ctr, 
        inputs=['pilot/angle', 'pilot/throttle', 'user/mode'],
        outputs=[],
        threaded=True, can_apply_config=False)

    # MUST be after discrete_to_float
    sonar = SonarController(trigger_pin=cfg.SON_TRIGGER_PIN,
                        echo_pin=cfg.SON_ECHO_PIN,
                        slowdown_limit=cfg.SON_SLOWDONW,
                        break_limit=cfg.SON_BREAK,
                        verbose = cfg.SON_VERBOSE
                        )
    V.add(sonar,
        inputs=['throttle', 'speed'],
        outputs=['throttle'],
        threaded=True)

    led_display = LedDisplay(cfg.LED_RED, cfg.LED_GREEN, cfg.LED_BLUE)
    V.add(led_display, inputs=['user/mode', 'throttle'])

    # steering and throttle should be added at the end
    V.add(steering, inputs=['angle'])
    V.add(throttle, inputs=['throttle', 'user/mode'], can_apply_config=True)

    # run the vehicle for 20 seconds
    V.start(rate_hz=cfg.DRIVE_LOOP_HZ,
            max_loop_count=cfg.MAX_LOOPS)

    print("You can now go to <your pi ip address>:8887 to drive your car.")


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = dk.load_config()

    if args['drive']:
        drive(cfg)
