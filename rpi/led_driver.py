from time import sleep, monotonic

import smi_leds

class LEDDriver:

    def __init__(self, leds, strips):
        self.strips = leds
        self.leds = strips

        smi_leds.leds_init(self.leds, 10)
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
            try:
                ba += bytearray(col)
            except ValueError:
                raise ValueError(col, " is invalid")

        smi_leds.leds_set(ba)
        smi_leds.leds_send()
