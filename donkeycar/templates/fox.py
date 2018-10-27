#!/usr/bin/env python3
"""
Scripts to drive a donkey 2 car and train a model for it. 

Usage:
    manage.py (drive) [--model=<model>] [--js|--tx|--pirf] [--sonar]
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
from donkeycar.parts.camera import Webcam
from donkeycar.parts.transform import Lambda
from donkeycar.parts.keras import KerasCategorical
from donkeycar.parts.datastore import TubHandler, TubGroup
from donkeycar.parts.controller import LocalWebController, FPVWebController, NucleoController

from sys import platform

def drive(cfg, model_path=None, use_joystick=False, use_tx=False, use_pirf=False, use_sonar=False):
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

    if platform != "darwin":
        cam = Webcam(resolution=cfg.CAMERA_RESOLUTION)
        V.add(cam, outputs=['cam/image_array'], threaded=True)

    #This web controller will create a web server that is capable
    #of managing steering, throttle, and modes, and more.
    ctr = LocalWebController()
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
    
    # add tub to save data
    inputs = ['cam/image_array', 'user/angle', 'user/throttle', 'user/mode', 'pilot/angle', 'pilot/throttle']
    types = ['image_array', 'float', 'float', 'str', 'numpy.float32', 'numpy.float32']

    th = TubHandler(path=cfg.DATA_PATH)
    tub = th.new_tub_writer(inputs=inputs, types=types)
#    V.add(tub, inputs=inputs, run_condition='recording')

    ctr = NucleoController(cfg.SERIAL_DEVICE, model_path, tub)
    V.add(ctr, 
        inputs=['cam/image_array'],
        outputs=['user/mode'],
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
        drive(cfg, model_path=args['--model'], use_joystick=args['--js'], use_tx=args['--tx'], use_pirf=args['--pirf'], use_sonar=args['--sonar'])

    elif args['train']:
        tub = args['--tub']
        model = args['--model']
        base_model = args['--base_model']
        cache = not args['--no_cache']
        train(cfg, tub, model, base_model=base_model)





