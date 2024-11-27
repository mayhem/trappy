from abc import abstractmethod
from colorsys import hsv_to_rgb
import itertools
from time import sleep, monotonic

from gradient import Gradient
from random import random, randint, shuffle
from effect import Effect, SpeedEvent, FaderEvent, DirectionEvent
from color import hue_to_rgb, random_color
from defs import NUM_LEDS, NUM_STRIPS

class Particle:

    STRIP_ALL = -1
    def __init__(self, t, strip, color, position, velocity, sprite_pattern):
        """ strip can be a strip number, STRIP_ALL or a list of strips """
        self.t = t                # Time when particle was added
        # Which strip(s) to display particle on (is a list)
        self.strips = [ strip ] if isinstance(strip, int) else strip
        assert isinstance(self.strips, list)
        if self.strips == [ Particle.STRIP_ALL ]:
            self.strips = list(range(NUM_STRIPS))

        self.color = color        # The color of the particle
        self.position = position  # Initial position -- we're not tracking current position
        self.velocity = velocity
        self.sprite_pattern = sprite_pattern

        # If this is set, this particle will be removed after the next render pass
        self.remove_after_next = False


class ParticleSystem(Effect):

    MAX_PARTICLE_COUNT = 8

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.particles = []

    def print_palette(self, palette):
        for pal in palette:
            print("%.2f: " % pal[0], pal[1])
        print()

    def render_leds(self, t, background_color=(0,0,0)):

        led_data = [ list(background_color) for x in range(self.driver.strips * self.driver.leds) ]

        still_alive = []
        for p in self.particles:
            is_alive = True
            for s in p.strips:
                pos = int(p.velocity * (t - p.t) + p.position)
                if pos >= self.driver.leds or pos < 0:
                    is_alive = False

                if is_alive:
                    color = self.get_next_color() if p.color is None else p.color
                    if p.sprite_pattern == 1:
                        led_data[(s * self.driver.leds) + pos] = color
                    else:
                        for i in range(8):
                            if p.sprite_pattern & (1 << i) != 0 and pos + i < self.driver.leds:
                                led_data[(s * self.driver.leds) + pos + i] = color

            if is_alive and not p.remove_after_next:
                still_alive.append(p)

        self.particles = still_alive

        return led_data
