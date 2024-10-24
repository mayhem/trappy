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


class EffectParticleSystem(Effect):

    FADER_COUNT = 4
    FADER_SPRITE = 5
    MAX_PARTICLE_COUNT = 8
    VARIANTS = 3

    def __init__(self, driver, event, apc = None, timeout=None):
        super().__init__(driver, event, apc, timeout)
        self.particles = []

    def get_active_faders(self):
        return [ self.FADER_COUNT, self.FADER_SPRITE ]

    def map_fader_value(self, fader, value):
        if fader == self.FADER_COUNT:
            # scale to MAX_PARTICLE_COUNT
            return value * (self.MAX_PARTICLE_COUNT-1) + 1

        if fader == self.FADER_SPRITE:
            return value * 254 + 1

        return None

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

    def detect_collisions(self, t, color = (255, 255, 255)):

        # Organize particles by strips 
        strips = [ [] for i in range(self.driver.strips) ]
        for p in self.particles:
            for s in p.strips:
                strips[s].append(p)

        for strip in strips:
            for a, b in itertools.combinations(strip, 2):
                a_pos = int(a.velocity * (t - a.t) + a.position)
                b_pos = int(b.velocity * (t - b.t) + b.position)

                if (a.velocity > 0 and b.velocity < 0 and a_pos >= b_pos) or \
                   (a.velocity < 0 and b.velocity > 0 and a_pos <= b_pos):
                    is_alive = False
                    a.color = b.color = color
                    a.remove_after_next = True
                    b.remove_after_next = True


    def run(self):

        t = 0
        row = 0
        skip_count = 0
        while not self.stop:
            if self.timeout is not None and monotonic() > self.timeout:
                return

            count = int(self.fader_value(self.FADER_COUNT))
            sprite = int(self.fader_value(self.FADER_SPRITE))

            if self.variant == 0:
                if count == self.driver.strips:
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, Particle.STRIP_ALL, None, 0, velocity, sprite))
                else:
                    strips = [ x for x in range(self.driver.strips)]
                    shuffle(strips)
                    for s in strips[:count]:
                        velocity = 1 + randint(2, 6)
                        self.particles.append(Particle(t, s, self.get_next_color(), 0, velocity, sprite))

            elif self.variant == 1:

                strips = [ x for x in range(self.driver.strips)]
                shuffle(strips)
                for s in strips[:count]:
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, s, self.get_next_color(ignore_odd_colors=True), 0, velocity, sprite))
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, s, self.get_next_color(ignore_odd_colors=True), self.driver.leds - 1, -velocity, sprite))

                self.detect_collisions(t)

            else:
                if skip_count == 0:
                    skip_count = count
                    velocity = 1 + randint(2, 6)
                    self.particles.append(Particle(t, Particle.STRIP_ALL, self.get_next_color(), 0, velocity, sprite))

                skip_count -= 1

            self.driver.set(self.render_leds(t))
            t += self.direction 
            row += 1

            self.sleep()
