from math import fmod
from colorsys import hsv_to_rgb
from random import randint

def hue_to_rgb(hue):
    r,g,b = hsv_to_rgb(fmod(hue, 1.0), 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))

def random_color():
    return (randint(32, 255), randint(32, 255), randint(32, 255))

