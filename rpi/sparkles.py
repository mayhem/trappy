from abc import abstractmethod
from colorsys import hsv_to_rgb
from random import random, randint, shuffle
from time import sleep, monotonic
from threading import Lock

from gradient import Gradient
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color


class EffectSparkles(Effect):

    FADER_NUM_DOTS = 3
    FADER_FADE = 4
    FADE_CONSTANT = .85

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.lock = Lock()
        self.hue = 0.0
        self.current_colors = []

    def map_fader_value(self, fader, value):
        if fader == self.FADER_NUM_DOTS:
            return int(value * ((self.driver.strips * 2) - 1) + 1)

        # unsure what is needed here
        if fader == self.FADER_FADE:
            return value

        return None

    def run(self):

        led_data = [ list([0,0,0]) for x in range(self.driver.strips * self.driver.leds) ]
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            speed = self.speed
            if speed == 0:
                sleep(.01)
                continue

            num_dots = int(self.fader_value(self.FADER_NUM_DOTS))
            fade_constant = self.fader_value(self.FADER_FADE)

            # Fade out existing data
            for i in range(self.driver.strips * self.driver.leds):
                color = led_data[i]
                for j in range(3):
                    color[j] = int(float(color[j]) * fade_constant)
                led_data[j] = color


            # Add more sparkles
            strips = [ x for x in range(self.driver.strips)]
            shuffle(strips)
            for s in strips[:num_dots]:
                led = randint(0, self.driver.leds-1)
                led_data[(self.driver.leds * s) + led] = self.get_next_color()

            self.driver.set(led_data)

            max_delay = .1
            delay = (1.0 - speed) * max_delay
            sleep(delay)
