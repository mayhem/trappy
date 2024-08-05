from time import sleep, monotonic

import smi_leds
from gamma_led_strips import GAMMA

class LEDDriver:

    def __init__(self, leds, strips):
        self.strips = strips
        self.leds = leds

        smi_leds.leds_init(self.strips, 10)
        smi_leds.leds_clear()

    def clear(self):
        smi_leds.leds_clear()

    def set_led(self, leds: list, strip: int, led: int, color: tuple):
        leds[strip * NUM_LEDS + led] = color

    def fill(self, color):
        leds = bytearray(color * self.leds * self.strips)
        smi_leds.leds_set(leds)
        smi_leds.leds_send()

    def set(self, buf):
        ba = bytearray()
        for col in buf:
            gcol = (GAMMA[col[0]], GAMMA[col[1]], GAMMA[col[2]])
            try:
                ba += bytearray(gcol)
            except ValueError:
                raise ValueError(col, " is invalid")

        smi_leds.leds_set(ba)
        smi_leds.leds_send()
