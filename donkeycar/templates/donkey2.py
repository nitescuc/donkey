#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it. 

Usage:
    manage.py (drive) [--model=<model>] [--js|--tx|--pirf] [--sonar] [--fpv]
    manage.py (calibrate)
    manage.py (train) [--tub=<tub1,tub2,..tubn>]  (--model=<model>) [--base_model=<base_model>] [--no_cache]

Options:
    -h --help        Show this screen.
    --tub TUBPATHS   List of paths to tubs. Comma separated. Use quotes to use wildcards. ie "~/tubs/*"
    --js             Use physical joystick.
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
from donkeycar.parts.camera import PiCamera
from donkeycar.parts.camera_calibrate import ImageCalibrate
from donkeycar.parts.preprocess import ImageProcessor
from donkeycar.parts.transform import Lambda
from donkeycar.parts.keras import KerasCategorical
from donkeycar.parts.actuator import PCA9685, PWMSteering, PWMThrottle
from donkeycar.parts.datastore import TubHandler, TubGroup
from donkeycar.parts.controller import LocalWebController, FPVWebController, JoystickController, TxController, PiRfController, SonarController
from donkeycar.parts.emergency import EmergencyController
from donkeycar.parts.led_display import LedDisplay

from sys import platform

def drive(cfg, model_path=None, use_joystick=False, use_tx=False, use_pirf=False, use_sonar=False, use_fpv=False):
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

    cam = PiCamera(resolution=cfg.CAMERA_RESOLUTION, framerate=cfg.CAMERA_FRAMERATE)
    V.add(cam, outputs=['cam/image_array'], threaded=True)
    preprocess = ImageProcessor(resolution=cfg.CAMERA_RESOLUTION, trimTop=(0,0), trimBottom=None)
    V.add(preprocess, inputs=['cam/image_array'], outputs=['cam/image_array'], threaded=False)

    steering_controller = PCA9685(cfg.STEERING_CHANNEL)
    steering = PWMSteering(controller=steering_controller,
                           left_pulse=cfg.STEERING_LEFT_PWM,
                           right_pulse=cfg.STEERING_RIGHT_PWM)

    throttle_controller = PCA9685(cfg.THROTTLE_CHANNEL)
    throttle = PWMThrottle(controller=throttle_controller,
                           max_pulse=cfg.THROTTLE_FORWARD_PWM,
                           zero_pulse=cfg.THROTTLE_STOPPED_PWM,
                           min_pulse=cfg.THROTTLE_REVERSE_PWM)

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
                        model_path = model_path,
                        verbose = cfg.PI_RF_VERBOSE
                        )
    V.add(ctr,
        inputs=[],
        outputs=['user/angle', 'user/throttle', 'user/mode', 'recording'],
        threaded=True)
    if use_fpv:
        fpv = FPVWebController()
        V.add(fpv,
            inputs=['cam/image_array'],
            threaded=True)        

    if not (use_pirf or cfg.USE_PI_RF_AS_DEFAULT):
        V.add(ctr,
            inputs=['cam/image_array'],
            outputs=['user/angle', 'user/throttle', 'user/mode', 'recording'],
            threaded=True)

    # See if we should even run the pilot module.
    # This is only needed because the part run_condition only accepts boolean
    def pilot_condition(mode):
        if mode == 'user':
            return False
        else:
            return True

    pilot_condition_part = Lambda(pilot_condition)
    V.add(pilot_condition_part, inputs=['user/mode'], outputs=['run_pilot'])

    if model_path:
        kl = KerasCategorical()
        kl.load(model_path)

        V.add(kl, inputs=['cam/image_array'],
            outputs=['pilot/angle', 'pilot/throttle'],
            run_condition='run_pilot')
    def discrete_to_float(steering, throttle):
        st = steering * (2/14) - 1
        th = throttle * (2/14) - 1
        return st, th
    discrete_to_float_part = Lambda(discrete_to_float)
    V.add(discrete_to_float_part, inputs=['pilot/angle', 'pilot/throttle'], outputs=['pilot/angle', 'pilot/throttle'], run_condition='run_pilot')    

    # Choose what inputs should change the car.
    def drive_mode(mode,
                   user_angle, user_throttle,
                   pilot_angle, pilot_throttle):
        if mode == 'user':
            return user_angle, user_throttle

        elif mode == 'local_angle':
            return pilot_angle, user_throttle

        else:
            return pilot_angle, pilot_throttle

    drive_mode_part = Lambda(drive_mode)
    V.add(drive_mode_part,
          inputs=['user/mode', 'user/angle', 'user/throttle',
                  'pilot/angle', 'pilot/throttle'],
          outputs=['angle', 'throttle'])
    
    if use_sonar:
        sonar = SonarController(trigger_pin=cfg.SON_TRIGGER_PIN,
                            echo_pin=cfg.SON_ECHO_PIN,
                            slowdown_limit=cfg.SON_SLOWDONW,
                            break_limit=cfg.SON_BREAK,
                            verbose = cfg.SON_VERBOSE
                            )
        V.add(sonar,
            inputs=['throttle'],
            outputs=['throttle'],
            threaded=True)

    led_display = LedDisplay()
    V.add(led_display, inputs=['user/mode', 'throttle'])

    # steering and throttle should be added at the end
    V.add(steering, inputs=['angle'])
    V.add(throttle, inputs=['throttle', 'user/mode'])

    # add tub to save data
    inputs = ['cam/image_array', 'user/angle', 'user/throttle', 'user/mode', 'pilot/angle', 'pilot/throttle']
    types = ['image_array', 'float', 'float', 'str', 'numpy.float32', 'numpy.float32']

    th = TubHandler(path=cfg.DATA_PATH)
    tub = th.new_tub_writer(inputs=inputs, types=types)
    V.add(tub, inputs=inputs, run_condition='recording')

    # run the vehicle for 20 seconds
    V.start(rate_hz=cfg.DRIVE_LOOP_HZ,
            max_loop_count=cfg.MAX_LOOPS)

    print("You can now go to <your pi ip address>:8887 to drive your car.")


def calibrate(cfg):
    # Initialize car
    V = dk.vehicle.Vehicle()

    cam = PiCamera((480, 640))
    V.add(cam, outputs=['cam/image_array'], threaded=True)
    calibrate = ImageCalibrate((480,640))
    V.add(calibrate, inputs=['cam/image_array'], outputs=['cam/image_array'], threaded=False)

    fpv = FPVWebController()
    V.add(fpv,
            inputs=['cam/image_array'],
            threaded=True)        
    # run the vehicle for 20 seconds
    V.start(rate_hz=cfg.DRIVE_LOOP_HZ,
            max_loop_count=cfg.MAX_LOOPS)
    print("You can now go to <your pi ip address>:8887 to drive your car.")

def train(cfg, tub_names, model_name, base_model=None):
    '''
    use the specified data in tub_names to train an artifical neural network
    saves the output trained model as model_name
    '''
    X_keys = ['cam/image_array']
    y_keys = ['user/angle', 'user/throttle']

    def rt(record):
        record['user/angle'] = dk.utils.linear_bin(record['user/angle'])
        return record

    kl = KerasCategorical()
    #kl = KerasLinear()
    print(base_model)
    if base_model is not None:
        base_model = os.path.expanduser(base_model)
        kl.load(base_model)

    print('tub_names', tub_names)
    if not tub_names:
        tub_names = os.path.join(cfg.DATA_PATH, '*')

    tubgroup = TubGroup(tub_names)
    train_gen, val_gen = tubgroup.get_train_val_gen(X_keys, y_keys, record_transform=rt,
                                                    batch_size=cfg.BATCH_SIZE,
                                                    train_frac=cfg.TRAIN_TEST_SPLIT)

    model_path = os.path.expanduser(model_name)

    total_records = len(tubgroup.df)
    total_train = int(total_records * cfg.TRAIN_TEST_SPLIT)
    total_val = total_records - total_train
    print('train: %d, validation: %d' % (total_train, total_val))
    steps_per_epoch = total_train // cfg.BATCH_SIZE
    print('steps_per_epoch', steps_per_epoch)

    kl.train(train_gen,
             val_gen,
             saved_model_path=model_path,
             steps=steps_per_epoch,
             train_split=cfg.TRAIN_TEST_SPLIT)


if __name__ == '__main__':
    args = docopt(__doc__)
    cfg = dk.load_config()

    if args['drive']:
        drive(cfg, model_path=args['--model'], use_joystick=args['--js'], use_tx=args['--tx'], use_pirf=args['--pirf'], use_sonar=args['--sonar'], use_fpv=args['--fpv'])

    elif args['calibrate']:
        calibrate(cfg)

    elif args['train']:
        tub = args['--tub']
        model = args['--model']
        base_model = args['--base_model']
        cache = not args['--no_cache']
        train(cfg, tub, model, base_model=base_model)





