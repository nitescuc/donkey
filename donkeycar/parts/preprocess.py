import numpy as np
import cv2


class ImageProcessor:
    def __init__(self, resolution=(120, 160), trimTop=None, trimBottom=None, applyClahe=True, applyBlur=False):
        self.resolution = resolution
        self.trimTop = trimTop
        self.trimBottom = trimBottom
        self.applyClahe = applyClahe
        self.applyBlur = applyBlur

    def apply_config(self, config):
        if 'apply_clahe' in config:
            self.applyClahe = config['apply_clahe']
        if 'applyBlur' in config:
            self.applyBlur = config['apply_blur']

    def preprocess(self, img):
        if img.shape[2] != 1:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        if self.trimTop != None:
            img[self.trimTop[0]:self.trimTop[1]] = 0
        if self.trimBottom != None:
            img[self.trimBottom[0]:self.trimBottom[1]] = 0

        if self.applyClahe:
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            img = clahe.apply(img)
        
        if self.applyBlur:
            img = cv2.bilateralFilter(img,9,75,75).reshape(self.resolution[0], self.resolution[1], 1)
        
        return img

    def run(self, image):
        return self.preprocess(image)
