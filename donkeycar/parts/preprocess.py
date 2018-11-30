import numpy as np
import cv2


class ImageProcessor:
    def __init__(self, resolution=(120, 160), trimTop=None, trimBottom=None, applyClahe=True):
        self.resolution = resolution
        self.trimTop = trimTop
        self.trimBottom = trimBottom
        self.applyClahe = applyClahe

    def preprocess(self, img):
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#        img = img + 50
        if self.trimTop != None:
            img[self.trimTop[0]:self.trimTop[1]] = 0
        if self.trimBottom != None:
            img[self.trimBottom[0]:self.trimBottom[1]] = 0

        if self.applyClahe:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            img = clahe.apply(img)
        
        return img

    def run(self, image):
        return self.preprocess(image)
