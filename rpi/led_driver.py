from time import sleep, monotonic

import smileds
from gamma_led_strips import GAMMA
from gamma_correct import GammaCorrector
from defs import NUM_LEDS, NUM_STRIPS, MAX_BRIGHTNESS, MIN_BRIGHTNESS


class LEDDriver:

    DEFAULT_GAMMA = 2.8
    INITIAL_BRIGHTNESS = 10

    def __init__(self):

        self.strips = NUM_STRIPS
        self.leds = NUM_LEDS
        self.max_brightness = MAX_BRIGHTNESS
        self.min_brightness = MIN_BRIGHTNESS

        smileds.leds_init(self.leds, self.INITIAL_BRIGHTNESS)
        smileds.leds_clear()

        self.gamma_correct = GammaCorrector()
        self.gamma_correct.set_gamma(self.DEFAULT_GAMMA)

    def set_brightness(self, brightness):
        """
        Set the brightness. On a scale of 1 - 100. A value of 100
        equals max_brightness.
        """
        if brightness < 0 or brightness > 100:
            raise RuntimeError("Invalid brightness: ", brightness)

        smileds.leds_brightness(int(brightness * (self.max_brightness - self.min_brightness) / 100) + self.min_brightness)

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
