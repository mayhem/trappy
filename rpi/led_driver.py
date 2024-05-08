from time import sleep, monotonic

import smi_leds

class LEDDriver:

    def __init__(self, leds, strips):
        self.strips = leds
        self.leds = strips

        smi_leds.leds_init(self.leds, 15)
        smi_leds.leds_clear()

        for i in range(3):
            self.fill((255, 0, 255))
            sleep(.1)
            self.fill((255, 60, 0))
            sleep(.1)

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
            ba += bytearray(col)

        smi_leds.leds_set(ba)
        smi_leds.leds_send()
