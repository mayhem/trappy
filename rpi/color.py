from math import fmod
from colorsys import hsv_to_rgb, rgb_to_hsv
from random import randint

def hue_to_rgb(hue, saturation=1.0, value=1.0):
    if saturation != 1.0:
        saturation = fmod(saturation, 1.0)
    if value != 1.0:
        value = fmod(value, 1.0)
    r,g,b = hsv_to_rgb(fmod(hue, 1.0), saturation, value) 
    return (int(r * 255), int(g * 255), int(b * 255))

def rgb_to_hue(color):
    h,s,v = rgb_to_hsv(color[0] / 255.0, color[1] / 255.0, color[2] / 255.0)
    return h,s,v

def random_color():
    return (randint(0, 255), randint(0, 255), randint(0, 255))

