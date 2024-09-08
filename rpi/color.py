from math import fmod
from colorsys import hsv_to_rgb
from random import randint

def hue_to_rgb(hue, saturation=1.0, value=1.0):
    if saturation != 1.0:
        saturation = fmod(saturation, 1.0)
    if value != 1.0:
        value = fmod(value, 1.0)
    r,g,b = hsv_to_rgb(fmod(hue, 1.0), saturation, value) 
    return (int(r * 255), int(g * 255), int(b * 255))

def random_color():
    return (randint(0, 255), randint(0, 255), randint(0, 255))

