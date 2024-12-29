from abc import abstractmethod
from colorsys import hsv_to_rgb, rgb_to_hsv
from math import fmod
from random import random, randint, shuffle
from time import sleep, monotonic

from gradient import Gradient
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, rgb_to_hue, random_color

def shift_color(color, shift):
    h, s, v = rgb_to_hsv(color[0] / 255, color[1] / 255, color[2] / 255)
    h = fmod(h + shift + 1.0, 1.0)
    r, g, b = hsv_to_rgb(h, s, v)
    return (int(255 * r), int(255 * g), int(255 * b))

def opposite_color(color):
    return shift_color(color, .5)

def tri_color(color):
    return shift_color(color, .33333), shift_color(color, .66666)

class EffectSweep(Effect):

    FADER_HUE = 4
    FADE_CONSTANT = .85

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)

    def get_active_faders(self):
        return [ self.FADER_HUE ]

    def map_fader_value(self, fader, value):
        if fader == self.FADER_HUE:
            return value / 4 
        return None

    def run(self):

        led_data = [ list([0,0,0]) for x in range(self.driver.strips * self.driver.leds) ]
        strip = 0
        step = 1
        _pass = 0
        color = self.get_next_color()

        hue = self.fader_value(self.FADER_HUE)
        color_1 = shift_color(color, hue)
        color_2 = shift_color(color, -hue)

        hue = 0.0
        hue_increment = .05
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            hue_inc = self.fader_value(self.FADER_HUE)

            #print("strip: %d step: %d pass %d" % (strip, step, _pass))
            for l in range(self.driver.leds):
                led_data[(strip * self.driver.leds) + l] = color
            self.driver.set(led_data)

            for l in range(self.driver.leds):
                r = randint(0, 25)
                if _pass == 1 or r >= 3:
                    led_data[(strip * self.driver.leds) + l] = (0,0,0)
                else:
                    if r % 2 == 0:
                        led_data[(strip * self.driver.leds) + l] = color_1
                    else:
                        led_data[(strip * self.driver.leds) + l] = color_2

            if self.driver.strips == 8:
                if strip == self.driver.strips - 1 and step > 0:
                    step = -1
                    _pass = (_pass + 1) % 2
                if strip == 0 and step < 0:
                    _pass = (_pass + 1) % 2
                    step = 1
                    color = self.get_next_color()
                    hue = self.fader_value(self.FADER_HUE)
                    color_1 = shift_color(color, hue)
                    color_2 = shift_color(color, -hue)
            else:
                if strip == self.driver.strips - 1:
                    color = hue_to_rgb(hue)
                    hue_shift = self.fader_value(self.FADER_HUE)
                    color_1 = shift_color(color, hue_shift)
                    color_2 = shift_color(color, -hue_shift)
                    _pass = (_pass + 1) % 2
                    hue = fmod(hue + hue_increment, 1.0)

            instant = self.get_instant_color()
            if instant is not None:
                hue_shift = self.fader_value(self.FADER_HUE)
                color = instant
                color_1 = shift_color(color, hue_shift)
                color_2 = shift_color(color, -hue_shift)
                hue, _, _ = rgb_to_hue(color)

            strip = (strip + step) % self.driver.strips
            self.sleep()
