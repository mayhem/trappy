from abc import abstractmethod
from colorsys import hsv_to_rgb, rgb_to_hsv
from math import fmod
from random import random, randint, shuffle
from time import sleep, monotonic

from gradient import Gradient
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color, shift_color, opposite_color, tri_color

# new pattern idea: dont sweep in even spreads, sweep in randomly, even for each sweep.

class EffectRainbowSweep(Effect):

    SLUG = "rainbow-sweep"
    FADER_SEGMENTS = 2
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

        self.sweep_color_0 = self.get_next_color()
        self.sweep_color_1 = self.get_next_color()
        self.phase_inc = 0

    def fill_segment_rainbow_sweep(self, led, _pass, phase, segment):
        col = None
        if phase == 0:
            if _pass == 0:
                if segment % 2 == 0:
                    col = self.quantized[led]
                else:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = self.quantized[led]
        else:
            if _pass == 0:
                if segment % 2 == 0:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = (0,0,0)

        return col

    def fill_segment_opposite(self, led, _pass, phase, segment):
        col = None
        if phase == 0:
            if _pass == 0:
                if segment % 2 == 0:
                    col = self.sweep_color_0
                else:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = self.sweep_color_1
        else:
            if _pass == 0:
                if segment % 2 == 0:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = (0,0,0)

        return col

    def fill_segment_random_colors(self, led, _pass, phase, segment):
        col = None
        if phase == 0:
            if _pass == 0:
                if segment % 2 == 0:
                    col = self.segment_color
                else:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = self.segment_color
        else:
            if _pass == 0:
                if segment % 2 == 0:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = (0,0,0)

        return col

    def fill_segment_gradient(self, led, _pass, phase, segment):
        col = None
        if phase == 0:
            if _pass == 0:
                if segment % 2 == 0:
                    col = self.user_color_gradient.get_color(led / self.driver.leds)
                else:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = self.user_color_gradient.get_color(led / self.driver.leds)
        else:
            if _pass == 0:
                if segment % 2 == 0:
                    col = (0,0,0)
            else:
                if segment % 2 == 1:
                    col = (0,0,0)

        return col


    def fill_segment(self, led, _pass, phase, segment):

        if self.variant == 0:
            return self.fill_segment_rainbow_sweep(led, _pass, phase, segment)

        if self.variant in (1, 4):
            return self.fill_segment_opposite(led, _pass, phase, segment)

        if self.variant == 2:
            return self.fill_segment_random_colors(led, _pass, phase, segment)

        if self.variant == 3:
            return self.fill_segment_gradient(led, _pass, phase, segment)

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

    def increment_back_forth(self, strip, step, _pass, phase):
        strip += step
        if strip == self.driver.strips and step > 0:
            step = -1
            _pass = (_pass + 1) % 2
            strip = self.driver.strips - 1
            self.start_sweep(step)
        if strip == -1 and step < 0:
            _pass = (_pass + 1) % 2 
            step = 1
            strip = 0
            phase = (phase + 1) % 2
            self.start_sweep(step)

        return strip, step, _pass, phase

    def increment_clockwise(self, strip, step, _pass, phase):
        strip += step
        if strip >= self.driver.strips:
            strip = strip % self.driver.strips
            _pass += 1
            if _pass == 2:
                phase = (phase + 1) % 2
                _pass = 0
        
        return strip, step, _pass, phase

    def run(self):

        led_data = [ list([0,0,0]) for x in range(self.driver.strips * self.driver.leds) ]
        led_data = [ list([0,0,0]) for x in range(self.driver.strips * self.driver.leds) ]
        strip = 0
        step = 1
        color = self.get_next_color()

        segments = self.fader_value(self.FADER_SEGMENTS)
        self.init(segments)

        phase = 0
        _pass = 0
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
                col = self.fill_segment(i, _pass, phase, segment)

                if col is not None:
                    led_data[(strip * self.driver.leds) + i] = col

            self.driver.set(led_data)
            if self.driver.strips == 8:
                strip, step, _pass, phase = self.increment_back_forth(strip, step, _pass, phase)
            else:
                strip, step, _pass, phase = self.increment_clockwise(strip, step, _pass, phase)

            self.sleep()
