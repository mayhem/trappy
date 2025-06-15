from abc import abstractmethod
from colorsys import hsv_to_rgb
from random import random, randint, shuffle
from time import sleep, monotonic
from threading import Lock

from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color
from config import NUM_LEDS, NUM_STRIPS


class EffectSparkles(Effect):

    SLUG = "sparkles"
    FADER_NUM_DOTS = 2
    FADER_FADE = 3
    FADE_CONSTANT = 1.0
    VARIANTS = 2

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.lock = Lock()
        self.hue = 0.0
        self.current_colors = []

    def get_active_faders(self):
        return [ self.FADER_NUM_DOTS, self.FADER_FADE ]


    def map_fader_value(self, fader, value):
        if fader == self.FADER_NUM_DOTS:
            return int(value * ((self.driver.strips * 2) - 1) + 1)

        # unsure what is needed here
        if fader == self.FADER_FADE:
            return value

        return None

    def drop_out_content(self, led_data, mode):
        if mode in (0, 1):
            dir = mode
        for i, led in enumerate(range(NUM_LEDS)):
            for strip in range(NUM_STRIPS):
                if mode == 2:
                    dir = strip % 2
                if mode == 3:
                    dir = strip < (NUM_STRIPS / 2)
                if dir == 0:
                    led_data.pop(strip * NUM_LEDS)
                    led_data.insert((strip * NUM_LEDS) + (NUM_LEDS-1), (0,0,0))
                elif dir == 1:
                    led_data.insert(strip * NUM_LEDS, (0,0,0))
                    led_data.pop((strip * NUM_LEDS) + (NUM_LEDS-1))

            if i % 4 == 0:
                self.driver.set(led_data)

        return led_data

    def run(self):

        self.set_sleep_params(0.0, .2)

        led_data = [ list([0,0,0]) for x in range(self.driver.strips * self.driver.leds) ]
        dot_count = 0
        dropout_count = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            num_dots = int(self.fader_value(self.FADER_NUM_DOTS))
            fade_constant = self.fader_value(self.FADER_FADE)

            if self.variant == 0:
                # Fade out existing data
                for i in range(self.driver.strips * self.driver.leds):
                    color = led_data[i]
                    for j in range(3):
                        color[j] = int(float(color[j]) * fade_constant)
                    led_data[j] = color

            if self.variant == 1:
                dots_before_clear = int(num_dots * 4000 * fade_constant / 255) 

                if dot_count > dots_before_clear:
                    dot_count = 0;
                    led_data = self.drop_out_content(led_data, dropout_count % 4)
                    dropout_count += 1

            # Add more sparkles
            strips = [ x for x in range(self.driver.strips)]
            shuffle(strips)
            for s in strips[:num_dots]:
                led = randint(0, self.driver.leds-1)
                led_data[(self.driver.leds * s) + led] = self.get_next_color()
                self.driver.set(led_data)
                dot_count += 1
                self.sleep(partial=num_dots)
