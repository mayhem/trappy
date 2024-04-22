import board
import neopixel
from adafruit_neopxl8 import
import time
from random import randint
from gradient import Gradient

class Trappy:

    def __init__(self):
        self.pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
        for i in range(3):
            self.pixel.fill((255, 0, 255))
            time.sleep(0.15)
            self.pixel.fill((160, 80, 0))
            time.sleep(0.15)

        self.pixel.fill((0, 0, 0))

        self.leds = 144
        self.strips = 8

        self.pixels = NeoPxl8(
            board.NEOPIXEL0,
            self.leds * self.strips,
            num_strands=self.strips,
            auto_write=False,
            brightness=.25
        )
        for i in range(5):
            self.pixels.fill((255, 80, 0))
            self.pixels.show()
            self.pixels.fill((255, 0, 255))
            self.pixels.show()

        self.pixels.fill((0, 0, 0))
        self.pixels.show()

    def set_led(self, strand, led, color):
        self.pixels[(strand * self.leds) + led] = color

    def test(self):
        while True:
            for i in range(15, 65):
                self.pixels.fill((i, 0, i))
                self.pixels.show();
                time.sleep(.05)
            for i in range(64, 15, -1):
                self.pixels.fill((i, 0, i))
                self.pixels.show();
                time.sleep(.05)

    def chase(self):
        while True:
            color = (randint(1, 255), randint(1, 255), randint(1, 16))
            for i in range(self.leds):
                self.pixels.fill((0, 0, 0))
                for j in range(self.strips):
                    self.set_led(j, i, color)
                self.pixels.show();

    def gradient(self):
        self.pixels.fill((0, 0, 0))
        g = [(0.0, (128, 0, 0)),
             (.5,  (0, 0, 128)),
             (1.0, (127, 0, 128))]
        gr = Gradient(g, leds=self.leds)
        for s in range(self.strips):
            for l in range(self.leds):
                #self.pixels[(s * self.leds) + l] = (255, 0, 0) #gr.get_color(l)
                self.set_led(s, l, (255, 0, 0)) #gr.get_color(l))
        self.pixels.show()


t = Trappy()
t.gradient()
