from time import sleep, monotonic

import smileds
from gamma_led_strips import GAMMA
from gamma_correct import GammaCorrector
from config import NUM_LEDS, NUM_STRIPS, MAX_BRIGHTNESS, MIN_BRIGHTNESS


class LEDDriver:

    DEFAULT_GAMMA = 2.8
    INITIAL_BRIGHTNESS = 10

    def __init__(self):

        self.strips = NUM_STRIPS
        self.leds = NUM_LEDS
        self.total_leds = self.strips * self.leds
        self.max_brightness = MAX_BRIGHTNESS
        self.min_brightness = MIN_BRIGHTNESS

        smileds.leds_init(self.leds, self.INITIAL_BRIGHTNESS)
        smileds.leds_clear()

        self.gamma_correct = GammaCorrector()
        self.gamma_correct.set_gamma(self.DEFAULT_GAMMA)
        self.last_8_threshold = 24 * self.leds

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

    def map_last_8(self, index, led, strip):
        if strip < 8:
            return index * 3
        new_strip = 7 - (strip - 8)
        return self.last_8_threshold + ((new_strip * self.leds + led) * 3)

    def set(self, buf, no_gamma=False):
        ba = bytearray([0,0,0] * self.strips * self.leds)
        led = 0
        strip = 0
        for i, col in enumerate(buf):
            if no_gamma:
                gcol = col
            else:
                gcol = self.gamma_correct.gamma_correct(col)

            try:
                index = self.map_last_8(i, led, strip)
                ba[index] = gcol[0]
                ba[index + 1] = gcol[1]
                ba[index + 2] = gcol[2]
            except ValueError:
                raise ValueError(col, " is invalid")

            led += 1
            if led == self.leds:
                strip += 1
                led = 0

        smileds.leds_set(ba)
        smileds.leds_send()

    def set_np(self, buf, no_gamma=False):

        ba = bytearray(buf.tobytes())
        table = self.gamma_correct.table
        for i in range(self.total_leds):
            ba[i] = table[ba[i]]

        smileds.leds_set(ba)
        smileds.leds_send()
