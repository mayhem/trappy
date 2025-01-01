from abc import abstractmethod
from colorsys import hsv_to_rgb, rgb_to_hsv
from math import fmod
from random import random, randint, shuffle
from time import sleep, monotonic

from gradient import Gradient
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, rgb_to_hue, random_color, shift_color


# Too tired to finish the radar effect, will need to go back when fresh
class EffectSweep(Effect):

    FADER_HUE = 4
    FADE_CONSTANT = 1.0
    VARIANTS = 1

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
        
        if self.variant == 0:
            color = self.get_next_color()
            hue = self.fader_value(self.FADER_HUE)
            color_1 = shift_color(color, hue)
            color_2 = shift_color(color, -hue)
        elif self.variant == 1:
            color = [128, 128,128]
            color_1 = [0, 128, 8]

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

            if self.variant == 3:
                # Fade out existing data
                for i in range(self.driver.strips * self.driver.leds):
                    color = led_data[i]
                    for j in range(3):
                        color[j] = int(float(color[j]) * self.FADE_CONSTANT)
                    led_data[i] = color

            for l in range(self.driver.leds):
                if self.variant == 0:
                    r = randint(0, 25)
                    if _pass == 1 or r >= 3:
                        led_data[(strip * self.driver.leds) + l] = [0,0,0]
                    else:
                        if r % 2 == 0:
                            led_data[(strip * self.driver.leds) + l] = color_1
                        else:
                            led_data[(strip * self.driver.leds) + l] = color_2
                elif self.variant == 1:
                    r = randint(0, 50)
                    if _pass == 1 or r >= 3:
                        pass # led_data[(strip * self.driver.leds) + l] = [0,0,0]
                    else:
                        led_data[(strip * self.driver.leds) + l] = color_1

            if self.driver.strips == 8:
                if strip == self.driver.strips - 1 and step > 0:
                    step = -1
                    _pass = (_pass + 1) % 2
                    strip = 8
                if strip == 0 and step < 0:
                    _pass = (_pass + 1) % 2
                    step = 1
                    strip = -1
                    if self.variant == 0:
                        color = self.get_next_color()
                        hue = self.fader_value(self.FADER_HUE)
                        color_1 = shift_color(color, hue)
                        color_2 = shift_color(color, -hue)
            else:
                if strip == self.driver.strips - 1:
                    if self.variant == 0:
                        color = hue_to_rgb(hue)
                        hue_shift = self.fader_value(self.FADER_HUE)
                        color_1 = shift_color(color, hue_shift)
                        color_2 = shift_color(color, -hue_shift)
                        _pass = (_pass + 1) % 2
                        hue = fmod(hue + hue_increment, 1.0)

            instant = self.get_instant_color()
            if self.variant != 0 and instant is not None:
                hue_shift = self.fader_value(self.FADER_HUE)
                color = instant
                color_1 = shift_color(color, hue_shift)
                color_2 = shift_color(color, -hue_shift)
                hue, _, _ = rgb_to_hue(color)

            strip = (strip + step) % self.driver.strips
            self.sleep()
