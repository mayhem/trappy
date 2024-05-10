from math import fmod
from colorsys import hsv_to_rgb

def hue_to_rgb(hue):
    r,g,b = hsv_to_rgb(fmod(hue, 1.0), 1.0, 1.0)
    return (int(r * 255), int(g * 255), int(b * 255))
