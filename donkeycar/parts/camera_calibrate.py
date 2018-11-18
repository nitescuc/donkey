import numpy as np
import cv2


class ImageCalibrate:
    def __init__(self, resolution=(480, 640)):
        self.resolution = resolution

    def preprocess(self, img):
        resolution = self.resolution
        yLen = resolution[1]
        xLen = resolution[0]
        for x in range(0, yLen, yLen//12):
            cv2.line(img, (40,x), (xLen,x), (57, 255, 20), 1)
            cv2.putText(img, str(x//4),
                (0,x+5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (57, 255, 20),
                1)
        for x in range(yLen//24, yLen, yLen//12):
            cv2.line(img, (40,x), (xLen,x), (255, 57, 20), 1)
            cv2.putText(img, str(x//4),
                (0,x+5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 57, 20),
                1)
        
        return img

    def run(self, image):
        return self.preprocess(image)