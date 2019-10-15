import os
import time
import numpy as np
from PIL import Image
import glob
import cv2

class BaseCamera:
    def __init__(self, resolution=(120, 160), framerate=20, brightness = 0, rotate = 0, processor = None):
        self.resolution = resolution
        self.framerate = framerate
        self.processor = processor

    def run_threaded(self):
        return np.copy(self.frame)

    def apply_config(self, config):
        if self.processor != None:
            self.processor.apply_config(config)

class PiCamera(BaseCamera):
    def __init__(self, resolution=(120, 160), framerate=20, brightness = 0, rotate = 0, processor = None):
        from picamera.array import PiRGBArray
        from picamera import PiCamera
        resolution = (resolution[1], resolution[0])
        # initialize the camera and stream
        self.camera = PiCamera() #PiCamera gets resolution (height, width)
        self.camera.resolution = resolution
        self.camera.framerate = framerate
        self.processor = processor
        # tuning
        self.camera.exposure_mode = 'sports'
        self.camera.color_effects = (128,128)

        #self.camera.exposure_mode = 'sports'
        #self.camera.iso = 800
        self.rawCapture = PiRGBArray(self.camera, size=resolution)
        self.stream = self.camera.capture_continuous(self.rawCapture,
            format="rgb", use_video_port=True)

        # initialize the frame and the variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.on = True

        print('PiCamera loaded.. .warming camera')
        time.sleep(2)

    def run(self):
        f = next(self.stream)
        frame = f.array
        self.rawCapture.truncate(0)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if self.processor != None:
            frame = self.processor.processFrame(frame)
        return frame

    def update(self):
        # keep looping infinitely until the thread is stopped
        for f in self.stream:
            # grab the frame from the stream and clear the stream in
            # preparation for the next frame
            frame = f.array
            self.rawCapture.truncate(0)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if self.processor != None:
                frame = self.processor.processFrame(frame)
            self.frame = frame

            # if the thread indicator variable is set, stop the thread
            if not self.on:
                break

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping PiCamera')
        time.sleep(.5)
        self.stream.close()
        self.rawCapture.close()
        self.camera.close()

class Webcam(BaseCamera):
    def __init__(self, resolution = (120, 160), framerate = 20, brightness = 0, rotate = 0, processor = None):
        from PyV4L2Camera.camera import Camera
        from PyV4L2Camera.controls import ControlIDs

        super().__init__()

        self.cam = Camera('/dev/video0', 640, 480)
        self.resolution = resolution
        self.framerate = framerate
        self.brightness = brightness
        self.rotate = rotate

#        self.cam.set_control_value(ControlIDs.BRIGHTNESS, self.brightness)
#        self.cam.set_control_value(ControlIDs.CONTRAST, 20)

        # initialize variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.on = True

        print('WebcamVideoStream loaded')

    def update(self):
        from datetime import datetime, timedelta
        while self.on:
            start = datetime.now()

            frame = self.cam.get_frame()
            im = Image.frombytes('RGB', (self.cam.width, self.cam.height), frame, 'raw', 'RGB')
            self.frame = cv2.resize(np.asarray(im), (self.resolution[1], self.resolution[0]))
            if self.rotate: 
                self.frame = cv2.rotate(self.frame, rotateCode=cv2.ROTATE_180)

            stop = datetime.now()
            s = 1 / self.framerate - (stop - start).total_seconds()
#            if s > 0:
#                time.sleep(s)
        self.cam.close()

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping Webcam')
        time.sleep(.5)

class PyGameWebcam(BaseCamera):
    def __init__(self, resolution = (120, 160), framerate = 20, brightness = 0, rotate = 0, processor = None):
        import pygame
        import pygame.camera

        super().__init__()

        pygame.init()
        pygame.camera.init()
        l = pygame.camera.list_cameras()
        self.cam = pygame.camera.Camera(l[0], resolution, "RGB")
        self.resolution = resolution
        self.cam.start()
        self.framerate = framerate

        # initialize variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.on = True

        print('WebcamVideoStream loaded.. .warming camera')

        time.sleep(2)

    def update(self):
        from datetime import datetime, timedelta
        import pygame.image
        while self.on:
            start = datetime.now()

            if self.cam.query_image():
                # snapshot = self.cam.get_image()
                # self.frame = list(pygame.image.tostring(snapshot, "RGB", False))
                snapshot = self.cam.get_image()
                snapshot1 = pygame.transform.scale(snapshot, self.resolution)
                self.frame = pygame.surfarray.pixels3d(pygame.transform.rotate(pygame.transform.flip(snapshot1, True, False), 90))

            stop = datetime.now()
            s = 1 / self.framerate - (stop - start).total_seconds()
            if s > 0:
                time.sleep(s)

        self.cam.stop()

    def run_threaded(self):
        return self.frame

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping Webcam')
        time.sleep(.5)

class CV2Webcam(BaseCamera):
    def __init__(self, resolution = (120, 160), framerate = 20, brightness = 0, rotate = 0, processor = None):
        super().__init__()

        self.resolution = resolution
        self.framerate = framerate
        self.processor = processor

        cam = self._create_cam()
        if not cam.isOpened():
            raise IOError("Cannot open webcam")
        
        self.cam = cam

        # initialize variable used to indicate
        # if the thread should be stopped
        self.frame = None
        self.on = True

        print('WebcamVideoStream loaded.. .warming camera')

    def _create_cam(self):
        return cv2.VideoCapture(0)

    def _readFrame(self):
        ret, frame = self.cam.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if self.processor != None:
                frame = self.processor.processFrame(frame)
            return frame
        else:
            return None
        
    def update(self):
        while self.on:
            frame = self._readFrame()
            if frame is not None:
                self.frame = frame
            else:
                break
#            self.frame = cv2.resize(frame, self.resolution)

    def run(self):
        return self._readFrame()

    def run_threaded(self):
        return self.frame

    def shutdown(self):
        # indicate that the thread should be stopped
        self.on = False
        print('stoping Webcam')
        self.cam.release()


class JetsonCV2Webcam(CV2Webcam):
    def _create_cam(self):
        return cv2.VideoCapture(self._gst_str(), cv2.CAP_GSTREAMER)

    def _gst_str(self):
        return 'nvarguscamerasrc ! video/x-raw(memory:NVMM), width=%d, height=%d, format=(string)NV12, framerate=(fraction)%d/1 ! nvvidconv flip-method=2 ! video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! videoconvert ! appsink' % (
            1280, 720, self.framerate, self.resolution[1], self.resolution[0])


class MockCamera(BaseCamera):
    '''
    Fake camera. Returns only a single static frame
    '''
    def __init__(self, resolution=(160, 120), image=None):
        if image is not None:
            self.frame = image
        else:
            self.frame = Image.new('RGB', resolution)

    def update(self):
        pass

    def shutdown(self):
        pass

class ImageListCamera(BaseCamera):
    '''
    Use the images from a tub as a fake camera output
    '''
    def __init__(self, path_mask='~/d2/data/**/*.jpg'):
        self.image_filenames = glob.glob(os.path.expanduser(path_mask), recursive=True)
    
        def get_image_index(fnm):
            sl = os.path.basename(fnm).split('_')
            return int(sl[0])

        '''
        I feel like sorting by modified time is almost always
        what you want. but if you tared and moved your data around,
        sometimes it doesn't preserve a nice modified time.
        so, sorting by image index works better, but only with one path.
        '''
        self.image_filenames.sort(key=get_image_index)
        #self.image_filenames.sort(key=os.path.getmtime)
        self.num_images = len(self.image_filenames)
        print('%d images loaded.' % self.num_images)
        print( self.image_filenames[:10])
        self.i_frame = 0
        self.frame = None
        self.update()

    def update(self):
        pass

    def run_threaded(self):        
        if self.num_images > 0:
            self.i_frame = (self.i_frame + 1) % self.num_images
            self.frame = Image.open(self.image_filenames[self.i_frame]) 

        return np.asarray(self.frame)

    def shutdown(self):
        pass
