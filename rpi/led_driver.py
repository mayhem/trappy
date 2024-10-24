from time import sleep, monotonic

import smileds
from gamma_led_strips import GAMMA
from gamma_correct import GammaCorrector


class LEDDriver:

    DEFAULT_GAMMA = 2.8

    def __init__(self, leds, strips):
        global num_leds, num_strips

        self.strips = strips
        self.leds = leds

        smileds.leds_init(self.leds, 10)
        smileds.leds_clear()

        self.gamma_correct = GammaCorrector()
        self.gamma_correct.set_gamma(self.DEFAULT_GAMMA)

    def set_gamma_correction(self, gamma):
        self.gamma_correct.set_gamma(gamma)

    def clear(self):
        smileds.leds_clear()

    def set_led(self, leds: list, strip: int, led: int, color: tuple):
        leds[strip * NUM_LEDS + led] = color

    def fill(self, color):
        leds = bytearray(color * self.leds * self.strips)
        smileds.leds_set(leds)
        smileds.leds_send()

    def set(self, buf, no_gamma=False):
        ba = bytearray()
        for col in buf:
            if no_gamma:
                gcol = col
            else:
                gcol = self.gamma_correct.gamma_correct(col)
            try:
                ba += bytearray(gcol)
            except ValueError:
                raise ValueError(col, " is invalid")

        smileds.leds_set(ba)
        smileds.leds_send()
