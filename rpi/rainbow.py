from abc import abstractmethod
from colorsys import hsv_to_rgb, rgb_to_hsv
from math import fmod
from random import random, randint, shuffle
from time import sleep, monotonic

from gradient import Gradient
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color

# new pattern idea: dont sweep in even spreads, sweep in randomly, even for each sweep.

def shift_color(color, shift):
    h, s, v = rgb_to_hsv(color[0] / 255, color[1] / 255, color[2] / 255)
    h = fmod(h + shift + 1.0, 1.0)
    r, g, b = hsv_to_rgb(h, s, v)
    return (int(255 * r), int(255 * g), int(255 * b))

def opposite_color(color):
    return shift_color(color, .5)

def tri_color(color):
    return shift_color(color, .33333), shift_color(color, .66666)

class EffectRainbowSweep(Effect):

    FADER_SEGMENTS = 4
    FADE_CONSTANT = .85
    SEGMENTS = [4, 6, 12, 18, 24, 48]
    VARIANTS = 5

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)

    def get_active_faders(self):
        return [ self.FADER_SEGMENTS ]

    def map_fader_value(self, fader, value):
        if fader == self.FADER_SEGMENTS:
            return self.SEGMENTS[int(value * (len(self.SEGMENTS) - 1))]
        return None

    def init(self, segments):
        self.quantized = [ list([0,0,0]) for x in range(self.driver.leds) ]
        inc = 1.0 / segments
        for i in range(self.driver.leds):
            segment = i // (self.driver.leds // segments)
            self.quantized[i] = hue_to_rgb(inc * segment)

        step = 1 / (len(self.colors) - 1)
        palette = []
        for i in range(len(self.colors)):
            palette.append([step * i, self.colors[i]])

        self.user_color_gradient = Gradient(palette)


    def fill_segment_rainbow_sweep(self, led, phase, direction, segment):
        col = None
        if phase == 0:
            if direction == 1:
                if segment % 2 == 0:
                    col = self.quantized[led]
                else:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = self.quantized[led]
        else:
            if direction == 1:
                if segment % 2 == 0:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = (0,0,0)

        return col

    def fill_segment_opposite(self, led, phase, direction, segment):
        col = None
        if phase == 0:
            if direction == 1:
                if segment % 2 == 0:
                    col = self.sweep_color_0
                else:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = self.sweep_color_1
        else:
            if direction == 1:
                if segment % 2 == 0:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = (0,0,0)

        return col

    def fill_segment_random_colors(self, led, phase, direction, segment):
        col = None
        if phase == 0:
            if direction == 1:
                if segment % 2 == 0:
                    col = self.segment_color
                else:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = self.segment_color
        else:
            if direction == 1:
                if segment % 2 == 0:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = (0,0,0)

        return col

    def fill_segment_gradient(self, led, phase, direction, segment):
        col = None
        if phase == 0:
            if direction == 1:
                if segment % 2 == 0:
                    col = self.user_color_gradient.get_color(led / self.driver.leds)
                else:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = self.user_color_gradient.get_color(led / self.driver.leds)
        else:
            if direction == 1:
                if segment % 2 == 0:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = (0,0,0)

        return col


    def fill_segment(self, led, phase, direction, segment):

        if self.variant == 0:
            return self.fill_segment_rainbow_sweep(led, phase, direction, segment)

        if self.variant in (1, 4):
            return self.fill_segment_opposite(led, phase, direction, segment)

        if self.variant == 2:
            return self.fill_segment_random_colors(led, phase, direction, segment)

        if self.variant == 3:
            return self.fill_segment_gradient(led, phase, direction, segment)

        assert False

    def start_sweep(self, direction):
        if self.variant == 1:
            self.sweep_color_0 = self.get_next_color()
            self.sweep_color_1 = self.get_next_color()
        if self.variant == 4:
            self.sweep_color_0 = self.user_color_gradient.get_color(random())
            self.sweep_color_1 = self.user_color_gradient.get_color(random())


    def start_segment(self, segment):
        self.segment_color = random_color()

    def run(self):

        led_data = [ list([0,0,0]) for x in range(self.driver.strips * self.driver.leds) ]
        led_data = [ list([0,0,0]) for x in range(self.driver.strips * self.driver.leds) ]
        strip = 0
        step = 1
        color = self.get_next_color()

        segments = self.fader_value(self.FADER_SEGMENTS)
        self.init(segments)

        phase = 0
        self.start_sweep(step)
        last_segment = None
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            segments = self.fader_value(self.FADER_SEGMENTS)

            for i in range(self.driver.leds):
                segment = i // (self.driver.leds // segments)
                if segment != last_segment:
                    self.start_segment(segment)
                    last_segment = segment
                col = self.fill_segment(i, phase, step, segment)

                if col is not None:
                    led_data[(strip * self.driver.leds) + i] = col

            self.driver.set(led_data)

            strip += step
            if strip == self.driver.strips and step > 0:
                step = -1
                strip = self.driver.strips - 1
                self.start_sweep(step)
            if strip == -1 and step < 0:
                step = 1
                strip = 0
                phase = (phase + 1) % 2
                self.start_sweep(step)

            self.sleep()
